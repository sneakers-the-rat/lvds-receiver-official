/* gpio.c - register layouts per board.h (VERIFY against RM0468). */
#include "gpio.h"

void gpio_set_mode(gpio_regs_t *port, uint32_t pin, gpio_mode_t mode)
{
    uint32_t shift = (pin & 0xFu) * 2u;
    port->MODER = (port->MODER & ~(0x3u << shift))
                | ((uint32_t)mode << shift);
    if (mode == GPIO_MODE_OUTPUT) {
        port->OTYPER &= ~(1u << pin); /* push-pull */
    }
}

void gpio_set_alt_func(gpio_regs_t *port, uint32_t pin, uint32_t af)
{
    if (pin < 8u) {
        uint32_t shift = pin * 4u;
        port->AFRL = (port->AFRL & ~(0xFu << shift)) | (af << shift);
    } else {
        uint32_t shift = (pin - 8u) * 4u;
        port->AFRH = (port->AFRH & ~(0xFu << shift)) | (af << shift);
    }
}

void gpio_set_pull(gpio_regs_t *port, uint32_t pin, uint32_t pull)
{
    uint32_t shift = (pin & 0xFu) * 2u;
    port->PUPDR = (port->PUPDR & ~(0x3u << shift)) | (pull << shift);
}

void gpio_write(gpio_regs_t *port, uint32_t pin, int value)
{
    /* BSRR: low half sets, high half resets - atomic, no read-modify-write. */
    port->BSRR = value ? (1u << pin) : (1u << (pin + 16u));
}

int gpio_read(gpio_regs_t *port, uint32_t pin)
{
    return (port->IDR & (1u << pin)) != 0u;
}

void gpio_init_board_pins(void)
{
    /* Status LED out, start off. */
    gpio_set_mode(BOARD_LED_PORT, BOARD_LED_PIN, GPIO_MODE_OUTPUT);
    gpio_write(BOARD_LED_PORT, BOARD_LED_PIN, 0);
    /* HV shutdown clamp, start OFF: PC7 low pulls the LT3757 SHDN
     * node to ~0 V through the fitted J5 interlock jumper. (The
     * R25/R26 divider alone also holds the node below the SHDN
     * threshold - 0.94 V vs 1.17 V minimum - so the converter is
     * off at power-up by hardware even before this runs; see
     * board.h and docs/03.) Load the low level BEFORE switching
     * the pin to output so it never presents a driven-high level,
     * and leave the pin an output for the life of the firmware. */
    gpio_write(BOARD_HV_SHDN_PORT, BOARD_HV_SHDN_PIN, 0);
    gpio_set_mode(BOARD_HV_SHDN_PORT, BOARD_HV_SHDN_PIN, GPIO_MODE_OUTPUT);
    /* The J5 sense input (PA6, analogue) is configured by
     * hv_sense.c on first use, with its ADC setup.
     * CDR status inputs: LOS (PB14) and LOL (PA2), both active high. */
    gpio_set_mode(BOARD_CDR_LOS_PORT, BOARD_CDR_LOS_PIN, GPIO_MODE_INPUT);
    gpio_set_mode(BOARD_CDR_LOL_PORT, BOARD_CDR_LOL_PIN, GPIO_MODE_INPUT);
    /* CDR SQUELCH out, deasserted (low = outputs enabled); the net
     * has no other driver, so it must not float. */
    gpio_write(BOARD_CDR_SQUELCH_PORT, BOARD_CDR_SQUELCH_PIN, 0);
    gpio_set_mode(BOARD_CDR_SQUELCH_PORT, BOARD_CDR_SQUELCH_PIN,
                  GPIO_MODE_OUTPUT);
    /* DAC SYNC out, start deasserted (high). */
    gpio_set_mode(BOARD_DAC_SYNC_PORT, BOARD_DAC_SYNC_PIN, GPIO_MODE_OUTPUT);
    gpio_write(BOARD_DAC_SYNC_PORT, BOARD_DAC_SYNC_PIN, 1);
    /* I2C1 pins PB6/PB7 alternate function 4, open-drain.
     * AF number: VERIFY against the datasheet AF table at bring-up. */
    gpio_set_mode(GPIOB, 6u, GPIO_MODE_ALTERNATE);
    gpio_set_mode(GPIOB, 7u, GPIO_MODE_ALTERNATE);
    gpio_set_alt_func(GPIOB, 6u, 4u);
    gpio_set_alt_func(GPIOB, 7u, 4u);
    GPIOB->OTYPER |= (1u << 6) | (1u << 7);
    /* SPI3 pins (PC10 SCK / PC12 MOSI, per the schematic) are NOT set
     * up here: their alternate-function setup happens in spi_init()
     * so the DAC's pin configuration lives in one place with its
     * driver. SYNC (PA15) is the plain GPIO set up above. */
}
