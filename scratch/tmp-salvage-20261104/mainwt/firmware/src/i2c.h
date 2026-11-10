/* i2c.h - polling, timeout-based I2C master for the board bus
 * (ADN2813 CDR + TMP117 temperature sensor share I2C1). */
#ifndef I2C_H
#define I2C_H

#include <stdint.h>
#include <stddef.h>

/* Return codes: 0 ok, -1 timeout, -2 NACK, -3 bad argument. */
typedef int i2c_result_t;

void i2c_init(void);

/* Register-style transactions (write pointer, then data / repeated
 * start + read), which is the access pattern both devices use. */
i2c_result_t i2c_write_regs(uint8_t dev_addr7, uint8_t reg,
                            const uint8_t *data, size_t len);
i2c_result_t i2c_read_regs(uint8_t dev_addr7, uint8_t reg,
                           uint8_t *data, size_t len);
i2c_result_t i2c_write_byte(uint8_t dev_addr7, uint8_t reg, uint8_t value);
i2c_result_t i2c_read_u16(uint8_t dev_addr7, uint8_t reg, uint16_t *out);

#endif /* I2C_H */
