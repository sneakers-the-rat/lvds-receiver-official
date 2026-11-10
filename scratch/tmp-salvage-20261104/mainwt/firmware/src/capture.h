/* capture.h - double-buffered capture of the CDR output stream.
 *
 * State machine: IDLE -> ARMED -> CAPTURING -> (buffer full) ->
 * DRAINING (host is reading the full buffer while the other fills)
 * -> IDLE/ARMED ... The byte source is capture_dma_push(), the single
 * entry point the board DMA path calls; on this board that path is a
 * timer/SPI-slave DMA fed by the ADN2813 recovered clock/data, whose
 * register programming is sketched in capture.c and remains a
 * bring-up item. */
#ifndef CAPTURE_H
#define CAPTURE_H

#include <stdint.h>
#include <stddef.h>

#define CAPTURE_BUF_BYTES 8192u
#define CAPTURE_NUM_BUFS  2u

typedef enum {
    CAPTURE_IDLE = 0,
    CAPTURE_ARMED,
    CAPTURE_CAPTURING,
    CAPTURE_DRAINING
} capture_state_t;

typedef struct {
    capture_state_t state;
    uint8_t  active;             /* buffer being filled */
    uint32_t fill;               /* bytes in the active buffer */
    uint32_t ready_len;          /* valid bytes in the ready buffer */
    int      ready_valid;        /* a full/finished buffer awaits the host */
    uint32_t overruns;           /* pushes dropped: no free buffer */
    uint32_t buffers_completed;  /* total buffers handed to the host */
} capture_t;

void capture_init(capture_t *cap);
int  capture_arm(capture_t *cap);   /* IDLE -> ARMED */
int  capture_stop(capture_t *cap);  /* any -> IDLE, partial buffer dropped */

/* Board DMA entry point ("capture_dma_push stub"): the DMA/timer ISR
 * or its half/full-transfer callbacks copy recovered bytes in through
 * here. Implemented in capture.c against the SRAM double buffer.
 * Returns bytes accepted; short returns count as overruns. */
size_t capture_dma_push(capture_t *cap, const uint8_t *data, size_t len);

/* Host side: if a buffer is ready, returns its pointer/length and
 * moves CAPTURING->DRAINING; capture_release() frees it. */
const uint8_t *capture_get_ready(capture_t *cap, uint32_t *len_out);
void capture_release(capture_t *cap);

/* Register-programming sketch for the real timer/DMA path - NOT
 * called yet; see the long comment in capture.c. */
void capture_board_dma_init_sketch(void);

#endif /* CAPTURE_H */
