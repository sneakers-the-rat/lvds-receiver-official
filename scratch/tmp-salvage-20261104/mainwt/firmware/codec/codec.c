/*
 * codec.c - see codec.h for conventions. Pure C99, no library calls.
 */
#include "codec.h"

/* ================================================================== */
/* 8b/10b                                                              */
/*                                                                     */
/* Tables written from the standard Widmer-Franaszek code (the same   */
/* table published as the IBM 8b/10b code, e.g. in IEEE 802.3z).       */
/* Each entry is the RD- form of the code group, stored as a binary    */
/* number reading in transmission order (first bit = MSB of field).   */
/* The RD+ form of an unbalanced group is its bitwise complement;      */
/* balanced groups use the same form at both disparities, except the  */
/* two special balanced alternates D.07 (5b/6b) and D.x.3 (3b/4b),     */
/* which also swap form with RD while keeping disparity 0.             */
/* ================================================================== */

/* 5b/6b, indexed by the low 5 bits (EDCBA value 0..31), RD- form. */
static const uint8_t enc5_rdminus[32] = {
    0x27, /* D.00 100111 */  0x1D, /* D.01 011101 */
    0x2D, /* D.02 101101 */  0x31, /* D.03 110001 */
    0x35, /* D.04 110101 */  0x29, /* D.05 101001 */
    0x19, /* D.06 011001 */  0x38, /* D.07 111000 */
    0x39, /* D.08 111001 */  0x25, /* D.09 100101 */
    0x15, /* D.10 010101 */  0x34, /* D.11 110100 */
    0x0D, /* D.12 001101 */  0x2C, /* D.13 101100 */
    0x1C, /* D.14 011100 */  0x17, /* D.15 010111 */
    0x1B, /* D.16 011011 */  0x23, /* D.17 100011 */
    0x13, /* D.18 010011 */  0x32, /* D.19 110010 */
    0x0B, /* D.20 001011 */  0x2A, /* D.21 101010 */
    0x1A, /* D.22 011010 */  0x3A, /* D.23 111010 */
    0x33, /* D.24 110011 */  0x26, /* D.25 100110 */
    0x16, /* D.26 010110 */  0x36, /* D.27 110110 */
    0x0E, /* D.28 001110 */  0x2E, /* D.29 101110 */
    0x1E, /* D.30 011110 */  0x2B  /* D.31 101011 */
};

/* K.28 5b/6b group, RD- form 001111 (RD+ form 110000 is its complement). */
#define ENC5_K28_RDMINUS 0x0Fu

/* 3b/4b, indexed by the high 3 bits (HGF value 0..7), RD- form.
 * Index 7 is the primary form D.x.P7; the alternate D.x.A7 is used for
 * specific x values to avoid creating a comma by accident (see code). */
static const uint8_t enc4_rdminus[8] = {
    0xB, /* D.x.0 1011 */  0x9, /* D.x.1 1001 */
    0x5, /* D.x.2 0101 */  0xC, /* D.x.3 1100 */
    0xD, /* D.x.4 1101 */  0xA, /* D.x.5 1010 */
    0x6, /* D.x.6 0110 */  0xE  /* D.x.P7 1110 */
};
#define ENC4_A7_RDMINUS 0x7u /* D.x.A7 0111 (RD+ form 1000) */

static int popcount_u32(uint32_t v)
{
    int n = 0;
    while (v != 0u) {
        n += (int)(v & 1u);
        v >>= 1;
    }
    return n;
}

/* Disparity of an n-bit code: (#ones - #zeros), one of -2, 0, +2 here. */
static int code_disparity(uint32_t code, int bits)
{
    return 2 * popcount_u32(code) - bits;
}

static int rd_sign(int rd)
{
    return (rd >= 0) ? CODEC_RD_POS : CODEC_RD_NEG;
}

/* Encode the 5b/6b group. Updates *rd. form_rd, when the caller needs
 * it, is implicit in the returned code. */
