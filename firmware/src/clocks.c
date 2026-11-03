/*
 * clocks.c - register-level clock setup, no HAL.
 *
 * PLL arithmetic (the intended configuration, worked in full):
 *   HSE                       = 25 MHz
 *   PLL1 divider M            = 5     -> VCO input  = 25/5    = 5 MHz
 *                                        (PLL input range 2 selected
 *                                         for a 5 MHz input -
 *                                         VERIFY range encoding vs RM0468)
 *   PLL1 multiplier N         = 110   -> VCO output = 5 * 110 = 550 MHz
 *   PLL1 divider P            = 1     -> PLL1P      = 550 MHz
 *   SYSCLK source             = PLL1P -> SYSCLK     = 550 MHz
 *   AHB divider               = 2     -> HCLK       = 275 MHz
 *   APB1/2/3/4 dividers       = 2     -> PCLKx      = 137.5 MHz
 *   PLL1 Q/R dividers         = 2     -> 275 MHz (unused in rev A)
 *
 * Voltage scaling: 550 MHz on the H723 requires VOS0 (the highest
 * core voltage scale) and the corresponding flash wait states; both
 * are programmed below with values that must be VERIFY-checked
 * against RM0468 / the datasheet at bring-up. If VOS0 is not reached,
 * running at 550 MHz is out of spec - the timeout return exists so
 * this failure is visible rather than silent.
 *
 * Every register offset/bit below: VERIFY against RM0468 at bring-up.
 */
#include "clocks.h"
#include "board.h"

/* RCC register offsets from RCC_BASE - VERIFY against RM0468 */
#define RCC_CR        (RCC_BASE + 0x00u)
#define RCC_CFGR      (RCC_BASE + 0x10u)
#define RCC_PLLCKSELR (RCC_BASE + 0x28u)
#define RCC_PLLCFGR   (RCC_BASE + 0x2Cu)
#define RCC_PLL1DIVR  (RCC_BASE + 0x30u)
#define RCC_D1CFGR    (RCC_BASE + 0x18u)
#define RCC_D2CFGR    (RCC_BASE + 0x1Cu)
#define RCC_D3CFGR    (RCC_BASE + 0x20u)
#define RCC_AHB4ENR   (RCC_BASE + 0xE0u)
#define RCC_APB1LENR  (RCC_BASE + 0xE8u)
#define RCC_APB2ENR   (RCC_BASE + 0xF0u)
#define RCC_APB4ENR   (RCC_BASE + 0xF4u)
#define RCC_AHB1ENR   (RCC_BASE + 0xD8u)
#define RCC_AHB2ENR   (RCC_BASE + 0xDCu)

/* PWR offsets - VERIFY against RM0468 */
#define PWR_CSR1 (PWR_BASE + 0x04u) /* VOSRDY lives here on H7 - VERIFY */
#define PWR_D3CR (PWR_BASE + 0x18u) /* VOS selection on H7 - VERIFY     */

/* FLASH offsets - VERIFY against RM0468 */
#define FLASH_ACR (FLASH_REG_BASE + 0x00u)

#define RCC_CR_HSEON   (1u << 16)
#define RCC_CR_HSERDY  (1u << 17)
#define RCC_CR_PLL1ON  (1u << 24)
#define RCC_CR_PLL1RDY (1u << 25)

static volatile uint32_t systick_ms;

uint32_t board_millis(void)
{
    return systick_ms;
}

void board_systick_irq(void)
{
    systick_ms++;
}

static int wait_flag(volatile uint32_t *reg, uint32_t mask, int want_set)
{
    uint32_t t = BOARD_TIMEOUT_LOOPS * 10u;
    while (t-- > 0u) {
        int is_set = (*reg & mask) != 0u;
        if (is_set == want_set) {
            return 0;
        }
    }
    return -1;
}

