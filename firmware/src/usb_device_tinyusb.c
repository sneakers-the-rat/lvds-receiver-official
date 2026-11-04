/*
 * usb_device_tinyusb.c - the real implementation of usb_device_if.h.
 *
 * Replaces usb_device_stub.c. The protocol engine is TinyUSB 0.21.0
 * (third_party/tinyusb, provenance in third_party/PROVENANCE.md),
 * configured as a CDC ACM device on the STM32H723's OTG HS core
 * behind the board's USB3300 ULPI PHY. This file is the board glue:
 *
 *   1. SYSCFG analog switches for the PC2_C / PC3_C pads CLOSED -
 *      without this, ULPI DIR/NXT do not exist digitally on the
 *      H723ZG (docs/02 deviation 2; bring-up item #1 in docs/04).
 *   2. ULPI pins to AF10 (map: hw/CONNECTIONS.md), PHY reset pulse
 *      on PA4 (USB3300 RESET is active high, per datasheets/
 *      usb3300.txt), 24 MHz crystal on the PHY makes its 60 MHz
 *      CLKOUT, which the core consumes on ULPI_CK (PA5).
 *   3. RCC gates for the OTG HS core + ULPI interface, PWR USB
 *      voltage detector enable.
 *   4. tusb_init() + the byte-pipe semantics of usb_device_if.h on
 *      top of the CDC data endpoints.
 *
 * Everything TinyUSB does above this layer (enumeration, SETUP
 * handling, suspend/resume state machines) is the library's proven
 * code, not ours. What this file cannot do is prove any of it
 * against a real host: enumeration, ULPI timing and suspend
 * behaviour remain bench-verifiable only - firmware/BRINGUP.md is
 * the checklist, and every register constant below keeps the house
 * VERIFY-against-RM0468 marking.
 *
 * Interrupt model: OTG_HS_IRQHandler (vector slot in startup.c)
 * calls tud_int_handler(); all stack processing runs in thread
 * context via tud_task(), pumped from usb_dev_*() below - main.c's
 * loop calls usb_dev_recv() every iteration, so the stack is pumped
 * continuously without touching main.c.
 */
#include "usb_device_if.h"
#include "board.h"
#include "clocks.h"
#include "gpio.h"

#include "tusb.h"

/* TinyUSB's DWC2 port (dwc2_stm32.h) reads SystemCoreClock for its
 * remote-wakeup delay loop. It is only an approximation there; the
 * design SYSCLK is the honest value to give it. */
uint32_t SystemCoreClock = BOARD_SYSCLK_HZ;

/* ------------------------------------------------------------------ */
/* Register offsets/bits local to this module - VERIFY vs RM0468      */
/* ------------------------------------------------------------------ */
#define RCC_AHB1ENR    (RCC_BASE + 0xD8u) /* as in clocks.c - VERIFY */
#define RCC_APB4ENR    (RCC_BASE + 0xF4u) /* as in clocks.c - VERIFY */
#define RCC_AHB1ENR_USB1OTGHSEN     (1u << 25) /* VERIFY */
#define RCC_AHB1ENR_USB1OTGHSULPIEN (1u << 26) /* VERIFY */
#define RCC_APB4ENR_SYSCFGEN        (1u << 1)  /* VERIFY */

#define SYSCFG_PMCR    (SYSCFG_BASE + 0x04u)   /* VERIFY offset */
#define SYSCFG_PMCR_PC2SO (1u << 26) /* 1 = analog switch OPEN - VERIFY */
#define SYSCFG_PMCR_PC3SO (1u << 27) /* 1 = analog switch OPEN - VERIFY */

#define PWR_CR3        (PWR_BASE + 0x0Cu)      /* VERIFY offset */
#define PWR_CR3_USB33DEN (1u << 24)            /* VERIFY */

#define USB_ULPI_AF    10u /* OTG HS ULPI alternate function - VERIFY */

/* ULPI pin map, from hw/CONNECTIONS.md (schematic is authoritative):
 *   D0 PA3, D1 PB0, D2 PB1, D3 PB10, D4 PB11, D5 PB12, D6 PB13,
 *   D7 PB5, CK PA5, STP PC0, DIR PC2_C, NXT PC3_C. */
struct ulpi_pin { gpio_regs_t *port; uint32_t pin; };
static const struct ulpi_pin ulpi_pins[] = {
    { GPIOA, 3u  }, /* D0  */
    { GPIOB, 0u  }, /* D1  */
    { GPIOB, 1u  }, /* D2  */
    { GPIOB, 10u }, /* D3  */
    { GPIOB, 11u }, /* D4  */
    { GPIOB, 12u }, /* D5  */
    { GPIOB, 13u }, /* D6  */
    { GPIOB, 5u  }, /* D7  */
    { GPIOA, 5u  }, /* CK  (PHY CLKOUT in) */
    { GPIOC, 0u  }, /* STP */
    { GPIOC, 2u  }, /* DIR (PC2_C analog-switch pad) */
    { GPIOC, 3u  }, /* NXT (PC3_C analog-switch pad) */
};

static void ulpi_gpio_init(void)
{
    size_t i;
    for (i = 0; i < sizeof ulpi_pins / sizeof ulpi_pins[0]; i++) {
        gpio_regs_t *port = ulpi_pins[i].port;
        uint32_t pin = ulpi_pins[i].pin;
        gpio_set_pull(port, pin, 0u);
        /* OSPEEDR very-high (0b11): the gpio helpers have no speed
         * setter, and 60 MHz ULPI edges need it - direct write via
         * the same register struct gpio.c uses. */
        port->OSPEEDR |= (0x3u << (2u * pin));
        gpio_set_alt_func(port, pin, USB_ULPI_AF);
        gpio_set_mode(port, pin, GPIO_MODE_ALTERNATE);
    }
}

