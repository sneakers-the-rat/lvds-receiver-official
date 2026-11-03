/*
 * adn2813.c - skeleton-plus: the I2C transaction logic is complete
 * (via i2c.c); the ADN2813 register numbers and the rate scaling are
 * NOT verified - there is no ADN2813 datasheet in datasheets/ yet.
 * Every constant below carries its VERIFY marker; fill them in from
 * the datasheet as bring-up item (see README) before trusting any
 * value this driver returns.
 */
#include "adn2813.h"
#include "board.h"
#include "gpio.h"
#include "i2c.h"

/* VERIFY vs ADN2813 datasheet - placeholder register assignments: */
#define ADN2813_REG_STATUS    0x00u /* VERIFY: status/LOL register */
#define ADN2813_STATUS_LOL    0x01u /* VERIFY: LOL bit mask */
#define ADN2813_REG_RATE_MSB  0x02u /* VERIFY: rate readback MSB */
#define ADN2813_REG_RATE_LSB  0x03u /* VERIFY: rate readback LSB */
/* VERIFY: rate readback unit. Placeholder assumption: the 16-bit
 * readback counts in units of 10 kbit/s (so 50 Mbps reads 5000). */
#define ADN2813_RATE_UNIT_KBPS 10u /* VERIFY vs datasheet */

int adn2813_init(void)
{
    /* The ADN2813 needs no reference clock and locks autonomously;
     * "init" here is only a presence probe: a status read that NACKs
     * or times out tells main.c the CDR is absent/not powered. */
    uint8_t status = 0;
    return i2c_read_regs(ADN2813_ADDR7, ADN2813_REG_STATUS, &status, 1u);
}

int adn2813_read_rate_kbps(uint32_t *kbps_out)
{
    uint8_t b[2];
    int r = i2c_read_regs(ADN2813_ADDR7, ADN2813_REG_RATE_MSB, b, 2u);
    uint32_t raw;
    if (r != 0) {
        return r;
    }
    raw = ((uint32_t)b[0] << 8) | (uint32_t)b[1];
    *kbps_out = raw * ADN2813_RATE_UNIT_KBPS;
    return 0;
}

int adn2813_lol_asserted(void)
{
    uint8_t status = 0;
    int r = i2c_read_regs(ADN2813_ADDR7, ADN2813_REG_STATUS, &status, 1u);
    if (r != 0) {
        return r;
    }
    return (status & ADN2813_STATUS_LOL) != 0u;
}

int adn2813_los_asserted(void)
{
    /* LOS is a hardware pin on the ADN2813 routed to BOARD_LOS_PIN;
     * reading the pin is the primary path (it works even if I2C is
     * down). Polarity: VERIFY vs datasheet at bring-up. */
    return gpio_read(BOARD_LOS_PORT, BOARD_LOS_PIN);
}
