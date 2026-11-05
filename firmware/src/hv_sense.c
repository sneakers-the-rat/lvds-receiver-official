/* hv_sense.c - ADC1 readback of the HV_SHDN node on PA6.
 *
 * Register-level, no HAL - same style as the rest of src/. Every
 * STM32H723-specific encoding below carries the repo's standing
 * caveat: VERIFY against RM0468 (ADC chapter) and the datasheet
 * pin table at bring-up; none of this has run on silicon. The
 * failure direction is safe by construction: any timeout or
 * implausible state makes hv_sense_read_mv() return -1, and
 * hv_ctrl treats -1 as "jumper not fitted" (enable refused).
 *
 * ADC choices, and why:
 *   - ADC1, channel BOARD_HV_SENSE_ADC_CHANNEL (PA6 = ADC12_INP3 -
 *     VERIFY against the STM32H723 datasheet pin-definition table).
 *   - Synchronous AHB clock (CCR CKMODE = HCLK/4): independent of
 *     the RCC kernel-clock mux / PLL2 state, so the ADC works
 *     whatever clocks.c has or has not configured.
 *   - Longest sampling time: the node source is the R25/R26
 *     divider (~27 kohm Thevenin), a high-impedance source.
 *   - 12-bit single conversion per call; callers sample at 10 Hz.
 */
#include "hv_sense.h"
#include "board.h"
#include "gpio.h"

/* ADC1 register offsets (STM32H7 ADC) - VERIFY against RM0468. */
#define ADC_ISR   (ADC1_BASE + 0x00u)
#define ADC_CR    (ADC1_BASE + 0x08u)
#define ADC_CFGR  (ADC1_BASE + 0x0Cu)
#define ADC_SMPR1 (ADC1_BASE + 0x14u)
#define ADC_PCSEL (ADC1_BASE + 0x1Cu)
#define ADC_SQR1  (ADC1_BASE + 0x30u)
#define ADC_DR    (ADC1_BASE + 0x40u)
/* ADC12 common registers: ADC1_BASE + 0x300. */
#define ADC_CCR   (ADC1_BASE + 0x300u)
/* RCC AHB1ENR: offset 0xD8, ADC12EN bit 5 - VERIFY against RM0468. */
#define RCC_AHB1ENR (RCC_BASE + 0xD8u)
#define RCC_ADC12EN (1u << 5)

/* CR bits. */
#define ADC_CR_ADEN     (1u << 0)
#define ADC_CR_ADSTART  (1u << 2)
#define ADC_CR_ADVREGEN (1u << 28)
#define ADC_CR_DEEPPWD  (1u << 29)
#define ADC_CR_ADCAL    (1u << 31)
/* ISR bits. */
#define ADC_ISR_ADRDY (1u << 0)
#define ADC_ISR_EOC   (1u << 2)

/* VDDA nominal: +3V3A is set to 3.32 V (docs/03). The decision
 * thresholds in hv_ctrl (0.45 V / 2.5 V) sit far from every node
 * signature (0 / 0.94 / 3.3 V), so the exact VDDA does not move
 * any verdict. */
#define HV_SENSE_VDDA_MV 3320

static int sense_ready = 0;
static int sense_broken = 0;

static void delay_crude(void)
{
    /* ~tens of microseconds at any plausible core clock: the ADC
     * voltage regulator needs >= 10 us after ADVREGEN before
     * calibration (datasheet tADCVREG_SETUP - VERIFY). */
    volatile uint32_t i;
    for (i = 0; i < 40000u; i++) {
    }
}

static int wait_bits(uint32_t addr, uint32_t mask, int want_set)
{
    uint32_t budget = 1000000u;
    while (budget-- > 0u) {
        int set = (REG32(addr) & mask) != 0u;
        if (set == want_set) {
            return 0;
        }
    }
    return -1;
}

static int hv_sense_init(void)
{
    uint32_t ch = BOARD_HV_SENSE_ADC_CHANNEL;

    gpio_set_mode(BOARD_HV_SENSE_PORT, BOARD_HV_SENSE_PIN,
                  GPIO_MODE_ANALOG);
    gpio_set_pull(BOARD_HV_SENSE_PORT, BOARD_HV_SENSE_PIN, 0u);

    REG32(RCC_AHB1ENR) |= RCC_ADC12EN;
    (void)REG32(RCC_AHB1ENR); /* clock-enable synchronisation read */

    /* Synchronous clock: CKMODE (CCR bits 17:16) = 0b11 -> HCLK/4. */
    REG32(ADC_CCR) = (REG32(ADC_CCR) & ~(0x3u << 16)) | (0x3u << 16);

    /* Power the ADC up: exit deep-power-down, enable the internal
     * voltage regulator, wait for it to stabilise. */
    REG32(ADC_CR) &= ~ADC_CR_DEEPPWD;
    REG32(ADC_CR) |= ADC_CR_ADVREGEN;
    delay_crude();

    /* 12-bit resolution: CFGR RES (bits 4:2) = 0b010 - VERIFY.
     * Longest sample time for the channel: SMPR field = 0b111
     * (SMPR1 covers channels 0-9, 3 bits each). Preselect the
     * channel (PCSEL) - required on this ADC before conversion. */
    REG32(ADC_CFGR) = (REG32(ADC_CFGR) & ~(0x7u << 2)) | (0x2u << 2);
    if (ch < 10u) {
        REG32(ADC_SMPR1) = (REG32(ADC_SMPR1) & ~(0x7u << (ch * 3u)))
                         | (0x7u << (ch * 3u));
    }
    REG32(ADC_PCSEL) |= (1u << ch);
    /* Regular sequence: length 1, first (only) rank = channel. */
    REG32(ADC_SQR1) = (ch << 6);

    /* Single-ended calibration (ADCALDIF = 0), then enable. */
    REG32(ADC_CR) |= ADC_CR_ADCAL;
    if (wait_bits(ADC_CR, ADC_CR_ADCAL, 0) != 0) {
        return -1;
    }
    REG32(ADC_ISR) = ADC_ISR_ADRDY; /* clear before enabling */
    REG32(ADC_CR) |= ADC_CR_ADEN;
    if (wait_bits(ADC_ISR, ADC_ISR_ADRDY, 1) != 0) {
        return -1;
    }
    return 0;
}

int hv_sense_read_mv(void)
{
    uint32_t counts;

    if (sense_broken) {
        return -1;
    }
    if (!sense_ready) {
        if (hv_sense_init() != 0) {
            sense_broken = 1;
            return -1;
        }
        sense_ready = 1;
    }

    REG32(ADC_ISR) = ADC_ISR_EOC; /* clear stale end-of-conversion */
    REG32(ADC_CR) |= ADC_CR_ADSTART;
    if (wait_bits(ADC_ISR, ADC_ISR_EOC, 1) != 0) {
        return -1;
    }
    counts = REG32(ADC_DR) & 0xFFFu;
    return (int)((counts * (uint32_t)HV_SENSE_VDDA_MV) / 4095u);
}
