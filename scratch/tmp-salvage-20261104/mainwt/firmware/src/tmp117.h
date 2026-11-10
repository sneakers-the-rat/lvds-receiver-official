/* tmp117.h - TI TMP117 temperature sensor (I2C), mounted 3 mm from
 * the APD (docs/02). Register addresses: VERIFY vs datasheets/tmp117.pdf. */
#ifndef TMP117_H
#define TMP117_H

#include <stdint.h>

/* I2C address with ADD0 tied to GND. VERIFY vs datasheet/board. */
#define TMP117_ADDR7 0x48u

int tmp117_init(void);                       /* checks the device ID register */
int tmp117_read_raw(int16_t *raw_out);       /* signed 16-bit temperature word */
int tmp117_read_milli_c(int32_t *milli_c);   /* raw * 0.0078125 C/LSB */
int tmp117_read_c(float *c_out);

#endif /* TMP117_H */
