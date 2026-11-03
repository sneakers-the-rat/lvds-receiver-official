/*
 * dac8562.c
 *
 * 24-bit frame, MSB first (VERIFY bit layout vs the DAC8562 datasheet
 * at bring-up):
 *   DB23..DB20  command
 *   DB19..DB16  address
 *   DB15..DB0   data
 * Command codes used here (VERIFY vs datasheet):
 *   0x3 (011b in DB23..DB21-class encoding, shown here as the 4-bit
 *        field value used by this driver) = write to input register n
 *        and update DAC n
 *   0x4 = power down/up control, 0x5 = software reset,
 *   0x7 = internal reference setup (data bit 0: 1 = reference ON)
 * Address (VERIFY vs datasheet): 0x0 = DAC A, 0x1 = DAC B, 0x7 = all.
 *
 * The exact packing below keeps command and address in separate
 * nibbles so that a datasheet correction at bring-up is a one-line
 * change to dac8562_frame() or the constants, and every call site is
 * already correct in intent.
 */
#include "dac8562.h"
#include "board.h"
#include "gpio.h"
#include "spi.h"

#define DAC_CMD_WRITE_UPDATE 0x3u /* VERIFY vs datasheet */
#define DAC_CMD_POWER        0x4u /* VERIFY vs datasheet */
#define DAC_CMD_RESET        0x5u /* VERIFY vs datasheet */
#define DAC_CMD_INT_REF      0x7u /* VERIFY vs datasheet */
#define DAC_ADDR_A           0x0u /* VERIFY vs datasheet */
#define DAC_ADDR_B           0x1u /* VERIFY vs datasheet */
#define DAC_ADDR_ALL         0x7u /* VERIFY vs datasheet */

uint32_t dac8562_frame(uint8_t cmd, uint8_t addr, uint16_t data)
{
    return ((uint32_t)(cmd & 0xFu) << 20)
         | ((uint32_t)(addr & 0xFu) << 16)
         | (uint32_t)data;
}

static int dac_write(uint8_t cmd, uint8_t addr, uint16_t data)
{
    uint32_t f = dac8562_frame(cmd, addr, data);
    uint8_t tx[3];
    int r;
    tx[0] = (uint8_t)(f >> 16);
    tx[1] = (uint8_t)(f >> 8);
    tx[2] = (uint8_t)(f >> 0);
    gpio_write(BOARD_DAC_CS_PORT, BOARD_DAC_CS_PIN, 0);
    r = spi_transfer(tx, NULL, 3u);
    gpio_write(BOARD_DAC_CS_PORT, BOARD_DAC_CS_PIN, 1);
    return r;
}

int dac8562_init(void)
{
    int r;
    /* Software reset (data ignored). */
    r = dac_write(DAC_CMD_RESET, DAC_ADDR_ALL, 0u);
    if (r != 0) {
        return r;
    }
    /* Internal reference ON (data bit 0 = 1) - gives the 2.5 V full
     * scale the threshold/bias dividers were designed around.
     * VERIFY data-bit meaning vs datasheet. */
    r = dac_write(DAC_CMD_INT_REF, DAC_ADDR_ALL, 0x0001u);
    if (r != 0) {
        return r;
    }
    /* Power up both DACs (data 0 = both channels normal operation;
     * VERIFY encoding vs datasheet). */
    r = dac_write(DAC_CMD_POWER, DAC_ADDR_ALL, 0u);
    if (r != 0) {
        return r;
    }
    /* Safe starting outputs: threshold mid-scale is NOT safe for the
     * comparator in all states, so both channels start at 0 and the
     * owning modules (main / hv_ctrl) raise them deliberately. */
    r = dac8562_set_threshold(0u);
    if (r != 0) {
        return r;
    }
    return dac8562_set_bias_setpoint(0u);
}

int dac8562_set_threshold(uint16_t counts)
{
    return dac_write(DAC_CMD_WRITE_UPDATE, DAC_ADDR_A, counts);
}

int dac8562_set_bias_setpoint(uint16_t counts)
{
    return dac_write(DAC_CMD_WRITE_UPDATE, DAC_ADDR_B, counts);
}
