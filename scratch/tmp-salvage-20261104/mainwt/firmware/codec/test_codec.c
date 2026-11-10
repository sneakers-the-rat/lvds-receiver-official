/*
 * test_codec.c - host tests for the codec library. No test framework:
 * each check prints a PASS line, failures print FAIL and make main
 * return nonzero.
 */
#include <stdio.h>
#include <string.h>

#include "codec.h"

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

/* Exhaustive 8b/10b round trip: every byte, from both starting RDs,
 * and a 4096-symbol chained stream where RD threads through (which is
 * how the code is actually used, and exercises the A7 alternates). */
static void test_8b10b(void)
{
    int ok = 1;
    int start_rd;
    int v;

    for (start_rd = -1; start_rd <= 1 && ok; start_rd += 2) {
        for (v = 0; v < 256; v++) {
            int rd = start_rd;
            uint16_t sym = codec_8b10b_encode((uint8_t)v, &rd);
            codec_8b10b_decoded_t d = codec_8b10b_decode(sym, start_rd);
            if (d.value != (uint8_t)v || d.is_control ||
                d.errors != 0u || d.rd_out != rd ||
                (rd != -1 && rd != 1) || sym > 0x3FFu) {
                printf("  byte 0x%02X start_rd %+d sym 0x%03X -> "
                       "val 0x%02X err 0x%X rd %+d (want %+d)\n",
                       v, start_rd, (unsigned)sym, d.value,
                       (unsigned)d.errors, d.rd_out, rd);
                ok = 0;
                break;
            }
        }
    }
    CHECK(ok, "8b10b exhaustive round trip 256 values x both RDs");

    {
        /* Chained stream: pseudo-random bytes, RD threaded through. */
        uint32_t lcg = 0x12345678u;
        int rd_enc = CODEC_RD_NEG;
        int rd_dec = CODEC_RD_NEG;
        int i;
        ok = 1;
        for (i = 0; i < 4096; i++) {
            uint8_t b;
            uint16_t sym;
            codec_8b10b_decoded_t d;
            lcg = lcg * 1664525u + 1013904223u;
            b = (uint8_t)(lcg >> 24);
            sym = codec_8b10b_encode(b, &rd_enc);
            d = codec_8b10b_decode(sym, rd_dec);
            rd_dec = d.rd_out;
            if (d.value != b || d.errors != 0u || rd_dec != rd_enc) {
                printf("  chained mismatch at %d byte 0x%02X\n", i, b);
                ok = 0;
                break;
            }
        }
        CHECK(ok, "8b10b chained RD stream round trip (4096 symbols)");
    }

    {
        /* A corrupted symbol must be flagged, not silently decoded:
         * 0x000 has code groups 000000 / 0000, neither in the table. */
        codec_8b10b_decoded_t d = codec_8b10b_decode(0x000u, CODEC_RD_NEG);
        CHECK((d.errors & CODEC_8B10B_ERR_CODE) != 0u,
              "8b10b invalid code group flagged");
    }
    {
        /* Disparity error: encode at RD- then decode claiming RD+. */
        int rd = CODEC_RD_NEG;
        uint16_t sym = codec_8b10b_encode(0x00u, &rd); /* D.00 has disp */
        codec_8b10b_decoded_t d = codec_8b10b_decode(sym, CODEC_RD_POS);
        CHECK(d.value == 0x00u &&
              (d.errors & CODEC_8B10B_ERR_DISPARITY) != 0u,
              "8b10b disparity error flagged");
    }
}

static void test_k28_5(void)
{
    int rd = CODEC_RD_NEG;
    uint16_t sym_neg = codec_8b10b_encode_k28_5(&rd);
    int rd_after_neg = rd;
    uint16_t sym_pos = codec_8b10b_encode_k28_5(&rd);
    codec_8b10b_decoded_t d1 = codec_8b10b_decode(sym_neg, CODEC_RD_NEG);
    codec_8b10b_decoded_t d2 = codec_8b10b_decode(sym_pos, CODEC_RD_POS);

    CHECK(sym_neg == 0x0FAu && rd_after_neg == CODEC_RD_POS,
          "K28.5 RD- symbol is 0x0FA and flips RD");
    CHECK(sym_pos == 0x305u && rd == CODEC_RD_NEG,
          "K28.5 RD+ symbol is 0x305 and flips RD");
    CHECK(d1.is_control && d1.value == CODEC_K28_5_BYTE &&
          d1.errors == 0u && d1.rd_out == CODEC_RD_POS &&
          d2.is_control && d2.value == CODEC_K28_5_BYTE &&
          d2.errors == 0u && d2.rd_out == CODEC_RD_NEG,
          "K28.5 decode round trip both RDs");

    {
        /* Comma property: read in wire order a..j, the symbol is
         * 0,0,1,1,1,1,1,0,1,0 - the run 0011111 across the 6b/4b
         * boundary is the comma a receiver hunts for to find symbol
         * alignment. */
        static const uint8_t wire[10] = {0, 0, 1, 1, 1, 1, 1, 0, 1, 0};
        int i;
        int match = 1;
        for (i = 0; i < 10; i++) {
            if ((uint8_t)((sym_neg >> (9 - i)) & 1u) != wire[i]) {
                match = 0;
            }
        }
        CHECK(match, "K28.5 comma sequence 0011111 present in wire order");
    }
}

