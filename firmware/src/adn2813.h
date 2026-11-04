/* adn2813.h - Analog Devices ADN2813 continuous-rate CDR (I2C).
 * What is sourced and what is not: the pinout, the LOS/LOL pin
 * numbers and polarity, and the I2C address are corroborated by
 * datasheets/MANIFEST.md (pin functions extracted from the official
 * Rev. C datasheet text) and hw/CONNECTIONS.md. The I2C REGISTER
 * numbers in adn2813.c are not in the manifest and remain marked
 * VERIFY - nothing here claims a checked register map. */
#ifndef ADN2813_H
#define ADN2813_H

#include <stdint.h>

#define ADN2813_ADDR7 0x40u /* SADDR5 tied to GND on the board;
                               address per hw/CONNECTIONS.md and
                               datasheets/MANIFEST.md */

int adn2813_init(void);
/* Rate readback: returns the CDR's reported data rate in kbit/s, or a
 * negative error. The register pair and scaling are VERIFY items. */
int adn2813_read_rate_kbps(uint32_t *kbps_out);
/* Status pins: 1 = asserted, 0 = not asserted. Both are hardware
 * pins on the part (LOS pin 22 -> PB14, LOL pin 16 -> PA2), read
 * directly, so they work even if I2C is down; both are LVTTL
 * active-high per the datasheet (MANIFEST.md). */
int adn2813_los_asserted(void);  /* loss of signal */
int adn2813_lol_asserted(void);  /* loss of lock */

#endif /* ADN2813_H */
