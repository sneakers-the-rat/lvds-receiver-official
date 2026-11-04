/*
 * board.h - the ONLY hardware-definition header for this firmware.
 *
 * There are no ST vendor headers (no CMSIS / HAL) in this repository,
 * so every peripheral base address and register offset used by the
 * code under src/ is defined here, from knowledge of the STM32H723
 * memory map.
 *
 * HONESTY RULE for this file: every address block below is marked
 *   "VERIFY against RM0468 at bring-up"
 * because none of it has been checked against the reference manual or
 * run on silicon yet. Treat these as well-informed starting points,
 * not as verified facts.
 */
#ifndef BOARD_H
#define BOARD_H

#include <stdint.h>

/* Register access helpers. */
#define REG32(addr) (*(volatile uint32_t *)(uintptr_t)(addr))
#define REG16(addr) (*(volatile uint16_t *)(uintptr_t)(addr))
#define REG8(addr)  (*(volatile uint8_t  *)(uintptr_t)(addr))

/* ------------------------------------------------------------------ */
/* Peripheral base addresses - VERIFY against RM0468 at bring-up       */
/* ------------------------------------------------------------------ */
#define BOARD_PERIPH_BASE   0x40000000u /* VERIFY against RM0468 */
#define BOARD_AHB4_BASE     0x58020000u /* VERIFY against RM0468 */

/* GPIO ports - VERIFY against RM0468 at bring-up */
#define GPIOA_BASE 0x58020000u /* VERIFY against RM0468 */
#define GPIOB_BASE 0x58020400u /* VERIFY against RM0468 */
#define GPIOC_BASE 0x58020800u /* VERIFY against RM0468 */
#define GPIOD_BASE 0x58020C00u /* VERIFY against RM0468 */
#define GPIOE_BASE 0x58021000u /* VERIFY against RM0468 */
#define GPIOF_BASE 0x58021400u /* VERIFY against RM0468 */
#define GPIOG_BASE 0x58021800u /* VERIFY against RM0468 */
#define GPIOH_BASE 0x58021C00u /* VERIFY against RM0468 */

/* RCC - VERIFY against RM0468 at bring-up */
#define RCC_BASE   0x58024400u /* VERIFY against RM0468 */
/* PWR - VERIFY against RM0468 at bring-up */
#define PWR_BASE   0x58024800u /* VERIFY against RM0468 */
/* FLASH controller - VERIFY against RM0468 at bring-up */
#define FLASH_REG_BASE 0x58004000u /* VERIFY against RM0468 */
/* SYSCFG - VERIFY against RM0468 at bring-up */
#define SYSCFG_BASE 0x58000400u /* VERIFY against RM0468 */

/* I2C - VERIFY against RM0468 at bring-up */
#define I2C1_BASE  0x40005400u /* VERIFY against RM0468 */
#define I2C2_BASE  0x40005800u /* VERIFY against RM0468 */

/* SPI - VERIFY against RM0468 at bring-up (H7 SPI register block) */
#define SPI1_BASE  0x40013000u /* VERIFY against RM0468 */
#define SPI2_BASE  0x40003800u /* VERIFY against RM0468 */
#define SPI3_BASE  0x40003C00u /* VERIFY against RM0468 */

/* Timers / DMA / ADC (used by the capture sketch) -
 * VERIFY against RM0468 at bring-up */
#define TIM2_BASE  0x40000000u /* VERIFY against RM0468 */
#define DMA1_BASE  0x40020000u /* VERIFY against RM0468 */
#define DMAMUX1_BASE 0x40020800u /* VERIFY against RM0468 */
#define ADC1_BASE  0x40022000u /* VERIFY against RM0468 */

/* USB OTG HS core - VERIFY against RM0468 at bring-up */
#define USB_OTG_HS_BASE 0x40040000u /* VERIFY against RM0468 */

/* Cortex-M7 system blocks (architectural, not ST-specific) */
#define SYSTICK_BASE 0xE000E010u
#define NVIC_BASE    0xE000E100u
#define SCB_BASE     0xE000ED00u

/* ------------------------------------------------------------------ */
/* GPIO register block (offsets are the standard STM32 GPIO layout) -  */
/* VERIFY against RM0468 at bring-up                                   */
/* ------------------------------------------------------------------ */
typedef struct {
    volatile uint32_t MODER;   /* 0x00 */
    volatile uint32_t OTYPER;  /* 0x04 */
    volatile uint32_t OSPEEDR; /* 0x08 */
    volatile uint32_t PUPDR;   /* 0x0C */
    volatile uint32_t IDR;     /* 0x10 */
    volatile uint32_t ODR;     /* 0x14 */
    volatile uint32_t BSRR;    /* 0x18 */
    volatile uint32_t LCKR;    /* 0x1C */
    volatile uint32_t AFRL;    /* 0x20 */
    volatile uint32_t AFRH;    /* 0x24 */
} gpio_regs_t;

#define GPIOA ((gpio_regs_t *)(uintptr_t)GPIOA_BASE)
#define GPIOB ((gpio_regs_t *)(uintptr_t)GPIOB_BASE)
#define GPIOC ((gpio_regs_t *)(uintptr_t)GPIOC_BASE)
#define GPIOD ((gpio_regs_t *)(uintptr_t)GPIOD_BASE)
#define GPIOE ((gpio_regs_t *)(uintptr_t)GPIOE_BASE)

