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
    /* HV enable out, start OFF (power-up default state, per docs/02). */
    gpio_set_mode(BOARD_HV_EN_PORT, BOARD_HV_EN_PIN, GPIO_MODE_OUTPUT);
    gpio_write(BOARD_HV_EN_PORT, BOARD_HV_EN_PIN, 0);
    /* Interlock + LOS inputs. */
    gpio_set_mode(BOARD_INTERLOCK_PORT, BOARD_INTERLOCK_PIN, GPIO_MODE_INPUT);
    gpio_set_mode(BOARD_LOS_PORT, BOARD_LOS_PIN, GPIO_MODE_INPUT);
    /* DAC CS out, start deasserted (high). */
    gpio_set_mode(BOARD_DAC_CS_PORT, BOARD_DAC_CS_PIN, GPIO_MODE_OUTPUT);
    gpio_write(BOARD_DAC_CS_PORT, BOARD_DAC_CS_PIN, 1);
    /* I2C1 pins PB6/PB7 alternate function 4, open-drain.
     * AF number: VERIFY against the datasheet AF table at bring-up. */
    gpio_set_mode(GPIOB, 6u, GPIO_MODE_ALTERNATE);
    gpio_set_mode(GPIOB, 7u, GPIO_MODE_ALTERNATE);
    gpio_set_alt_func(GPIOB, 6u, 4u);
    gpio_set_alt_func(GPIOB, 7u, 4u);
    GPIOB->OTYPER |= (1u << 6) | (1u << 7);
    /* SPI1 pins PA5/PA6/PA7 alternate function 5 - but PA5 is also the
     * LED on this board plan; see the CONFLICT NOTE in board.h. The AF
     * setup is deliberately NOT done here: gpio_init for the SPI pins
     * happens in spi_init() so the conflict is resolved in one place
     * at bring-up, not silently here. */
}