static void usb3300_reset_pulse(void)
{
    /* PA4 = USB_RST (hw/CONNECTIONS.md). USB3300 RESET is an active
     * high input; a >= 1 us pulse resets the transceiver (the ULPI
     * register set survives it, per the datasheet). Hold it a rough
     * millisecond, release, then give the crystal/PLL time to raise
     * CLKOUT before the core is initialised against it. */
    gpio_set_mode(GPIOA, 4u, GPIO_MODE_OUTPUT);
    gpio_write(GPIOA, 4u, 1);
    clocks_delay_ms_rough(1u);
    gpio_write(GPIOA, 4u, 0);
    clocks_delay_ms_rough(5u);
}

int usb_dev_init(void)
{
    tusb_rhport_init_t rh_init = {
        .role = TUSB_ROLE_DEVICE,
        .speed = TUSB_SPEED_HIGH,
    };
    tud_configure_dwc2_t dwc2_cfg = CFG_TUD_CONFIGURE_DWC2_DEFAULT;

    /* 1. SYSCFG clock on, then close the PC2_C / PC3_C analog
     *    switches (clearing the *SO bits connects the pads to the
     *    digital ULPI functions). Nothing else in the firmware
     *    touches PMCR; if these bit positions are wrong, ULPI is
     *    dead no matter what the rest does - BRINGUP.md, item 1. */
    REG32(RCC_APB4ENR) |= RCC_APB4ENR_SYSCFGEN;
    (void)REG32(RCC_APB4ENR);
    REG32(SYSCFG_PMCR) &= ~(SYSCFG_PMCR_PC2SO | SYSCFG_PMCR_PC3SO);

    /* 2. USB voltage detector (the HAL's EnableUSBVoltageDetector
     *    step on ST's own ULPI boards). */
    REG32(PWR_CR3) |= PWR_CR3_USB33DEN;

    /* 3. Pins, then PHY out of reset. */
    ulpi_gpio_init();
    usb3300_reset_pulse();

    /* 4. Core + ULPI interface clocks. */
    REG32(RCC_AHB1ENR) |= RCC_AHB1ENR_USB1OTGHSEN
                        | RCC_AHB1ENR_USB1OTGHSULPIEN;
    (void)REG32(RCC_AHB1ENR);

    /* 5. VBUS sensing: OFF in the core (the default). The USB3300
     *    owns VBUS on this board - its VBUS pin is wired to the
     *    connector and it reports session state to the core over
     *    ULPI - so the core is told to treat the B-session as valid
     *    (TinyUSB then sets GOTGCTL BVALOEN|BVALOVAL). Made explicit
     *    here rather than left as a silent library default, and
     *    listed in BRINGUP.md for bench confirmation. */
    dwc2_cfg.vbus_sensing = false;
    (void)tud_configure(0, TUD_CFGID_DWC2, &dwc2_cfg);

    /* 6. Stack init. The DWC2 driver detects the ULPI PHY from the
     *    core's GHWCFG2, initialises it, sizes the FIFOs from the
     *    core's own parameters, and enables the OTG_HS interrupt in
     *    the NVIC (through tinyusb_port/stm32h7xx.h). */
    if (!tusb_init(0, &rh_init)) {
        return USB_DEV_IO_ERROR;
    }
    return USB_DEV_OK;
}

/* Send budget: a capture buffer is 8 KiB; at HS bulk rates that is
 * ~1.5 ms of wire time. 100 ms of wall clock is generous headroom
 * that still can never wedge the main loop's 10 Hz safety duties if
 * the host stops reading. The iteration cap keeps the bound honest
 * even if SysTick is not running (clock-init failure path). */
#define USB_SEND_TIMEOUT_MS 100u
#define USB_SEND_GUARD      4000000u

int usb_dev_send(const uint8_t *data, size_t len)
{
    size_t sent = 0;
    uint32_t start = board_millis();
    uint32_t guard = 0;

    if (!tud_mounted()) {
        return USB_DEV_NOT_CONNECTED;
    }
    while (sent < len) {
        uint32_t avail, chunk;

        tud_task();
        if (!tud_mounted()) {
            return USB_DEV_NOT_CONNECTED;
        }
        avail = tud_cdc_write_available();
        if (avail == 0u) {
            if ((board_millis() - start) > USB_SEND_TIMEOUT_MS
                || ++guard > USB_SEND_GUARD) {
                (void)tud_cdc_write_flush();
                return USB_DEV_IO_ERROR; /* host not draining */
            }
            continue;
        }
        chunk = (uint32_t)(len - sent);
        if (chunk > avail) {
            chunk = avail;
        }
        sent += tud_cdc_write(data + sent, chunk);
        (void)tud_cdc_write_flush();
    }
    return USB_DEV_OK;
}

int usb_dev_recv(uint8_t *buf, size_t cap)
{
    uint32_t n;

    tud_task();
    if (!tud_mounted()) {
        return USB_DEV_NOT_CONNECTED;
    }
    n = tud_cdc_available();
    if (n == 0u) {
        return USB_DEV_NO_DATA;
    }
    if (n > cap) {
        n = (uint32_t)cap;
    }
    return (int)tud_cdc_read(buf, n);
}

int usb_dev_connected(void)
{
    tud_task();
    return tud_mounted() ? 1 : 0;
}

/* OTG HS global interrupt - vector slot reserved in startup.c. */
void OTG_HS_IRQHandler(void)
{
    tud_int_handler(0);
}