/* ------------------------------------------------------------------ */
/* Board pin assignments (rev A intent). Pin numbers are design        */
/* choices for this board, not datasheet facts; the schematic in hw/   */
/* is authoritative once it exists. VERIFY against the schematic at    */
/* bring-up.                                                           */
/* ------------------------------------------------------------------ */
/* Status LED: PC9 (LED_STAT on the schematic, hw/CONNECTIONS.md,
 * via R45). This define previously said PA5 - the schematic assigns
 * PA5 to ULPI_CK, so PA5 cannot be the LED on the real board; the
 * schematic is authoritative (see the header of this file). */
#define BOARD_LED_PORT GPIOC
#define BOARD_LED_PIN  9u
/* USB: ULPI bus + USB3300 reset. PA4 is USB_RST and nothing else:
 * hw/CONNECTIONS.md assigns it to the USB3300 RESET input and the
 * USB code (usb_device_tinyusb.c) is its only user. The DAC that
 * once claimed PA4 as its chip select hangs on SPI3 with PA15 as
 * SYNC - see the DAC defines below. The full ULPI pin table lives
 * in usb_device_tinyusb.c. */
/* HV converter control: PC7 = HV_SHDN, the LT3757's SHDN/UVLO pin
 * node (hw/circuit.py U6/U10; hw/CONNECTIONS.md "HV bias"). This is
 * the ONLY MCU connection to the converter. R25 100 kOhm / R26 33 kOhm
 * divide +5 V onto the node: 1.241 V, just above the SHDN threshold
 * of 1.22 V (falling; datasheets/MANIFEST.md, LT3757 section). So
 * the pin's logic is a shutdown clamp, not an enable:
 *   PC7 driven LOW  -> node ~0 V -> converter shut down (HV OFF)
 *   PC7 high/floating -> divider wins -> converter enabled
 * Firmware must therefore configure PC7 as a push-pull output and
 * drive it low at init, and never float it (docs/03-power.md states
 * the same semantics). Full derivation: docs/06-hv-cdr-pin-inventory.md.
 * (This define previously claimed PB0 as an "HV enable" with an AND
 * gate and an interlock jumper in series. None of that exists in the
 * drawn design - PB0 is ULPI_D1.) */
#define BOARD_HV_SHDN_PORT GPIOC
#define BOARD_HV_SHDN_PIN  7u
/* There is NO interlock input on rev A. The requirement text
 * (docs/01 R9, docs/02) assumes an enclosure interlock jumper, but
 * the drawn design fits neither a jumper nor a sense input: the
 * inventory in docs/06-hv-cdr-pin-inventory.md searched every net,
 * part and MCU pin and found none. Firmware must not invent one;
 * hv_ctrl therefore never satisfies its enable gate on this board
 * (owner design decision, recorded in docs/00-status.md and
 * firmware/BRINGUP.md). No BOARD_INTERLOCK define exists, on
 * purpose. (It previously claimed PB1 - that pin is ULPI_D2.) */
/* ADN2813 status outputs (hw/circuit.py U4/U6; datasheets/MANIFEST.md
 * ADN2813 section, official Rev. C text): LOS pin 22 -> PB14,
 * LOL pin 16 -> PA2. Both are LVTTL, ACTIVE HIGH (1 = asserted). */
#define BOARD_CDR_LOS_PORT GPIOB
#define BOARD_CDR_LOS_PIN  14u
#define BOARD_CDR_LOL_PORT GPIOA
#define BOARD_CDR_LOL_PIN  2u
/* ADN2813 SQUELCH input: pin 27 <- PB15. LVTTL, active high disables
 * the CDR outputs. The net has no pull resistor and no other driver,
 * so firmware drives it low (outputs enabled) at init - leaving it
 * floating, as earlier firmware did, leaves the CDR outputs gated
 * by a floating CMOS input on the real board. */
#define BOARD_CDR_SQUELCH_PORT GPIOB
#define BOARD_CDR_SQUELCH_PIN  15u
/* DAC8562 (U8) serial interface, per the schematic
 * (hw/CONNECTIONS.md: "SPI3: PC10 SCK, PC12 MOSI -> DAC8562;
 * PA15 = DAC_SYNC"; hw/circuit.py U6/U8 net assignments agree):
 * SPI3 with SCK on PC10 and MOSI on PC12 (write-only - the DAC has
 * no data output, so no MISO is routed), SYNC on PA15 (active low,
 * manual GPIO around the SPI transfer; LDAC is tied to GND on the
 * board, so the outputs update on the SYNC rising edge). */
#define BOARD_DAC_SPI_BASE  SPI3_BASE
#define BOARD_DAC_SCK_PORT  GPIOC
#define BOARD_DAC_SCK_PIN   10u
#define BOARD_DAC_MOSI_PORT GPIOC
#define BOARD_DAC_MOSI_PIN  12u
#define BOARD_DAC_SPI_AF    6u /* SPI3 on PC10/PC12 - VERIFY against the STM32H723 datasheet AF table at bring-up */
#define BOARD_DAC_SYNC_PORT GPIOA
#define BOARD_DAC_SYNC_PIN  15u
/* I2C bus shared by ADN2813 and TMP117: I2C1, PB6=SCL PB7=SDA (AF4) */
#define BOARD_I2C_INSTANCE 1u

/* Clock intent (see clocks.c for the full arithmetic) */
#define BOARD_HSE_HZ        25000000u
#define BOARD_SYSCLK_HZ    550000000u
#define BOARD_AHB_DIV      2u   /* HCLK  = 275 MHz */
#define BOARD_APB_DIV      2u   /* PCLKx = 137.5 MHz */

/* Default driver timeout: a plain loop bound, roughly milliseconds at
 * 550 MHz; it exists so a wedged bus can never hang the firmware.
 * It is NOT a calibrated time. VERIFY/tune at bring-up. */
#define BOARD_TIMEOUT_LOOPS 1000000u

#endif /* BOARD_H */
