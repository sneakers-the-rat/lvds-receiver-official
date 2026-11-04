/*
 * test_usb_framing.c - host round-trip of the firmware's host
 * protocol FRAMES through the real transport interface.
 *
 * What runs here is the real code at both ends of the wire format:
 * the test plays the host (it builds command frames exactly as a
 * host tool must, and decodes the response bytes), src/usb_app.c
 * plays the device, and the two are connected by an in-memory
 * loopback that implements src/usb_device_if.h - the same interface
 * the TinyUSB transport implements on target. The device side is
 * pumped with the same recv -> process -> send block main.c runs.
 * What this proves: the framing contract (opcodes, payload layouts,
 * status codes, the interface's byte-pipe semantics) is consistent
 * end to end. What it cannot prove: anything about USB itself.
 *
 * The control backends usb_app.c drives (HV, DAC, capture) are
 * mocks: they reproduce the function contracts against the real
 * state structs, and record what the protocol asked them to do.
 */
#include <stdio.h>
#include <string.h>

#include "usb_app.h"
#include "usb_device_if.h"

/* ------------------------------------------------------------------ */
/* Mock control backends (the real ones are register-level)           */
/* ------------------------------------------------------------------ */
static uint16_t mock_threshold_counts;
static int mock_threshold_writes;

int dac8562_set_threshold(uint16_t counts)
{
    mock_threshold_counts = counts;
    mock_threshold_writes++;
    return 0;
}

void hv_ctrl_set_setpoint(hv_ctrl_t *hv, float volts_at_25c)
{
    hv->setpoint_v_at_25c = volts_at_25c;
}

int hv_ctrl_enable(hv_ctrl_t *hv, int on)
{
    if (on && !hv->interlock_ok) {
        return -1;
    }
    hv->enabled = on;
    return 0;
}

int capture_arm(capture_t *cap)
{
    if (cap->state != CAPTURE_IDLE) {
        return -1;
    }
    cap->state = CAPTURE_ARMED;
    return 0;
}

int capture_stop(capture_t *cap)
{
    cap->state = CAPTURE_IDLE;
    return 0;
}

/* ------------------------------------------------------------------ */
/* Loopback transport behind usb_device_if.h                          */
/* ------------------------------------------------------------------ */
#define LB_CAP 16384u
static uint8_t lb_h2d[LB_CAP]; static size_t lb_h2d_len;
static uint8_t lb_d2h[LB_CAP]; static size_t lb_d2h_len;

int usb_dev_init(void) { return USB_DEV_OK; }
int usb_dev_connected(void) { return 1; }

int usb_dev_send(const uint8_t *data, size_t len)
{
    if (lb_d2h_len + len > LB_CAP) {
        return USB_DEV_IO_ERROR;
    }
    memcpy(lb_d2h + lb_d2h_len, data, len);
    lb_d2h_len += len;
    return USB_DEV_OK;
}

int usb_dev_recv(uint8_t *buf, size_t cap)
{
    size_t n;
    if (lb_h2d_len == 0u) {
        return USB_DEV_NO_DATA;
    }
    n = lb_h2d_len < cap ? lb_h2d_len : cap;
    memcpy(buf, lb_h2d, n);
    memmove(lb_h2d, lb_h2d + n, lb_h2d_len - n);
    lb_h2d_len -= n;
    return (int)n;
}

static void host_write(const uint8_t *data, size_t len)
{
    memcpy(lb_h2d + lb_h2d_len, data, len);
    lb_h2d_len += len;
}

static size_t host_read(uint8_t *buf, size_t cap)
{
    size_t n = lb_d2h_len < cap ? lb_d2h_len : cap;
    memcpy(buf, lb_d2h, n);
    memmove(lb_d2h, lb_d2h + n, lb_d2h_len - n);
    lb_d2h_len -= n;
    return n;
}

/* ------------------------------------------------------------------ */
/* Device under test: real usb_app + the same poll block as main.c    */
/* ------------------------------------------------------------------ */
static hv_ctrl_t hv;
static capture_t cap;
static usb_app_t app;

static void device_poll(void)
{
    uint8_t cmd[64];
    uint8_t resp[64];
    int n = usb_dev_recv(cmd, sizeof cmd);
    if (n > 0) {
        size_t rlen = usb_app_process(&app, cmd, (size_t)n,
                                      resp, sizeof resp);
        if (rlen > 0u) {
            (void)usb_dev_send(resp, rlen);
        }
    }
}

static size_t roundtrip(const uint8_t *cmd, size_t cmd_len,
                        uint8_t *resp, size_t resp_cap)
{
    host_write(cmd, cmd_len);
    device_poll();
    return host_read(resp, resp_cap);
}

static int failures = 0;

#define CHECK(cond, name)                                              \
    do {                                                               \
        if (cond) {                                                    \
            printf("PASS %s\n", (name));                               \
        } else {                                                       \
            printf("FAIL %s (line %d)\n", (name), __LINE__);           \
            failures++;                                                \
        }                                                              \
    } while (0)

static uint16_t rd_u16(const uint8_t *p)
{
    return (uint16_t)((uint16_t)p[0] | ((uint16_t)p[1] << 8));
}
static uint32_t rd_u32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8)
         | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