static uint8_t encode6(uint8_t x, int *rd)
{
    uint8_t code = enc5_rdminus[x & 0x1Fu];
    int disp = code_disparity(code, 6);
    if (disp != 0 || x == 7u) {
        /* Unbalanced groups always take the form opposing current RD;
         * D.07 is balanced but still alternates form with RD. */
        if (rd_sign(*rd) > 0) {
            code = (uint8_t)(~code & 0x3Fu);
            disp = -disp;
        }
    }
    if (disp > 0) {
        *rd = CODEC_RD_POS;
    } else if (disp < 0) {
        *rd = CODEC_RD_NEG;
    }
    return code;
}

static uint8_t encode4_data(uint8_t x, uint8_t y, int *rd)
{
    uint8_t code;
    int disp;
    int use_a7 = 0;

    if (y == 7u) {
        /* D.x.A7 selection (standard rule): with RD- (the RD entering
         * this 4b group) for x = 17, 18, 20; with RD+ for x = 11, 13, 14. */
        if (rd_sign(*rd) < 0) {
            use_a7 = (x == 17u || x == 18u || x == 20u);
        } else {
            use_a7 = (x == 11u || x == 13u || x == 14u);
        }
    }
    code = use_a7 ? (uint8_t)ENC4_A7_RDMINUS : enc4_rdminus[y & 0x7u];
    disp = code_disparity(code, 4);
    if (y == 3u) {
        /* D.x.3 is balanced in both forms (1100 / 0011) and alternates. */
        if (rd_sign(*rd) > 0) {
            code = (uint8_t)(~code & 0xFu);
        }
    } else if (disp != 0) {
        if (rd_sign(*rd) > 0) {
            code = (uint8_t)(~code & 0xFu);
            disp = -disp;
        }
    }
    if (disp > 0) {
        *rd = CODEC_RD_POS;
    } else if (disp < 0) {
        *rd = CODEC_RD_NEG;
    }
    return code;
}

uint16_t codec_8b10b_encode(uint8_t byte, int *rd)
{
    uint8_t x = (uint8_t)(byte & 0x1Fu);
    uint8_t y = (uint8_t)((byte >> 5) & 0x7u);
    uint8_t c6 = encode6(x, rd);
    uint8_t c4 = encode4_data(x, y, rd);
    return (uint16_t)(((uint16_t)c6 << 4) | (uint16_t)c4);
}

uint16_t codec_8b10b_encode_k28_5(int *rd)
{
    uint16_t symbol;
    if (rd_sign(*rd) < 0) {
        symbol = 0x0FAu; /* 001111 1010 */
        *rd = CODEC_RD_POS;
    } else {
        symbol = 0x305u; /* 110000 0101 */
        *rd = CODEC_RD_NEG;
    }
    return symbol;
}

/* --- decoding helpers --- */

/* Classification of one received sub-block code.
 * form_rd: the RD context (-1/+1) in which an encoder emits this form,
 * or 0 when the form is emitted at either RD. */
typedef struct {
    int valid;
    int value;    /* 5-bit or 3-bit decoded value */
    int form_rd;
    int disp;     /* disparity of the received code */
} subblock_t;

static subblock_t decode6(uint8_t code, int *is_k28)
{
    subblock_t r;
    int i;
    r.valid = 0;
    r.value = 0;
    r.form_rd = 0;
    r.disp = code_disparity(code, 6);
    *is_k28 = 0;

    if (code == (uint8_t)ENC5_K28_RDMINUS) {        /* 001111, disp +2 */
        r.valid = 1; r.value = 28; r.form_rd = CODEC_RD_NEG;
        *is_k28 = 1;
        return r;
    }
    if (code == (uint8_t)(~ENC5_K28_RDMINUS & 0x3Fu)) { /* 110000, -2 */
        r.valid = 1; r.value = 28; r.form_rd = CODEC_RD_POS;
        *is_k28 = 1;
        return r;
    }
    for (i = 0; i < 32; i++) {
        uint8_t base = enc5_rdminus[i];
        int bdisp = code_disparity(base, 6);
        if (code == base) {
            r.valid = 1;
            r.value = i;
            /* The RD- base form is emitted at RD- when it is a +2 code
             * or the D.07 alternate; balanced singles at either RD. */
            r.form_rd = (bdisp > 0 || i == 7) ? CODEC_RD_NEG : 0;
            return r;
        }
        if ((bdisp != 0 || i == 7) &&
            code == (uint8_t)(~base & 0x3Fu)) {
            r.valid = 1;
            r.value = i;
            r.form_rd = CODEC_RD_POS;
            return r;
        }
    }
    return r;
}

