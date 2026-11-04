/*
 * stm32h7xx.h - MINIMAL SHIM, not an ST header.
 *
 * TinyUSB's STM32 DWC2 port header (dwc2_stm32.h) includes
 * "stm32h7xx.h" and uses a handful of symbols from it. This repo has
 * no ST vendor headers by policy (see board.h), so this shim supplies
 * exactly what the port consumes, and nothing else:
 *
 *   USB1_OTG_HS_PERIPH_BASE - OTG HS core base address. With this
 *       defined (and USB_OTG_HS_PERIPH_BASE deliberately NOT
 *       defined), dwc2_stm32.h aliases its port-0 slot onto the HS
 *       core, so the single OTG HS core of the H723 is rhport 0.
 *   OTG_HS_IRQn             - the core's NVIC IRQ number (77).
 *   IRQn_Type               - opaque IRQ number type.
 *   NVIC_EnableIRQ/DisableIRQ - NVIC ISER/ICER are ARM-architectural
 *       registers (0xE000E100 / 0xE000E180), not ST-specific.
 *   __NOP                   - compiler intrinsic used by the port's
 *       remote-wakeup delay loop.
 *   SystemCoreClock         - extern, defined in
 *       usb_device_tinyusb.c; the port uses it only to approximate a
 *       1 ms delay for remote wakeup.
 *
 * The address and IRQ number below carry the same status as every
 * other constant in board.h: VERIFY against RM0468 at bring-up.
 */
#ifndef STM32H7XX_SHIM_H
#define STM32H7XX_SHIM_H

#include <stdint.h>

typedef int IRQn_Type;

#define USB1_OTG_HS_PERIPH_BASE 0x40040000u /* VERIFY against RM0468 */
#define OTG_HS_IRQn             77          /* VERIFY against RM0468 */

#define SHIM_NVIC_ISER_BASE 0xE000E100u /* architectural, Cortex-M */
#define SHIM_NVIC_ICER_BASE 0xE000E180u /* architectural, Cortex-M */

static inline void NVIC_EnableIRQ(IRQn_Type irqn)
{
    volatile uint32_t *iser =
        (volatile uint32_t *)(uintptr_t)(SHIM_NVIC_ISER_BASE
                                         + 4u * ((uint32_t)irqn >> 5));
    *iser = 1u << ((uint32_t)irqn & 31u);
}

static inline void NVIC_DisableIRQ(IRQn_Type irqn)
{
    volatile uint32_t *icer =
        (volatile uint32_t *)(uintptr_t)(SHIM_NVIC_ICER_BASE
                                         + 4u * ((uint32_t)irqn >> 5));
    *icer = 1u << ((uint32_t)irqn & 31u);
}

static inline void __NOP(void)
{
    __asm__ volatile ("nop");
}

extern uint32_t SystemCoreClock;

#endif /* STM32H7XX_SHIM_H */
