/* gpio.h - minimal register-level GPIO helpers. */
#ifndef GPIO_H
#define GPIO_H

#include "board.h"

typedef enum {
    GPIO_MODE_INPUT = 0,
    GPIO_MODE_OUTPUT = 1,
    GPIO_MODE_ALTERNATE = 2,
    GPIO_MODE_ANALOG = 3
} gpio_mode_t;

void gpio_set_mode(gpio_regs_t *port, uint32_t pin, gpio_mode_t mode);
void gpio_set_alt_func(gpio_regs_t *port, uint32_t pin, uint32_t af);
void gpio_set_pull(gpio_regs_t *port, uint32_t pin, uint32_t pull); /* 0 none, 1 up, 2 down */
void gpio_write(gpio_regs_t *port, uint32_t pin, int value);
int  gpio_read(gpio_regs_t *port, uint32_t pin);
void gpio_init_board_pins(void); /* LED, HV_SHDN (driven low = HV off), CDR LOS/LOL in, SQUELCH out low, DAC SYNC */

#endif /* GPIO_H */