static subblock_t decode4_data(uint8_t code)
{
    subblock_t r;
    r.valid = 1;
    r.value = 0;
    r.form_rd = 0;
    r.disp = code_disparity(code, 4);
    switch (code) {
    case 0xB: r.value = 0; r.form_rd = CODEC_RD_NEG; break; /* 1011 +2 */
    case 0x4: r.value = 0; r.form_rd = CODEC_RD_POS; break; /* 0100 -2 */
    case 0x9: r.value = 1; break;                           /* 1001  0 */
    case 0x5: r.value = 2; break;                           /* 0101  0 */
    case 0xC: r.value = 3; r.form_rd = CODEC_RD_NEG; break; /* 1100  0 */
    case 0x3: r.value = 3; r.form_rd = CODEC_RD_POS; break; /* 0011  0 */
    case 0xD: r.value = 4; r.form_rd = CODEC_RD_NEG; break; /* 1101 +2 */
    case 0x2: r.value = 4; r.form_rd = CODEC_RD_POS; break; /* 0010 -2 */
    case 0xA: r.value = 5; break;                           /* 1010  0 */
    case 0x6: r.value = 6; break;                           /* 0110  0 */
    case 0xE: r.value = 7; r.form_rd = CODEC_RD_NEG; break; /* P7 +2   */
    case 0x1: r.value = 7; r.form_rd = CODEC_RD_POS; break; /* P7 -2   */
    case 0x7: r.value = 7; r.form_rd = CODEC_RD_NEG; break; /* A7 +2   */
    case 0x8: r.value = 7; r.form_rd = CODEC_RD_POS; break; /* A7 -2   */
    default:  r.valid = 0; break;              /* 0000 and 1111 unused */
    }
    return r;
}

codec_8b10b_decoded_t codec_8b10b_decode(uint16_t symbol, int rd_in)
{
    codec_8b10b_decoded_t out;
    uint8_t c6 = (uint8_t)((symbol >> 4) & 0x3Fu);
    uint8_t c4 = (uint8_t)(symbol & 0xFu);
    int is_k28 = 0;
    subblock_t s6 = decode6(c6, &is_k28);
    subblock_t s4;
    int rd = rd_sign(rd_in);
    int rd_mid;

    out.value = 0;
    out.is_control = 0;
    out.errors = 0;
    out.rd_out = rd;

    if (!s6.valid) {
        out.errors |= CODEC_8B10B_ERR_CODE;
        return out;
    }
    if (s6.form_rd != 0 && s6.form_rd != rd) {
        out.errors |= CODEC_8B10B_ERR_DISPARITY;
    }
    rd_mid = (s6.disp > 0) ? CODEC_RD_POS
           : (s6.disp < 0) ? CODEC_RD_NEG : rd;

    if (is_k28 && (c4 == 0xAu || c4 == 0x5u)) {
        /* K28.5: the 4b group is 1010 (overall RD-) or 0101 (RD+),
         * both balanced, emitted at either mid-symbol RD. */
        out.value = CODEC_K28_5_BYTE;
        out.is_control = 1;
        out.rd_out = rd_mid; /* 4b disparity is 0 */
        return out;
    }

    s4 = decode4_data(c4);
    if (!s4.valid) {
        out.errors |= CODEC_8B10B_ERR_CODE;
        out.rd_out = rd_mid;
        return out;
    }
    if (s4.form_rd != 0 && s4.form_rd != rd_mid) {
        out.errors |= CODEC_8B10B_ERR_DISPARITY;
    }
    out.rd_out = (s4.disp > 0) ? CODEC_RD_POS
               : (s4.disp < 0) ? CODEC_RD_NEG : rd_mid;
    out.value = (uint8_t)(((uint8_t)s4.value << 5) | (uint8_t)s6.value);
    out.is_control = is_k28 ? 1u : 0u;
    return out;
}

/* ================================================================== */
/* Manchester                                                          */
/* ================================================================== */

