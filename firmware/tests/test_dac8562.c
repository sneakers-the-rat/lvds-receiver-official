/*
 * test_dac8562.c - host tests for the DAC8562 driver (src/dac8562.c),
 * linked against mock gpio_write / spi_transfer backends.
 *
 * What the mocks can and cannot observe, stated plainly:
 *
 * - OBSERVABLE: every call the driver makes crosses these two
 *   functions, so the mocks see WHICH port pointer and pin the
 *   driver drives for SYNC, in what order relative to the SPI
 *   transfers, and the exact bytes transferred. That is enough to
 *   prove the threshold path frames SYNC on the pin board.h assigns
 *   (PA15) and never touches PA4 (the USB3300 reset) - the
 *   regression this test exists to lock.
 * - NOT OBSERVABLE: which hardware SPI peripheral spi.c points its
 *   register block at. That choice is a compile-time base address
 *   inside spi.c; no host run of this test can see it. The pin-map
 *   lock below therefore also asserts board.h's DAC SPI base equals
 *   the SPI3 base from the schematic assignment (hw/CONNECTIONS.md:
 *   SPI3, PC10 SCK / PC12 MOSI), so a future edit that moves the
 *   define back to SPI1 fails here even though spi.c itself is not
 *   executed.
 *
 * Expected pin map, taken from the schematic sources (independent
 * literals in this file, on purpose):
 *   hw/CONNECTIONS.md: "SPI3: PC10 SCK, PC12 MOSI -> DAC8562;
 *                       PA15 = DAC_SYNC", "PA4 USB_RST"
 *   hw/circuit.py:     U6 "PC10":"SPI_SCK", "PC12":"SPI_MOSI",
 *                      "PA15":"DAC_SYNC", "PA4":"USB_RST";
 *                      U8 pin 6 SYNC=DAC_SYNC, 7 SCLK=SPI_SCK,
 *                      8 DIN=SPI_MOSI.
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

#include "board.h"
#include "dac8562.h"

static int failures = 0;

#define CHECK(cond, name)                                              \
    do {                                                               \
        if (cond) {                                                    \
            printf("PASS %s\n", (name));                               \
        } else {                                                       \
            printf("FAIL %s (line %d)\n", (name), __LINE__);           \
            failures++;                                                \
        }                                                              \
    } while (0)

/* ------------------------- mock backends ------------------------- */

#define EV_GPIO  1
#define EV_XFER  2

typedef struct {
    int kind;
    gpio_regs_t *port; /* EV_GPIO only */
    uint32_t pin;      /* EV_GPIO only */
    int value;         /* EV_GPIO only */
    uint8_t bytes[3];  /* EV_XFER only */
    size_t len;        /* EV_XFER only */
} event_t;

#define MAX_EVENTS 64
static event_t events[MAX_EVENTS];
static int nevents = 0;
static int pa4_touched = 0; /* set if any GPIO event hits GPIOA pin 4 */

static void ev_reset(void)
{
    nevents = 0;
    pa4_touched = 0;
    memset(events, 0, sizeof(events));
}

/* Mock for the gpio_write the driver calls (gpio.c is NOT linked). */
void gpio_write(gpio_regs_t *port, uint32_t pin, int value)
{
    if (port == GPIOA && pin == 4u) {
        pa4_touched = 1;
    }
    if (nevents < MAX_EVENTS) {
        events[nevents].kind = EV_GPIO;
        events[nevents].port = port;
        events[nevents].pin = pin;
        events[nevents].value = value;
        nevents++;
    }
}

/* Mock for the spi_transfer the driver calls (spi.c is NOT linked).
 * The DAC is write-only on this board: rx must be NULL and every
 * frame exactly 3 bytes. */
int spi_transfer(const uint8_t *tx, uint8_t *rx, size_t len)
{
    if (nevents < MAX_EVENTS) {
        size_t i;
        events[nevents].kind = EV_XFER;
        events[nevents].len = len;
        for (i = 0; i < len && i < 3u; i++) {
            events[nevents].bytes[i] = tx[i];
        }
        nevents++;
    }
    return (rx == NULL && len == 3u) ? 0 : -1;
}

/* ----------------------------- tests ----------------------------- */