int clocks_init(void)
{
    uint32_t v;

    /* 1. Request VOS0 core voltage, wait until the regulator is ready.
     *    Bit positions: VERIFY against RM0468 at bring-up. */
    v = REG32(PWR_D3CR);
    v &= ~(0x3u << 14);        /* VOS field - VERIFY */
    v |= (0x0u << 14);         /* encoding for VOS0 - VERIFY (may be 01b
                                  with a separate ODEN step on some H7
                                  variants; that uncertainty is exactly
                                  why this is a bring-up item) */
    REG32(PWR_D3CR) = v;
    if (wait_flag((volatile uint32_t *)(uintptr_t)PWR_CSR1,
                  (1u << 13) /* VOSRDY - VERIFY */, 1) != 0) {
        return -1;
    }

    /* 2. Flash latency for 550 MHz / VOS0: value 7 here is a
     *    placeholder-class value - VERIFY the exact LATENCY and WRHIGHFREQ
     *    encoding against the datasheet table at bring-up, BEFORE
     *    raising the clock. */
    v = REG32(FLASH_ACR);
    v &= ~0xFu;
    v |= 7u;                   /* LATENCY - VERIFY */
    REG32(FLASH_ACR) = v;

    /* 3. Start HSE (25 MHz crystal), wait for it. */
    REG32(RCC_CR) |= RCC_CR_HSEON;
    if (wait_flag((volatile uint32_t *)(uintptr_t)RCC_CR,
                  RCC_CR_HSERDY, 1) != 0) {
        return -2;
    }

    /* 4. PLL1 source = HSE, M = 5. PLLCKSELR: PLLSRC in bits [1:0],
     *    DIVM1 in bits [9:4] - VERIFY against RM0468. */
    v = REG32(RCC_PLLCKSELR);
    v &= ~0x3u;
    v |= 0x2u;                 /* PLLSRC = HSE - VERIFY encoding */
    v &= ~(0x3Fu << 4);
    v |= (5u << 4);            /* DIVM1 = 5 */
    REG32(RCC_PLLCKSELR) = v;

    /* 5. PLL1 N = 110, P = 1, Q = 2, R = 2. PLL1DIVR fields store
     *    (divider-1): N in bits [8:0], P in [15:9], Q in [22:16],
     *    R in [30:24] (approx.) - VERIFY against RM0468. */
    REG32(RCC_PLL1DIVR) = ((110u - 1u) << 0)
                        | ((1u - 1u) << 9)
                        | ((2u - 1u) << 16)
                        | ((2u - 1u) << 24);

    /* 6. PLLCFGR: enable PLL1P output, set VCO/input range encodings
     *    for a 5 MHz input and a 550 MHz (wide) VCO.
     *    All bit positions VERIFY against RM0468. */
    v = REG32(RCC_PLLCFGR);
    v |= (1u << 16);           /* DIVPEN (PLL1 P output enable) - VERIFY */
    v &= ~(0x3u << 2);
    v |= (0x2u << 2);          /* PLL1RGE: input range 4-8 MHz - VERIFY */
    v &= ~(0x1u << 1);         /* PLL1VCOSEL: wide VCO - VERIFY */
    REG32(RCC_PLLCFGR) = v;

    /* 7. Bus dividers BEFORE switching SYSCLK up: AHB /2, APB /2.
     *    Field positions VERIFY against RM0468. */
    v = REG32(RCC_D1CFGR);
    v &= ~(0xFu << 0);
    v |= (0x8u << 0);          /* HPRE encoding for /2 - VERIFY */
    v &= ~(0x7u << 4);
    v |= (0x4u << 4);          /* D1PPRE encoding for /2 - VERIFY */
    REG32(RCC_D1CFGR) = v;
    v = REG32(RCC_D2CFGR);
    v &= ~((0x7u << 4) | (0x7u << 8));
    v |= (0x4u << 4) | (0x4u << 8); /* APB1/APB2 /2 - VERIFY fields */
    REG32(RCC_D2CFGR) = v;
    v = REG32(RCC_D3CFGR);
    v &= ~(0x7u << 4);
    v |= (0x4u << 4);          /* APB4 /2 - VERIFY field */
    REG32(RCC_D3CFGR) = v;

    /* 8. Enable PLL1, wait for lock. */
    REG32(RCC_CR) |= RCC_CR_PLL1ON;
    if (wait_flag((volatile uint32_t *)(uintptr_t)RCC_CR,
                  RCC_CR_PLL1RDY, 1) != 0) {
        return -3;
    }

    /* 9. Switch SYSCLK to PLL1P: CFGR SW in bits [2:0], SWS in [5:3];
     *    PLL encoding VERIFY against RM0468. */
    v = REG32(RCC_CFGR);
    v &= ~0x7u;
    v |= 0x3u;                 /* SW = PLL1 - VERIFY encoding */
    REG32(RCC_CFGR) = v;
    {
        uint32_t t = BOARD_TIMEOUT_LOOPS * 10u;
        while (t-- > 0u) {
            if (((REG32(RCC_CFGR) >> 3) & 0x7u) == 0x3u) {
                break;
            }
        }
        if (t == 0u) {
            return -4;
        }
    }

    /* 10. SysTick at 1 kHz from HCLK (275 MHz): reload = HCLK/1000 - 1.
     *     SysTick registers are architectural Cortex-M7. */
    REG32(SYSTICK_BASE + 0x04u) = (275000000u / 1000u) - 1u; /* LOAD */
    REG32(SYSTICK_BASE + 0x08u) = 0u;                        /* VAL  */
    REG32(SYSTICK_BASE + 0x00u) = 0x7u; /* CTRL: enable, tickint, HCLK */
    return 0;
}

void clocks_delay_ms_rough(uint32_t ms)
{
    /* ~550 MHz core: order of 130k loop iterations per ms with the
     * loop below at -O2. Deliberately rough - see header note. */
    volatile uint32_t i;
    while (ms-- > 0u) {
        for (i = 0; i < 130000u; i++) {
            __asm__ volatile ("nop");
        }
    }
}

/* Peripheral clock gates used by the other modules. Kept here so the
 * RCC_AHB/APB enable bits live in one file. All bit positions VERIFY
 * against RM0468 at bring-up. */
void board_enable_peripheral_clocks(void)
{
    REG32(RCC_AHB4ENR) |= (1u << 0)   /* GPIOA - VERIFY */
                        | (1u << 1)   /* GPIOB - VERIFY */
                        | (1u << 2);  /* GPIOC - VERIFY */
    REG32(RCC_APB1LENR) |= (1u << 21); /* I2C1 - VERIFY */
    REG32(RCC_APB2ENR) |= (1u << 12);  /* SPI1 - VERIFY */
    REG32(RCC_AHB1ENR) |= (1u << 0);   /* DMA1 - VERIFY */
    (void)REG32(RCC_AHB4ENR);          /* read-back: enable takes effect */
}