uint16_t codec_manchester_encode(uint8_t byte)
{
    uint16_t chips = 0;
    int i;
    for (i = 0; i < 8; i++) {
        int bit = (byte >> (7 - i)) & 1;
        /* bit 1 -> chips 10b, bit 0 -> chips 01b; first pair at the top */
        uint16_t pair = bit ? 0x2u : 0x1u;
        chips = (uint16_t)(chips |
                            (uint16_t)(pair << (14 - 2 * i)));
    }
    return chips;
}

void codec_manchester_dec_init(codec_manchester_dec_t *dec)
{
    dec->bit_count = 0;
    dec->shift = 0;
    dec->have_chip = 0;
    dec->first_chip = 0;
    dec->pair_errors = 0;
    dec->bytes_out = 0;
}

int codec_manchester_dec_feed_chip(codec_manchester_dec_t *dec,
                                   int chip, uint8_t *out)
{
    int bit;
    if (!dec->have_chip) {
        dec->first_chip = chip ? 1u : 0u;
        dec->have_chip = 1;
        return 0;
    }
    dec->have_chip = 0;
    if (dec->first_chip == 1u && !chip) {
        bit = 1;
    } else if (dec->first_chip == 0u && chip) {
        bit = 0;
    } else {
        dec->pair_errors++;
        return -1;
    }
    dec->shift = (uint8_t)((dec->shift << 1) | (uint8_t)bit);
    dec->bit_count++;
    if (dec->bit_count == 8u) {
        dec->bit_count = 0;
        dec->bytes_out++;
        if (out != NULL) {
            *out = dec->shift;
        }
        dec->shift = 0;
        return 1;
    }
    return 0;
}

void codec_manchester_os_dec_init(codec_manchester_os_dec_t *dec)
{
    codec_manchester_dec_init(&dec->chip_dec);
    dec->sample_phase = 0;
    dec->first_sample = 0;
    dec->sample_disagreements = 0;
}

int codec_manchester_os_dec_feed_sample(codec_manchester_os_dec_t *dec,
                                        int sample, uint8_t *out)
{
    if (dec->sample_phase == 0u) {
        dec->first_sample = sample ? 1u : 0u;
        dec->sample_phase = 1;
        return 0;
    }
    dec->sample_phase = 0;
    if ((sample ? 1 : 0) != (int)dec->first_sample) {
        dec->sample_disagreements++;
    }
    /* Mid-chip decision: the second sample of the chip. */
    return codec_manchester_dec_feed_chip(&dec->chip_dec, sample, out);
}

/* ================================================================== */
/* PRBS-15                                                             */
/* ================================================================== */

uint16_t codec_prbs15_seed_for_buffer(uint32_t buffer_count)
{
    return (uint16_t)((buffer_count & 0x7FFFu) | 1u);
}

void codec_prbs15_init(codec_prbs15_t *p, uint16_t seed)
{
    p->state = (uint16_t)(seed & 0x7FFFu);
    if (p->state == 0u) {
        p->state = 1u; /* the all-zero state is a lock-up state */
    }
}

uint8_t codec_prbs15_next_bit(codec_prbs15_t *p)
{
    uint16_t s = (uint16_t)(p->state & 0x7FFFu);
    uint8_t out = (uint8_t)((s >> 14) & 1u);
    uint16_t fb = (uint16_t)(((s >> 14) ^ (s >> 13)) & 1u);
    p->state = (uint16_t)(((uint16_t)(s << 1) & 0x7FFFu) | fb);
    return out;
}

uint8_t codec_prbs15_next_byte(codec_prbs15_t *p)
{
    uint8_t v = 0;
    int i;
    for (i = 0; i < 8; i++) {
        v = (uint8_t)((v << 1) | codec_prbs15_next_bit(p));
    }
    return v;
}

void codec_prbs15_fill_buffer(uint8_t *buf, size_t len,
                              uint32_t buffer_count)
{
    codec_prbs15_t p;
    size_t i;
    codec_prbs15_init(&p, codec_prbs15_seed_for_buffer(buffer_count));
    for (i = 0; i < len; i++) {
        buf[i] = codec_prbs15_next_byte(&p);
    }
}

