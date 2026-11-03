/*
 * capture.c - the state machine and double buffer are complete and
 * hardware-independent apart from the buffer section attribute. The
 * hardware byte source is NOT complete: see the sketch at the bottom.
 */
#include "capture.h"
#include "board.h"

/* Double buffer in AXI SRAM (512 KB region at 0x24000000, see
 * linker.ld) - that SRAM is reachable by the DMA masters that will
 * feed this path, unlike DTCM. VERIFY DMA reachability vs RM0468
 * (bus matrix) at bring-up. */
#if defined(__GNUC__)
__attribute__((section(".axi_sram"), aligned(32)))
#endif
static uint8_t capture_bufs[CAPTURE_NUM_BUFS][CAPTURE_BUF_BYTES];

void capture_init(capture_t *cap)
{
    cap->state = CAPTURE_IDLE;
    cap->active = 0;
    cap->fill = 0;
    cap->ready_len = 0;
    cap->ready_valid = 0;
    cap->overruns = 0;
    cap->buffers_completed = 0;
}

int capture_arm(capture_t *cap)
{
    if (cap->state != CAPTURE_IDLE) {
        return -1;
    }
    cap->fill = 0;
    cap->ready_valid = 0;
    cap->state = CAPTURE_ARMED;
    return 0;
}

int capture_stop(capture_t *cap)
{
    cap->state = CAPTURE_IDLE;
    cap->fill = 0;
    cap->ready_valid = 0;
    return 0;
}

size_t capture_dma_push(capture_t *cap, const uint8_t *data, size_t len)
{
    size_t accepted = 0;
    if (cap->state == CAPTURE_ARMED) {
        cap->state = CAPTURE_CAPTURING;
    }
    if (cap->state != CAPTURE_CAPTURING && cap->state != CAPTURE_DRAINING) {
        cap->overruns++;
        return 0;
    }
    while (accepted < len) {
        uint32_t space;
        size_t chunk;
        size_t i;
        space = CAPTURE_BUF_BYTES - cap->fill;
        if (space == 0u) {
            cap->overruns++;
            break;
        }
        chunk = len - accepted;
        if (chunk > space) {
            chunk = space;
        }
        for (i = 0; i < chunk; i++) {
            capture_bufs[cap->active][cap->fill + i] = data[accepted + i];
        }
        cap->fill += (uint32_t)chunk;
        accepted += chunk;
        if (cap->fill == CAPTURE_BUF_BYTES) {
            /* Buffer full: it becomes the ready buffer. */
            if (cap->ready_valid) {
                /* Previous ready buffer never released - the host is
                 * a full buffer behind. Count the rest as overrun
                 * rather than overwriting data the host is reading. */
                cap->overruns++;
                cap->fill = CAPTURE_BUF_BYTES; /* stay full, drop rest */
                break;
            }
            cap->ready_len = cap->fill;
            cap->ready_valid = 1;
            cap->buffers_completed++;
            cap->active = (uint8_t)(cap->active ^ 1u);
            cap->fill = 0;
            cap->state = CAPTURE_DRAINING;
        }
    }
    return accepted;
}

const uint8_t *capture_get_ready(capture_t *cap, uint32_t *len_out)
{
    if (!cap->ready_valid) {
        return NULL;
    }
    if (len_out != NULL) {
        *len_out = cap->ready_len;
    }
    return capture_bufs[cap->active ^ 1u];
}

void capture_release(capture_t *cap)
{
    cap->ready_valid = 0;
    cap->ready_len = 0;
    if (cap->state == CAPTURE_DRAINING) {
        /* The other buffer is still the active fill target. */
        cap->state = CAPTURE_CAPTURING;
    }
}

/*
 * capture_board_dma_init_sketch - deliberately NOT called anywhere.
 *
 * The real byte path on this board (docs/02) is:
 *   ADN2813 recovered data + recovered clock -> an MCU peripheral
 *   that can be externally clocked (SPI slave, or a timer input
 *   capture / SDMMC-class path) -> DMA in circular mode into
 *   capture_bufs -> half-transfer / transfer-complete callbacks call
 *   capture_dma_push().
 *
 * Register programming sketched (ALL VERIFY against RM0468):
 *   1. Enable DMA1 + DMAMUX1 + the chosen peripheral clocks (RCC).
 *   2. DMAMUX: route the peripheral's DMA request to DMA1 stream 0.
 *   3. DMA stream: peripheral-to-memory, byte width, circular mode,
 *      source = peripheral data register (TIM2/SPIx - VERIFY base
 *      addresses in board.h), destination alternating between
 *      capture_bufs[0] and capture_bufs[1] (double-buffer mode).
 *   4. Peripheral: slave/external-clock configuration so each
 *      recovered-clock edge moves one recovered-data bit/byte; the
 *      exact peripheral choice (SPI slave vs timer) depends on the
 *      ADN2813 output format decision at schematic time - THAT open
 *      decision is why this is a sketch and not finished code.
 *   5. NVIC: enable the DMA stream IRQ; callbacks feed
 *      capture_dma_push() and nothing else (keep the ISR short).
 *
 * No register writes are performed by this function in rev A: writing
 * guessed DMA registers would be worse than writing none, because it
 * could start transfers from random addresses. The function exists so
 * the call graph has its final shape.
 */
void capture_board_dma_init_sketch(void)
{
    /* Intentionally empty - see the block comment above. */
}
