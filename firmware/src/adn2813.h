/* adn2813.h - Analog Devices ADN2813 continuous-rate CDR (I2C).
 * ALL register numbers in adn2813.c are marked VERIFY vs the ADN2813
 * datasheet: the part is not in datasheets/ in this repo, so nothing
 * here claims a checked register map. */
#ifndef ADN2813_H
#define ADN2813_H

#include <stdint.h>

#define ADN2813_ADDR7 0x40u /* VERIFY vs datasheet (address pins) */

int adn2813_init(void);
/* Rate readback: returns the CDR's reported data rate in kbit/s, or a
 * negative error. The register pair and scaling are VERIFY items. */
int adn2813_read_rate_kbps(uint32_t *kbps_out);
/* Status: 1 = asserted, 0 = not asserted, negative = I2C error. */
int adn2813_los_asserted(void);  /* loss of signal */
int adn2813_lol_asserted(void);  /* loss of lock */

#endif /* ADN2813_H */
