/* usb_app.c - the command parser described in usb_app.h. */
#include "usb_app.h"
#include "../codec/codec.h"
#include "dac8562.h"

#define FW_VERSION_MAJOR 0u
#define FW_VERSION_MINOR 1u
#define PROTOCOL_VERSION 1u

static void put_u16_le(uint8_t *d, uint16_t v)
{
    d[0] = (uint8_t)(v & 0xFFu);
    d[1] = (uint8_t)((v >> 8) & 0xFFu);
}
static void put_u32_le(uint8_t *d, uint32_t v)
{
    d[0] = (uint8_t)(v & 0xFFu);
    d[1] = (uint8_t)((v >> 8) & 0xFFu);
    d[2] = (uint8_t)((v >> 16) & 0xFFu);
    d[3] = (uint8_t)((v >> 24) & 0xFFu);
}
static uint16_t get_u16_le(const uint8_t *s)
{
    return (uint16_t)((uint16_t)s[0] | ((uint16_t)s[1] << 8));
}
static uint32_t get_u32_le(const uint8_t *s)
{
    return (uint32_t)s[0] | ((uint32_t)s[1] << 8)
         | ((uint32_t)s[2] << 16) | ((uint32_t)s[3] << 24);
}
static float get_f32_le(const uint8_t *s)
{
    /* Bit-preserving u32 -> float without aliasing tricks. */
    uint32_t u = get_u32_le(s);
    float f;
    const uint8_t *pu = (const uint8_t *)&u;
    uint8_t *pf = (uint8_t *)&f;
    size_t i;
    for (i = 0; i < 4u; i++) {
        pf[i] = pu[i];
    }
    return f;
}
static void put_f32_le(uint8_t *d, float f)
{
    uint32_t u;
    const uint8_t *pf = (const uint8_t *)&f;
    uint8_t *pu = (uint8_t *)&u;
    size_t i;
    for (i = 0; i < 4u; i++) {
        pu[i] = pf[i];
    }
    put_u32_le(d, u);
}

void usb_app_init(usb_app_t *app, hv_ctrl_t *hv, capture_t *cap)
{
    app->hv = hv;
    app->cap = cap;
    app->threshold_counts = 0;
    app->last_temp_c = 0.0f;
    app->temp_valid = 0;
    app->los_asserted = 0;
    app->ber_running = 0;
    app->ber_buffer_count = 0;
    app->ber_bit_errors = 0;
    app->ber_bits_checked = 0;
    app->ber_packets_failed = 0;
    app->ber_current_buffer_errors = 0;
    app->ber_bytes_in_buffer = 0;
}

void usb_app_set_environment(usb_app_t *app, float temp_c,
                             int temp_valid, int los_asserted)
{
    app->last_temp_c = temp_c;
    app->temp_valid = temp_valid;
    app->los_asserted = los_asserted;
}

void usb_app_ber_feed(usb_app_t *app, const uint8_t *data, size_t len)
{
    /* Score byte by byte against a regenerated stream. A fresh
     * checker is built per buffer from ber_buffer_count so a dropped
     * partial buffer resynchronises at the next buffer boundary -
     * the same reseed rule as the paper's PER mode. */
    while (len > 0u && app->ber_running) {
        codec_prbs15_checker_t chk;
        uint32_t room = CODEC_PRBS15_PAYLOAD_BYTES
                      - app->ber_bytes_in_buffer;
        size_t chunk = len;
        if (chunk > room) {
            chunk = room;
        }
        /* Regenerate from the buffer start and skip the bytes already
         * scored in this buffer: PRBS generation is cheap, and this
         * keeps the checker stateless between feeds. */
        {
            codec_prbs15_t gen;
            uint32_t i;
            codec_prbs15_init(
                &gen, codec_prbs15_seed_for_buffer(app->ber_buffer_count));
            for (i = 0; i < app->ber_bytes_in_buffer; i++) {
                (void)codec_prbs15_next_byte(&gen);
            }
            codec_prbs15_checker_init(&chk, app->ber_buffer_count);
            chk.gen = gen;
        }
        codec_prbs15_checker_feed(&chk, data, chunk);
        app->ber_current_buffer_errors += chk.bit_errors;
        app->ber_bit_errors += chk.bit_errors;
        app->ber_bits_checked += (uint32_t)chunk * 8u;
        app->ber_bytes_in_buffer += (uint32_t)chunk;
        data += chunk;
        len -= chunk;
        if (app->ber_bytes_in_buffer == CODEC_PRBS15_PAYLOAD_BYTES) {
            if (app->ber_current_buffer_errors > 0u) {
                app->ber_packets_failed++;
            }
            app->ber_current_buffer_errors = 0;
            app->ber_bytes_in_buffer = 0;
            app->ber_buffer_count++;
        }
    }
}

static size_t respond(uint8_t *out, size_t out_cap, uint8_t opcode,
                      uint8_t status, const uint8_t *payload,
                      size_t payload_len)
{
    size_t i;
    if (out_cap < 2u + payload_len) {
        return 0;
    }
    out[0] = (uint8_t)(opcode | 0x80u);
    out[1] = status;
    for (i = 0; i < payload_len; i++) {
        out[2u + i] = payload[i];
    }
    return 2u + payload_len;
}

