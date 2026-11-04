/*
 * spi.c - H7-style SPI register block (CR1/CR2/CFG1/CFG2/SR/TXDR/RXDR).
 * VERIFY every offset and bit against RM0468 at bring-up; the H7 SPI
 * differs substantially from the F-series SPI this code is NOT based on.
 *
 * Configuration intent: master, software slave management with a GPIO
 * slave select (the DAC driver owns SYNC), 8-bit data size, SPI mode 1
 * (CPOL 0, CPHA 1 - VERIFY what the DAC8562 wants vs its datasheet at
 * bring-up), baud prescaler targeting a few MHz from the kernel clock.
 */
#include "spi.h"
#include "board.h"
#include "gpio.h"

/* VERIFY against RM0468 at bring-up */
typedef struct {
    volatile uint32_t CR1;  /* 0x00 */
    volatile uint32_t CR2;  /* 0x04 */
    volatile uint32_t CFG1; /* 0x08 */
    volatile uint32_t CFG2; /* 0x0C */
    volatile uint32_t IER;  /* 0x10 */
    volatile uint32_t SR;   /* 0x14 */
    volatile uint32_t IFCR; /* 0x18 */
    volatile uint32_t TXDR; /* 0x20 (byte access used) */
    volatile uint32_t RXDR; /* 0x30 (byte access used) - VERIFY gap */
} spi_regs_t;

#define BOARD_SPI ((spi_regs_t *)(uintptr_t)BOARD_DAC_SPI_BASE)

#define SPI_CR1_SPE   (1u << 0)
#define SPI_CR1_CSTART (1u << 9)
#define SPI_CFG1_DSIZE (0x1Fu << 0)
#define SPI_CFG2_MASTER (1u << 22)
#define SPI_CFG2_SSM    (1u << 26)
#define SPI_SR_RXP    (1u << 0)
#define SPI_SR_TXP    (1u << 1)
#define SPI_SR_EOT    (1u << 3)

void spi_init(void)
{
    uint32_t v;
    /* Pin hookup, per the schematic (hw/CONNECTIONS.md): SPI3 SCK on
     * PC10, MOSI on PC12, alternate function per board.h. The DAC is
     * write-only, so no MISO pin is configured. This lives here (not
     * in gpio_init_board_pins) so the DAC's pins are configured in
     * exactly one place; SYNC (PA15) is a plain GPIO, set up by
     * gpio_init_board_pins and driven by the DAC driver. */
    gpio_set_mode(BOARD_DAC_SCK_PORT, BOARD_DAC_SCK_PIN,
                  GPIO_MODE_ALTERNATE);
    gpio_set_alt_func(BOARD_DAC_SCK_PORT, BOARD_DAC_SCK_PIN,
                      BOARD_DAC_SPI_AF);
    gpio_set_mode(BOARD_DAC_MOSI_PORT, BOARD_DAC_MOSI_PIN,
                  GPIO_MODE_ALTERNATE);
    gpio_set_alt_func(BOARD_DAC_MOSI_PORT, BOARD_DAC_MOSI_PIN,
                      BOARD_DAC_SPI_AF);
    BOARD_SPI->CR1 &= ~SPI_CR1_SPE;
    v = BOARD_SPI->CFG1;
    v &= ~SPI_CFG1_DSIZE;
    v |= (7u << 0);          /* DSIZE = 8 bits (value is bits-1) - VERIFY */
    v &= ~(0x7u << 28);
    v |= (4u << 28);         /* MBR prescaler /32 - VERIFY field position */
    BOARD_SPI->CFG1 = v;
    v = BOARD_SPI->CFG2;
    v |= SPI_CFG2_MASTER | SPI_CFG2_SSM;
    v &= ~(1u << 24);        /* CPOL = 0 - VERIFY field position */
    v |= (1u << 23);         /* CPHA = 1 (mode 1) - VERIFY field position */
    BOARD_SPI->CFG2 = v;
    BOARD_SPI->CR1 |= SPI_CR1_SPE;
}

int spi_transfer(const uint8_t *tx, uint8_t *rx, size_t len)
{
    size_t sent = 0;
    size_t received = 0;
    uint32_t t;
    BOARD_SPI->CR2 = (uint32_t)len; /* TSIZE - VERIFY semantics */
    BOARD_SPI->CR1 |= SPI_CR1_CSTART;
    t = BOARD_TIMEOUT_LOOPS * 4u;
    while ((sent < len || received < len) && t-- > 0u) {
        uint32_t sr = BOARD_SPI->SR;
        if ((sr & SPI_SR_TXP) != 0u && sent < len) {
            *(volatile uint8_t *)(uintptr_t)&BOARD_SPI->TXDR = tx[sent];
            sent++;
        }
        if ((sr & SPI_SR_RXP) != 0u && received < len) {
            uint8_t b = *(volatile uint8_t *)(uintptr_t)&BOARD_SPI->RXDR;
            if (rx != NULL) {
                rx[received] = b;
            }
            received++;
        }
    }
    if (sent < len || received < len) {
        return -1;
    }
    t = BOARD_TIMEOUT_LOOPS;
    while (t-- > 0u && (BOARD_SPI->SR & SPI_SR_EOT) == 0u) {
        /* wait for end of transfer */
    }
    return (t == 0u) ? -1 : 0;
}