uint32_t codec_prbs15_count_errors(const uint8_t *buf, size_t len,
                                   uint32_t buffer_count)
{
    codec_prbs15_t p;
    uint32_t errors = 0;
    size_t i;
    codec_prbs15_init(&p, codec_prbs15_seed_for_buffer(buffer_count));
    for (i = 0; i < len; i++) {
        uint8_t diff = (uint8_t)(buf[i] ^ codec_prbs15_next_byte(&p));
        errors += (uint32_t)popcount_u32(diff);
    }
    return errors;
}

void codec_prbs15_checker_init(codec_prbs15_checker_t *c,
                               uint32_t buffer_count)
{
    codec_prbs15_init(&c->gen,
                      codec_prbs15_seed_for_buffer(buffer_count));
    c->bit_errors = 0;
    c->bits_checked = 0;
}

void codec_prbs15_checker_feed(codec_prbs15_checker_t *c,
                               const uint8_t *buf, size_t len)
{
    size_t i;
    for (i = 0; i < len; i++) {
        uint8_t diff = (uint8_t)(buf[i] ^ codec_prbs15_next_byte(&c->gen));
        c->bit_errors += (uint32_t)popcount_u32(diff);
        c->bits_checked += 8u;
    }
}

/* ================================================================== */
/* Paper packet                                                        */
/* ================================================================== */

static void put_u32_le(uint8_t *dst, uint32_t v)
{
    dst[0] = (uint8_t)(v & 0xFFu);
    dst[1] = (uint8_t)((v >> 8) & 0xFFu);
    dst[2] = (uint8_t)((v >> 16) & 0xFFu);
    dst[3] = (uint8_t)((v >> 24) & 0xFFu);
}

static uint32_t get_u32_le(const uint8_t *src)
{
    return (uint32_t)src[0]
         | ((uint32_t)src[1] << 8)
         | ((uint32_t)src[2] << 16)
         | ((uint32_t)src[3] << 24);
}

size_t codec_packet_build(uint8_t *out, size_t out_cap,
                          const codec_packet_header_t *header,
                          const uint8_t *payload)
{
    uint32_t words[CODEC_PACKET_HEADER_WORDS];
    size_t i;
    if (out_cap < CODEC_PACKET_WIRE_BYTES) {
        return 0;
    }
    words[0] = header->frame_index;
    words[1] = header->global_packet;
    words[2] = header->packet_in_frame;
    words[3] = header->timestamp;
    words[4] = header->pixel_count;
    words[5] = header->battery_raw;
    words[6] = header->vin_raw;
    for (i = 0; i < 4u; i++) {
        words[7u + i] = header->reserved[i];
    }
    put_u32_le(out, CODEC_PACKET_SYNC);
    for (i = 0; i < CODEC_PACKET_HEADER_WORDS; i++) {
        put_u32_le(out + 4u + 4u * i, words[i]);
    }
    for (i = 0; i < CODEC_PACKET_PAYLOAD_BYTES; i++) {
        out[48u + i] = payload[i];
    }
    return CODEC_PACKET_WIRE_BYTES;
}

int codec_packet_parse(const uint8_t *in, size_t len,
                       codec_packet_header_t *header_out,
                       uint8_t *payload_out)
{
    uint32_t words[CODEC_PACKET_HEADER_WORDS];
    size_t i;
    if (len < CODEC_PACKET_WIRE_BYTES) {
        return -1;
    }
    if (get_u32_le(in) != CODEC_PACKET_SYNC) {
        return -2;
    }
    for (i = 0; i < CODEC_PACKET_HEADER_WORDS; i++) {
        words[i] = get_u32_le(in + 4u + 4u * i);
    }
    if (header_out != NULL) {
        header_out->frame_index = words[0];
        header_out->global_packet = words[1];
        header_out->packet_in_frame = words[2];
        header_out->timestamp = words[3];
        header_out->pixel_count = words[4];
        header_out->battery_raw = words[5];
        header_out->vin_raw = words[6];
        for (i = 0; i < 4u; i++) {
            header_out->reserved[i] = words[7u + i];
        }
    }
    if (payload_out != NULL) {
        for (i = 0; i < CODEC_PACKET_PAYLOAD_BYTES; i++) {
            payload_out[i] = in[48u + i];
        }
    }
    return 0;
}