int main(void)
{
    uint8_t resp[64];
    size_t n;

    memset(&hv, 0, sizeof hv);
    memset(&cap, 0, sizeof cap);
    cap.state = CAPTURE_IDLE;
    usb_app_init(&app, &hv, &cap);

    /* No input queued: the device stays silent. */
    device_poll();
    CHECK(host_read(resp, sizeof resp) == 0u,
          "framing: idle device produces no bytes");

    /* GET_INFO round trip. */
    {
        const uint8_t cmd[] = { USB_CMD_GET_INFO };
        n = roundtrip(cmd, sizeof cmd, resp, sizeof resp);
        CHECK(n == 9u && resp[0] == (USB_CMD_GET_INFO | 0x80u)
              && resp[1] == USB_STATUS_OK
              && memcmp(resp + 2, "PDRX", 4) == 0
              && rd_u16(resp + 6) == 0x0001u && resp[8] == 1u,
              "framing: GET_INFO -> PDRX magic, fw 0.1, protocol 1");
    }

    /* SET_THRESHOLD reaches the (mock) DAC and reads back in status. */
    {
        const uint8_t cmd[] = { USB_CMD_SET_THRESHOLD, 0x34, 0x12 };
        n = roundtrip(cmd, sizeof cmd, resp, sizeof resp);
        CHECK(n == 2u && resp[0] == (USB_CMD_SET_THRESHOLD | 0x80u)
              && resp[1] == USB_STATUS_OK
              && mock_threshold_writes == 1
              && mock_threshold_counts == 0x1234u,
              "framing: SET_THRESHOLD delivered 0x1234 to the DAC backend");
    }
    {
        const uint8_t cmd[] = { USB_CMD_GET_STATUS };
        n = roundtrip(cmd, sizeof cmd, resp, sizeof resp);
        CHECK(n == 32u && resp[1] == USB_STATUS_OK
              && rd_u16(resp + 2 + 6) == 0x1234u,
              "framing: GET_STATUS reports the threshold just set");
    }

    /* SET_BIAS honours the interlock gate, both ways. */
    {
        const uint8_t cmd[] = { USB_CMD_SET_BIAS,
                                0x00, 0x00, 0x48, 0x43 }; /* 200.0f */
        hv.interlock_ok = 0;
        n = roundtrip(cmd, sizeof cmd, resp, sizeof resp);
        CHECK(n == 2u && resp[1] == USB_STATUS_INTERLOCK && !hv.enabled,
              "framing: SET_BIAS with open interlock -> INTERLOCK, HV off");
        hv.interlock_ok = 1;
        n = roundtrip(cmd, sizeof cmd, resp, sizeof resp);
        CHECK(n == 2u && resp[1] == USB_STATUS_OK && hv.enabled
              && hv.setpoint_v_at_25c == 200.0f,
              "framing: SET_BIAS 200 V with interlock -> OK, HV enabled");
    }

    /* BER test start/stop echoes zeroed counters for an unfed test. */
    {
        const uint8_t start[] = { USB_CMD_BER_TEST_START,
                                  7, 0, 0, 0 };
        const uint8_t stop[] = { USB_CMD_BER_TEST_STOP };
        n = roundtrip(start, sizeof start, resp, sizeof resp);
        CHECK(n == 2u && resp[1] == USB_STATUS_OK && app.ber_running,
              "framing: BER_TEST_START arms the scorer");
        n = roundtrip(stop, sizeof stop, resp, sizeof resp);
        CHECK(n == 14u && resp[1] == USB_STATUS_OK
              && rd_u32(resp + 2) == 0u && rd_u32(resp + 6) == 0u
              && rd_u32(resp + 10) == 0u && !app.ber_running,
              "framing: BER_TEST_STOP returns zeroed counters, disarms");
    }

    /* STREAM_START/STOP drive the capture state machine. */
    {
        const uint8_t start[] = { USB_CMD_STREAM_START };
        const uint8_t stop[] = { USB_CMD_STREAM_STOP };
        n = roundtrip(start, sizeof start, resp, sizeof resp);
        CHECK(n == 2u && resp[1] == USB_STATUS_OK
              && cap.state == CAPTURE_ARMED,
              "framing: STREAM_START arms capture");
        n = roundtrip(start, sizeof start, resp, sizeof resp);
        CHECK(n == 2u && resp[1] == USB_STATUS_BAD_STATE,
              "framing: STREAM_START while armed -> BAD_STATE");
        n = roundtrip(stop, sizeof stop, resp, sizeof resp);
        CHECK(n == 2u && resp[1] == USB_STATUS_OK
              && cap.state == CAPTURE_IDLE,
              "framing: STREAM_STOP returns capture to IDLE");
    }

    /* Malformed input is answered, not swallowed. */
    {
        const uint8_t bad_op[] = { 0x7F };
        const uint8_t short_frame[] = { USB_CMD_SET_THRESHOLD, 0x01 };
        n = roundtrip(bad_op, sizeof bad_op, resp, sizeof resp);
        CHECK(n == 2u && resp[0] == 0xFFu
              && resp[1] == USB_STATUS_BAD_OPCODE,
              "framing: unknown opcode -> BAD_OPCODE");
        n = roundtrip(short_frame, sizeof short_frame, resp, sizeof resp);
        CHECK(n == 2u && resp[1] == USB_STATUS_BAD_FRAME,
              "framing: truncated SET_THRESHOLD -> BAD_FRAME");
    }

    if (failures == 0) {
        printf("RESULT: ALL TESTS PASSED\n");
        return 0;
    }
    printf("RESULT: %d FAILURE(S)\n", failures);
    return 1;
}
