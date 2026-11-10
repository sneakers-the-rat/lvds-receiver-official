/* spi.h - polling SPI master for the DAC8562 (SPI3: PC10 SCK,
 * PC12 MOSI; SYNC is a GPIO owned by the DAC driver, PA15). */
#ifndef SPI_H
#define SPI_H

#include <stdint.h>
#include <stddef.h>

/* Return codes: 0 ok, -1 timeout. */
void spi_init(void);
int  spi_transfer(const uint8_t *tx, uint8_t *rx, size_t len);

#endif /* SPI_H */
