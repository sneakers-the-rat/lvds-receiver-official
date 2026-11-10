/* dac8562.h - TI DAC8562 dual 16-bit SPI DAC.
 * Channel A: comparator threshold. Channel B: APD bias (HV) setpoint.
 * Frame format / command codes: VERIFY against the DAC8562 datasheet
 * (in datasheets/) at bring-up - see dac8562.c. */
#ifndef DAC8562_H
#define DAC8562_H

#include <stdint.h>

/* Build one 24-bit SPI frame (pure function: command in bits [23:20]-
 * class field, address, then the 16-bit data word). Exposed so the
 * frame packing can be reviewed/tested without hardware. */
uint32_t dac8562_frame(uint8_t cmd, uint8_t addr, uint16_t data);

int dac8562_init(void);                    /* reset, internal ref ON, both channels powered */
int dac8562_set_threshold(uint16_t counts);/* channel A, write + update */
int dac8562_set_bias_setpoint(uint16_t counts); /* channel B, write + update */

#endif /* DAC8562_H */
