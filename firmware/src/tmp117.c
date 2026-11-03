/*
 * tmp117.c - register numbers below (0x00 temp result, 0x0F device ID
 * with expected value 0x0117) are the standard TMP117 map; VERIFY
 * against datasheets/tmp117.pdf at bring-up.
 * Resolution: 0.0078125 C per LSB (1/128 C), signed 16-bit result.
 */
#include "tmp117.h"
#include "i2c.h"

#define TMP117_REG_TEMP   0x00u /* VERIFY vs datasheet */
#define TMP117_REG_CONFIG 0x01u /* VERIFY vs datasheet */
#define TMP117_REG_DEVID  0x0Fu /* VERIFY vs datasheet */
#define TMP117_DEVID_EXPECTED 0x0117u /* VERIFY vs datasheet */

int tmp117_init(void)
{
    uint16_t id = 0;
    int r = i2c_read_u16(TMP117_ADDR7, TMP117_REG_DEVID, &id);
    if (r != 0) {
        return r;
    }
    return (id == TMP117_DEVID_EXPECTED) ? 0 : -10;
}

int tmp117_read_raw(int16_t *raw_out)
{
    uint16_t v = 0;
    int r = i2c_read_u16(TMP117_ADDR7, TMP117_REG_TEMP, &v);
    if (r != 0) {
        return r;
    }
    *raw_out = (int16_t)v;
    return 0;
}

int tmp117_read_milli_c(int32_t *milli_c)
{
    int16_t raw = 0;
    int r = tmp117_read_raw(&raw);
    if (r != 0) {
        return r;
    }
    /* milli-C = raw * 1000 / 128 = raw * 125 / 16 */
    *milli_c = ((int32_t)raw * 125) / 16;
    return 0;
}

int tmp117_read_c(float *c_out)
{
    int16_t raw = 0;
    int r = tmp117_read_raw(&raw);
    if (r != 0) {
        return r;
    }
    *c_out = (float)raw * 0.0078125f;
    return 0;
}
