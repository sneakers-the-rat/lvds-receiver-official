/*
 * i2c.c - full transaction logic for a register-addressed I2C slave,
 * polling the ISR flags with a bounded timeout on every wait, so a
 * missing/NACKing device produces an error code instead of a hang.
 *
 * Register offsets and bit positions are the standard STM32 I2C
 * peripheral layout (CR1/CR2/TIMINGR/ISR/ICR/RXDR/TXDR).
 * VERIFY against RM0468 at bring-up - in particular the TIMINGR value
 * below is an uncomputed placeholder class value for ~100 kHz from a
 * 137.5 MHz kernel clock; compute the real one at bring-up.
 */
#include "i2c.h"
#include "board.h"

/* I2C register block - VERIFY against RM0468 at bring-up */
typedef struct {
    volatile uint32_t CR1;    /* 0x00 */
    volatile uint32_t CR2;    /* 0x04 */
    volatile uint32_t OAR1;   /* 0x08 */
    volatile uint32_t OAR2;   /* 0x0C */
    volatile uint32_t TIMINGR;/* 0x10 */
    volatile uint32_t TIMEOUTR;/* 0x14 */
    volatile uint32_t ISR;    /* 0x18 */
    volatile uint32_t ICR;    /* 0x1C */
    volatile uint32_t PECR;   /* 0x20 */
    volatile uint32_t RXDR;   /* 0x24 */
    volatile uint32_t TXDR;   /* 0x28 */
} i2c_regs_t;

#define BOARD_I2C ((i2c_regs_t *)(uintptr_t)I2C1_BASE)

#define I2C_CR1_PE      (1u << 0)
#define I2C_CR2_SADD    (0x3FFu << 0)
#define I2C_CR2_RD_WRN  (1u << 10)
#define I2C_CR2_START   (1u << 13)
#define I2C_CR2_STOP    (1u << 14)
#define I2C_CR2_NACK    (1u << 15)
#define I2C_CR2_NBYTES  (0xFFu << 16)
#define I2C_CR2_AUTOEND (1u << 25)

#define I2C_ISR_TXIS    (1u << 1)
#define I2C_ISR_RXNE    (1u << 2)
#define I2C_ISR_NACKF   (1u << 4)
#define I2C_ISR_STOPF   (1u << 5)
#define I2C_ISR_TC      (1u << 6)
#define I2C_ISR_BUSY    (1u << 15)

#define I2C_ICR_NACKCF  (1u << 4)
#define I2C_ICR_STOPCF  (1u << 5)

static i2c_result_t wait_isr(uint32_t mask)
{
    uint32_t t = BOARD_TIMEOUT_LOOPS;
    while (t-- > 0u) {
        uint32_t isr = BOARD_I2C->ISR;
        if ((isr & I2C_ISR_NACKF) != 0u) {
            BOARD_I2C->ICR = I2C_ICR_NACKCF;
            return -2;
        }
        if ((isr & mask) != 0u) {
            return 0;
        }
    }
    return -1;
}

static i2c_result_t wait_not_busy(void)
{
    uint32_t t = BOARD_TIMEOUT_LOOPS;
    while (t-- > 0u) {
        if ((BOARD_I2C->ISR & I2C_ISR_BUSY) == 0u) {
            return 0;
        }
    }
    return -1;
}

static void set_transfer(uint8_t addr7, int read_dir, size_t nbytes,
                         int autoend)
{
    uint32_t cr2 = BOARD_I2C->CR2;
    cr2 &= ~(I2C_CR2_SADD | I2C_CR2_RD_WRN | I2C_CR2_NBYTES | I2C_CR2_AUTOEND);
    cr2 |= ((uint32_t)addr7 << 1);
    if (read_dir) {
        cr2 |= I2C_CR2_RD_WRN;
    }
    cr2 |= ((uint32_t)nbytes << 16);
    if (autoend) {
        cr2 |= I2C_CR2_AUTOEND;
    }
    BOARD_I2C->CR2 = cr2;
}