static void test_manchester(void)
{
    int ok = 1;
    int v;
    for (v = 0; v < 256 && ok; v++) {
        uint16_t chips = codec_manchester_encode((uint8_t)v);
        codec_manchester_dec_t dec;
        uint8_t out = 0;
        int got = 0;
        int i;
        codec_manchester_dec_init(&dec);
        for (i = 0; i < 16; i++) {
            int chip = (chips >> (15 - i)) & 1;
            int r = codec_manchester_dec_feed_chip(&dec, chip, &out);
            if (r == 1) {
                got = 1;
            } else if (r != 0) {
                ok = 0;
            }
        }
        if (!got || out != (uint8_t)v || dec.pair_errors != 0u) {
            ok = 0;
        }
    }
    CHECK(ok, "Manchester round trip 256 values (chip stream)");

    {
        /* Convention spot checks: 0x80 = 1000 0000b MSB first ->
         * pairs 10 01 01 01 01 01 01 01 = 0x9555; 0x00 -> 0x5555. */
        CHECK(codec_manchester_encode(0x80u) == 0x9555u &&
              codec_manchester_encode(0x00u) == 0x5555u &&
              codec_manchester_encode(0xFFu) == 0xAAAAu,
              "Manchester known patterns 0x80/0x00/0xFF");
    }
    {
        /* Invalid pair (00) is reported and counted. */
        codec_manchester_dec_t dec;
        uint8_t out = 0;
        int r0, r1;
        codec_manchester_dec_init(&dec);
        r0 = codec_manchester_dec_feed_chip(&dec, 0, &out);
        r1 = codec_manchester_dec_feed_chip(&dec, 0, &out);
        CHECK(r0 == 0 && r1 == -1 && dec.pair_errors == 1u,
              "Manchester invalid pair 00 flagged and counted");
    }
    {
        /* 2x-oversampled API: duplicate every chip, decode 256 values. */
        int ok2 = 1;
        for (v = 0; v < 256 && ok2; v++) {
            uint16_t chips = codec_manchester_encode((uint8_t)v);
            codec_manchester_os_dec_t dec;
            uint8_t out = 0;
            int got = 0;
            int i;
            codec_manchester_os_dec_init(&dec);
            for (i = 0; i < 16; i++) {
                int chip = (chips >> (15 - i)) & 1;
                int s;
                for (s = 0; s < 2; s++) {
                    int r = codec_manchester_os_dec_feed_sample(
                        &dec, chip, &out);
                    if (r == 1) {
                        got = 1;
                    } else if (r < 0) {
                        ok2 = 0;
                    }
                }
            }
            if (!got || out != (uint8_t)v ||
                dec.sample_disagreements != 0u) {
                ok2 = 0;
            }
        }
        CHECK(ok2, "Manchester round trip via 2x oversampled input");
    }
}

