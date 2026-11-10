/* usb_app.h - application-level host protocol handler.
 *
 * This layer is complete and transport-independent: it consumes one
 * command frame from a byte buffer and produces one response frame.
 * Carrying the frames over USB is usb_device_if.h's job (stubbed).
 *
 * Frame format (little-endian payloads):
 *   command:  [opcode][payload...]
 *   response: [opcode | 0x80][status][payload...]   status 0 = OK
 *
 * Opcodes and payloads:
 *   GET_INFO       0x01  -> "PDRX" magic, fw version u16, protocol u8
 *   SET_BIAS       0x02  in: float32 volts at 25 C (also enables HV,
 *                        subject to the interlock in hv_ctrl)
 *   SET_THRESHOLD  0x03  in: u16 DAC counts
 *   GET_STATUS     0x04  -> status struct (see usb_app.c)
 *   BER_TEST_START 0x05  in: u32 starting buffer_count
 *   BER_TEST_STOP  0x06  -> u32 bit_errors, u32 bits_checked,
 *                           u32 packets_failed (any buffer with errors)
 *   STREAM_START   0x07  arm the capture state machine
 *   STREAM_STOP    0x08  stop capture
 */
#ifndef USB_APP_H
#define USB_APP_H

#include <stdint.h>
#include <stddef.h>
#include "capture.h"
#include "hv_ctrl.h"

enum {
    USB_CMD_GET_INFO = 0x01,
    USB_CMD_SET_BIAS = 0x02,
    USB_CMD_SET_THRESHOLD = 0x03,
    USB_CMD_GET_STATUS = 0x04,
    USB_CMD_BER_TEST_START = 0x05,
    USB_CMD_BER_TEST_STOP = 0x06,
    USB_CMD_STREAM_START = 0x07,
    USB_CMD_STREAM_STOP = 0x08
};

enum {
    USB_STATUS_OK = 0,
    USB_STATUS_BAD_FRAME = 1,
    USB_STATUS_BAD_OPCODE = 2,
    USB_STATUS_INTERLOCK = 3,
    USB_STATUS_IO_ERROR = 4,
    USB_STATUS_BAD_STATE = 5
};

typedef struct {
    hv_ctrl_t *hv;
    capture_t *cap;
    uint16_t   threshold_counts;
    float      last_temp_c;
    int        temp_valid;
    int        los_asserted;
    /* BER test (Miniscope Zero PER mode, via codec PRBS-15) */
    int        ber_running;
    uint32_t   ber_buffer_count;  /* count for the NEXT buffer */
    uint32_t   ber_bit_errors;
    uint32_t   ber_bits_checked;
    uint32_t   ber_packets_failed;
    uint32_t   ber_current_buffer_errors;
    uint32_t   ber_bytes_in_buffer;
} usb_app_t;

void usb_app_init(usb_app_t *app, hv_ctrl_t *hv, capture_t *cap);
void usb_app_set_environment(usb_app_t *app, float temp_c,
                             int temp_valid, int los_asserted);

/* Process one command frame. Returns the response length (0 if the
 * output buffer is too small to answer at all). */
size_t usb_app_process(usb_app_t *app, const uint8_t *in, size_t in_len,
                       uint8_t *out, size_t out_cap);

/* While a BER test runs, decoded payload bytes stream through here in
 * order; each completed 5032-byte buffer is scored against the PRBS
 * stream for its buffer_count (a buffer with any error bit counts as
 * one failed packet, exactly as in the paper's PER mode). */
void usb_app_ber_feed(usb_app_t *app, const uint8_t *data, size_t len);

#endif /* USB_APP_H */