size_t usb_app_process(usb_app_t *app, const uint8_t *in, size_t in_len,
                       uint8_t *out, size_t out_cap)
{
    uint8_t payload[32];
    uint8_t opcode;

    if (in_len < 1u) {
        return respond(out, out_cap, 0u, USB_STATUS_BAD_FRAME, NULL, 0u);
    }
    opcode = in[0];
    switch (opcode) {
    case USB_CMD_GET_INFO:
        payload[0] = 'P'; payload[1] = 'D';
        payload[2] = 'R'; payload[3] = 'X';
        put_u16_le(payload + 4,
                   (uint16_t)((FW_VERSION_MAJOR << 8) | FW_VERSION_MINOR));
        payload[6] = PROTOCOL_VERSION;
        return respond(out, out_cap, opcode, USB_STATUS_OK, payload, 7u);

    case USB_CMD_SET_BIAS: {
        float volts;
        int r;
        if (in_len < 5u) {
            return respond(out, out_cap, opcode,
                           USB_STATUS_BAD_FRAME, NULL, 0u);
        }
        volts = get_f32_le(in + 1);
        hv_ctrl_set_setpoint(app->hv, volts);
        r = hv_ctrl_enable(app->hv, 1);
        if (r != 0) {
            return respond(out, out_cap, opcode,
                           USB_STATUS_INTERLOCK, NULL, 0u);
        }
        return respond(out, out_cap, opcode, USB_STATUS_OK, NULL, 0u);
    }

    case USB_CMD_SET_THRESHOLD: {
        uint16_t counts;
        int r;
        if (in_len < 3u) {
            return respond(out, out_cap, opcode,
                           USB_STATUS_BAD_FRAME, NULL, 0u);
        }
        counts = get_u16_le(in + 1);
        r = dac8562_set_threshold(counts);
        if (r != 0) {
            return respond(out, out_cap, opcode,
                           USB_STATUS_IO_ERROR, NULL, 0u);
        }
        app->threshold_counts = counts;
        return respond(out, out_cap, opcode, USB_STATUS_OK, NULL, 0u);
    }

    case USB_CMD_GET_STATUS:
        /* Payload layout (offsets fixed by PROTOCOL_VERSION 1):
         *  0 u8  capture state      1 u8  hv enabled
         *  2 u8  interlock ok       3 u8  hv fault
         *  4 u8  LOS asserted       5 u8  temp valid
         *  6 u16 threshold counts   8 u16 hv DAC counts
         * 10 f32 temp C             14 f32 commanded bias V
         * 18 f32 setpoint V @25C    22 u32 capture overruns
         * 26 u32 buffers completed */
        payload[0] = (uint8_t)app->cap->state;
        payload[1] = (uint8_t)app->hv->enabled;
        payload[2] = (uint8_t)app->hv->interlock_ok;
        payload[3] = (uint8_t)app->hv->fault;
        payload[4] = (uint8_t)app->los_asserted;
        payload[5] = (uint8_t)app->temp_valid;
        put_u16_le(payload + 6, app->threshold_counts);
        put_u16_le(payload + 8, app->hv->dac_counts);
        put_f32_le(payload + 10, app->last_temp_c);
        put_f32_le(payload + 14, app->hv->commanded_v);
        put_f32_le(payload + 18, app->hv->setpoint_v_at_25c);
        put_u32_le(payload + 22, app->cap->overruns);
        put_u32_le(payload + 26, app->cap->buffers_completed);
        return respond(out, out_cap, opcode, USB_STATUS_OK, payload, 30u);

    case USB_CMD_BER_TEST_START:
        if (in_len < 5u) {
            return respond(out, out_cap, opcode,
                           USB_STATUS_BAD_FRAME, NULL, 0u);
        }
        app->ber_buffer_count = get_u32_le(in + 1);
        app->ber_bit_errors = 0;
        app->ber_bits_checked = 0;
        app->ber_packets_failed = 0;
        app->ber_current_buffer_errors = 0;
        app->ber_bytes_in_buffer = 0;
        app->ber_running = 1;
        return respond(out, out_cap, opcode, USB_STATUS_OK, NULL, 0u);

    case USB_CMD_BER_TEST_STOP:
        app->ber_running = 0;
        put_u32_le(payload + 0, app->ber_bit_errors);
        put_u32_le(payload + 4, app->ber_bits_checked);
        put_u32_le(payload + 8, app->ber_packets_failed);
        return respond(out, out_cap, opcode, USB_STATUS_OK, payload, 12u);

    case USB_CMD_STREAM_START:
        if (capture_arm(app->cap) != 0) {
            return respond(out, out_cap, opcode,
                           USB_STATUS_BAD_STATE, NULL, 0u);
        }
        return respond(out, out_cap, opcode, USB_STATUS_OK, NULL, 0u);

    case USB_CMD_STREAM_STOP:
        (void)capture_stop(app->cap);
        return respond(out, out_cap, opcode, USB_STATUS_OK, NULL, 0u);

    default:
        return respond(out, out_cap, opcode,
                       USB_STATUS_BAD_OPCODE, NULL, 0u);
    }
}