/* The pin map in board.h, locked to the schematic literals. */
static void test_pin_map_lock(void)
{
    CHECK(BOARD_DAC_SYNC_PORT == GPIOA, "dac sync port is GPIOA");
    CHECK(BOARD_DAC_SYNC_PIN == 15u, "dac sync pin is PA15 (not PA4)");
    CHECK(BOARD_DAC_SPI_BASE == SPI3_BASE, "dac spi base define is SPI3");
    CHECK(SPI3_BASE == 0x40003C00u, "SPI3 base matches STM32H723 map");
    CHECK(BOARD_DAC_SCK_PORT == GPIOC && BOARD_DAC_SCK_PIN == 10u,
          "dac spi SCK is PC10");
    CHECK(BOARD_DAC_MOSI_PORT == GPIOC && BOARD_DAC_MOSI_PIN == 12u,
          "dac spi MOSI is PC12");
}

/* One framed write: SYNC (PA15) low, 3 bytes, SYNC high - and the
 * event sequence contains exactly those three events. */
static int check_one_write(uint8_t b0, uint8_t b1, uint8_t b2)
{
    return nevents == 3
        && events[0].kind == EV_GPIO && events[0].port == GPIOA
        && events[0].pin == 15u && events[0].value == 0
        && events[1].kind == EV_XFER && events[1].len == 3u
        && events[1].bytes[0] == b0 && events[1].bytes[1] == b1
        && events[1].bytes[2] == b2
        && events[2].kind == EV_GPIO && events[2].port == GPIOA
        && events[2].pin == 15u && events[2].value == 1;
}

static void test_set_threshold(void)
{
    ev_reset();
    CHECK(dac8562_set_threshold(0xBEEFu) == 0, "set_threshold returns ok");
    /* frame: cmd 0x3, addr 0 (DAC A), data 0xBEEF -> 0x30 0xBE 0xEF */
    CHECK(check_one_write(0x30u, 0xBEu, 0xEFu),
          "set_threshold pulses PA15 SYNC around the A-channel frame");
    CHECK(pa4_touched == 0, "set_threshold never touches PA4 (USB_RST)");
}

static void test_set_bias_setpoint(void)
{
    ev_reset();
    CHECK(dac8562_set_bias_setpoint(0x1234u) == 0, "set_bias returns ok");
    /* frame: cmd 0x3, addr 1 (DAC B), data 0x1234 -> 0x31 0x12 0x34 */
    CHECK(check_one_write(0x31u, 0x12u, 0x34u),
          "set_bias pulses PA15 SYNC around the B-channel frame");
    CHECK(pa4_touched == 0, "set_bias never touches PA4 (USB_RST)");
}

static void test_init_sequence(void)
{
    /* init: reset (cmd 5, addr 7), internal ref on (cmd 7, addr 7,
     * data 1), power up (cmd 4, addr 7), threshold 0, bias 0 - five
     * framed writes, each wrapped in its own PA15 SYNC pulse. */
    static const uint8_t want[5][3] = {
        {0x57u, 0x00u, 0x00u},
        {0x77u, 0x00u, 0x01u},
        {0x47u, 0x00u, 0x00u},
        {0x30u, 0x00u, 0x00u},
        {0x31u, 0x00u, 0x00u},
    };
    int ok = 1;
    int i;
    ev_reset();
    CHECK(dac8562_init() == 0, "dac8562_init returns ok");
    if (nevents != 15) {
        ok = 0;
    } else {
        for (i = 0; i < 5; i++) {
            const event_t *g0 = &events[i * 3];
            const event_t *xf = &events[i * 3 + 1];
            const event_t *g1 = &events[i * 3 + 2];
            if (!(g0->kind == EV_GPIO && g0->port == GPIOA
                  && g0->pin == 15u && g0->value == 0
                  && xf->kind == EV_XFER && xf->len == 3u
                  && xf->bytes[0] == want[i][0]
                  && xf->bytes[1] == want[i][1]
                  && xf->bytes[2] == want[i][2]
                  && g1->kind == EV_GPIO && g1->port == GPIOA
                  && g1->pin == 15u && g1->value == 1)) {
                ok = 0;
            }
        }
    }
    CHECK(ok, "init emits the 5 expected frames, each SYNC-pulsed on PA15");
    CHECK(pa4_touched == 0, "init never touches PA4 (USB_RST)");
}

int main(void)
{
    test_pin_map_lock();
    test_set_threshold();
    test_set_bias_setpoint();
    test_init_sequence();
    if (failures != 0) {
        printf("test_dac8562: %d FAILURES\n", failures);
        return 1;
    }
    printf("test_dac8562: all checks passed\n");
    return 0;
}
