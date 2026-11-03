/* clocks.h - clock tree setup for the STM32H723 target. */
#ifndef CLOCKS_H
#define CLOCKS_H

#include <stdint.h>

/* Bring the part from the reset clock (HSI) to the intended tree:
 * HSE 25 MHz -> PLL1 -> SYSCLK 550 MHz, HCLK 275 MHz, APB 137.5 MHz.
 * Returns 0 on success, negative on a timeout/failure at any step. */
int clocks_init(void);

/* Very rough busy-wait millisecond delay, scaled for 550 MHz SYSCLK.
 * Not calibrated; for LED blink / sequencing only, never for protocol
 * timing. VERIFY at bring-up. */
void clocks_delay_ms_rough(uint32_t ms);

/* Monotonic millisecond counter from SysTick (started by clocks_init).
 * Used by main.c to run the 10 Hz HV temperature-compensation loop. */
uint32_t board_millis(void);
void board_systick_irq(void); /* call from the SysTick vector */

/* Enable the RCC clock gates for the peripherals this firmware uses
 * (GPIO ports, I2C1, SPI1, DMA1). Implemented in clocks.c so all RCC
 * bit-twiddling lives in one file. */
void board_enable_peripheral_clocks(void);

#endif /* CLOCKS_H */