void i2c_init(void)
{
    uint32_t t;
    BOARD_I2C->CR1 &= ~I2C_CR1_PE;
    /* TIMINGR for ~100 kHz (standard mode) - PLACEHOLDER: compute the
     * real PRESC/SCLDEL/SDADEL/SCLH/SCLL fields for the actual I2C
     * kernel clock at bring-up. VERIFY against RM0468. */
    BOARD_I2C->TIMINGR = 0x307075B1u; /* VERIFY - placeholder, see above */
    BOARD_I2C->CR1 |= I2C_CR1_PE;
    t = BOARD_TIMEOUT_LOOPS;
    while (t-- > 0u && (BOARD_I2C->CR1 & I2C_CR1_PE) == 0u) {
        /* spin until PE reads back */
    }
}

i2c_result_t i2c_write_regs(uint8_t dev_addr7, uint8_t reg,
                            const uint8_t *data, size_t len)
{
    i2c_result_t r;
    size_t i;
    if (len > 254u) {
        return -3; /* NBYTES field + the register byte must fit 255 */
    }
    r = wait_not_busy();
    if (r != 0) {
        return r;
    }
    set_transfer(dev_addr7, 0, len + 1u, 1 /*autoend: STOP at end*/);
    BOARD_I2C->CR2 |= I2C_CR2_START;
    r = wait_isr(I2C_ISR_TXIS);
    if (r != 0) {
        return r;
    }
    BOARD_I2C->TXDR = reg;
    for (i = 0; i < len; i++) {
        r = wait_isr(I2C_ISR_TXIS);
        if (r != 0) {
            return r;
        }
        BOARD_I2C->TXDR = data[i];
    }
    r = wait_isr(I2C_ISR_STOPF);
    if (r != 0) {
        return r;
    }
    BOARD_I2C->ICR = I2C_ICR_STOPCF;
    return 0;
}

i2c_result_t i2c_read_regs(uint8_t dev_addr7, uint8_t reg,
                           uint8_t *data, size_t len)
{
    i2c_result_t r;
    size_t i;
    if (len == 0u || len > 255u) {
        return -3;
    }
    r = wait_not_busy();
    if (r != 0) {
        return r;
    }
    /* Phase 1: write the register pointer, no STOP (repeated start). */
    set_transfer(dev_addr7, 0, 1u, 0);
    BOARD_I2C->CR2 |= I2C_CR2_START;
    r = wait_isr(I2C_ISR_TXIS);
    if (r != 0) {
        return r;
    }
    BOARD_I2C->TXDR = reg;
    r = wait_isr(I2C_ISR_TC);
    if (r != 0) {
        return r;
    }
    /* Phase 2: repeated START as a read, AUTOEND gives the final STOP. */
    set_transfer(dev_addr7, 1, len, 1);
    BOARD_I2C->CR2 |= I2C_CR2_START;
    for (i = 0; i < len; i++) {
        r = wait_isr(I2C_ISR_RXNE);
        if (r != 0) {
            return r;
        }
        data[i] = (uint8_t)BOARD_I2C->RXDR;
    }
    r = wait_isr(I2C_ISR_STOPF);
    if (r != 0) {
        return r;
    }
    BOARD_I2C->ICR = I2C_ICR_STOPCF;
    return 0;
}

i2c_result_t i2c_write_byte(uint8_t dev_addr7, uint8_t reg, uint8_t value)
{
    return i2c_write_regs(dev_addr7, reg, &value, 1u);
}

i2c_result_t i2c_read_u16(uint8_t dev_addr7, uint8_t reg, uint16_t *out)
{
    uint8_t b[2];
    i2c_result_t r = i2c_read_regs(dev_addr7, reg, b, 2u);
    if (r != 0) {
        return r;
    }
    *out = (uint16_t)(((uint16_t)b[0] << 8) | (uint16_t)b[1]);
    return 0;
}