static void test_prbs(void)
{
    static uint8_t buf[CODEC_PRBS15_PAYLOAD_BYTES];
    static uint8_t want[CODEC_PRBS15_PAYLOAD_BYTES];

    codec_prbs15_fill_buffer(buf, sizeof buf, 0u);
    codec_prbs15_fill_buffer(want, sizeof want, 0u);
    CHECK(memcmp(buf, want, sizeof buf) == 0 &&
          codec_prbs15_count_errors(buf, sizeof buf, 0u) == 0u,
          "PRBS-15 self-check: regenerated buffer matches (buffer 0)");
    CHECK(codec_prbs15_count_errors(buf, sizeof buf, 7u) > 1000u,
          "PRBS-15 wrong buffer_count does not match (reseed matters)");

    {
        /* Seed rule, taken from the paper's PER mode. */
        CHECK(codec_prbs15_seed_for_buffer(0u) == 1u &&
              codec_prbs15_seed_for_buffer(1u) == 1u &&
              codec_prbs15_seed_for_buffer(2u) == 3u &&
              codec_prbs15_seed_for_buffer(0x8001u) == 1u &&
              codec_prbs15_seed_for_buffer(0xFFFEu) == 0x7FFFu,
              "PRBS-15 seed = (buffer_count & 0x7FFF) | 1");
    }
    {
        /* Injected errors: flip exactly 5 known bits, expect exactly 5. */
        buf[0] ^= 0x01u;
        buf[100] ^= 0x80u;
        buf[2515] ^= 0x18u; /* two bits */
        buf[5031] ^= 0x40u;
        CHECK(codec_prbs15_count_errors(buf, sizeof buf, 0u) == 5u,
              "PRBS-15 injected-error count is exact (5 bits)");
    }
    {
        /* Streaming checker agrees with the one-shot counter, and the
         * full payload is 40256 bits as the paper specifies. */
        codec_prbs15_checker_t chk;
        codec_prbs15_checker_init(&chk, 0u);
        codec_prbs15_checker_feed(&chk, buf, 2000u);
        codec_prbs15_checker_feed(&chk, buf + 2000,
                                  sizeof buf - 2000u);
        CHECK(chk.bit_errors == 5u &&
              chk.bits_checked == CODEC_PRBS15_PAYLOAD_BITS &&
              CODEC_PRBS15_PAYLOAD_BITS == 40256u,
              "PRBS-15 streaming checker: 5 errors over 40256 bits");
    }
    {
        /* Period: state returns to the seed after 32767 bits and the
         * state is never 0 along the way. */
        codec_prbs15_t p;
        uint32_t i;
        int okp = 1;
        codec_prbs15_init(&p, 1u);
        for (i = 0; i < 32767u; i++) {
            (void)codec_prbs15_next_bit(&p);
            if (p.state == 0u) {
                okp = 0;
            }
            if (i + 1u < 32767u && p.state == 1u) {
                okp = 0; /* returned early: period shorter than 32767 */
            }
        }
        CHECK(okp && p.state == 1u,
              "PRBS-15 period is exactly 32767 bits from seed 1");
    }
}

static void test_packet(void)
{
    static uint8_t wire[CODEC_PACKET_WIRE_BYTES];
    static uint8_t payload[CODEC_PACKET_PAYLOAD_BYTES];
    static uint8_t payload_out[CODEC_PACKET_PAYLOAD_BYTES];
    codec_packet_header_t h;
    codec_packet_header_t h_out;
    size_t i;
    size_t n;

    memset(&h, 0, sizeof h);
    h.frame_index = 0x11223344u;
    h.global_packet = 0x55667788u;
    h.packet_in_frame = 7u;
    h.timestamp = 0xAABBCCDDu;
    h.pixel_count = 40000u;
    h.battery_raw = 0x0B0Cu;
    h.vin_raw = 0x0D0Eu;
    for (i = 0; i < sizeof payload; i++) {
        payload[i] = (uint8_t)(i * 31u + 7u);
    }

    n = codec_packet_build(wire, sizeof wire, &h, payload);
    CHECK(n == CODEC_PACKET_WIRE_BYTES &&
          CODEC_PACKET_WIRE_BYTES == 5080u,
          "packet build: wire size 5080 bytes");
    CHECK(wire[0] == 0x11u && wire[1] == 0xEEu &&
          wire[2] == 0xFFu && wire[3] == 0xC0u,
          "packet build: sync 0xC0FFEE11 stored little-endian");
    CHECK(wire[4] == 0x44u && wire[5] == 0x33u &&
          wire[6] == 0x22u && wire[7] == 0x11u,
          "packet build: header word 0 is frame_index, little-endian");

    memset(&h_out, 0, sizeof h_out);
    memset(payload_out, 0, sizeof payload_out);
    CHECK(codec_packet_parse(wire, n, &h_out, payload_out) == 0 &&
          memcmp(&h, &h_out, sizeof h) == 0 &&
          memcmp(payload, payload_out, sizeof payload) == 0,
          "packet build/parse round trip (header + 5032B payload)");

    wire[0] ^= 0xFFu;
    CHECK(codec_packet_parse(wire, n, &h_out, payload_out) == -2,
          "packet parse: bad sync rejected (-2)");
    wire[0] ^= 0xFFu;
    CHECK(codec_packet_parse(wire, n - 1u, &h_out, payload_out) == -1,
          "packet parse: short buffer rejected (-1)");
    CHECK(codec_packet_build(wire, 100u, &h, payload) == 0u,
          "packet build: undersized output rejected (0)");
}

int main(void)
{
    test_8b10b();
    test_k28_5();
    test_manchester();
    test_prbs();
    test_packet();
    if (failures != 0) {
        printf("RESULT: %d FAILURE(S)\n", failures);
        return 1;
    }
    printf("RESULT: ALL TESTS PASSED\n");
    return 0;
}
