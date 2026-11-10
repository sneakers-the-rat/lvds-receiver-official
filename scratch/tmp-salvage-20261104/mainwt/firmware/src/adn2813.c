/*
 * adn2813.c - skeleton-plus: the I2C transaction logic is complete
 * (via i2c.c); the ADN2813 register numbers and the rate scaling are
 * NOT verified - the register map is not among the datasheet
 * material extracted into datasheets/MANIFEST.md. Every register
 * constant below carries its VERIFY marker; fill them in from the
 * datasheet as bring-up item (see README) before trusting any value
 * the I2C paths return. The status pins (LOS/LOL) need no register
 * map: they are read as GPIOs, with pin numbers and polarity from
 * the manifest's pin-function extraction.
 */
#include "adn2813.h"
#include "board.h"
#include "gpio.h"
#include "i2c.h"

/* VERIFY vs ADN2813 datasheet - placeholder register assignments.
 * REG_STATUS is used only as an init presence probe (any readable
 * register proves the part ACKs); LOL no longer comes from a
 * register - it is a hardware pin, read in adn2813_lol_asserted(). */
#define ADN2813_REG_STATUS    0x00u /* VERIFY: status register */
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
    /* LOL is a hardware pin on the ADN2813 (pin 16) routed to PA2;
     * LVTTL active high (datasheets/MANIFEST.md), so the pin value
     * is the assertion state. Reading the pin replaces an earlier
     * read of an unverified I2C status-register bit. */
    return gpio_read(BOARD_CDR_LOL_PORT, BOARD_CDR_LOL_PIN);
}

int adn2813_los_asserted(void)
{
    /* LOS is a hardware pin on the ADN2813 (pin 22) routed to PB14;
     * LVTTL active high (datasheets/MANIFEST.md), so the pin value
     * is the assertion state. Reading the pin is the primary path
     * (it works even if I2C is down). */
    return gpio_read(BOARD_CDR_LOS_PORT, BOARD_CDR_LOS_PIN);
}
