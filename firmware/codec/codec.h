/*
 * codec.h - portable line/packet codecs for the photodiode LVDS receiver.
 *
 * Pure C99, no hardware or libc dependencies (the .c file does not call
 * any library function), so the same code builds for the host tests and
 * for the STM32H723 target.
 *
 * Contents:
 *   - 8b/10b encode/decode with running disparity (Widmer-Franaszek)
 *   - Manchester encode/decode (chip stream, plus a 2x-oversampled input)
 *   - PRBS-15 generator/checker (Miniscope Zero PER test mode)
 *   - Paper packet build/parse (11-word header + 5032-byte payload)
 */
#ifndef CODEC_H
#define CODEC_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ------------------------------------------------------------------ */
/* 8b/10b                                                              */
/*                                                                     */
/* Bit order convention (documented, used consistently everywhere):    */
/* the returned 10-bit symbol stores the first transmitted bit 'a' in  */
/* bit 9 (MSB) and the last transmitted bit 'j' in bit 0, i.e. the     */
/* symbol value reads exactly like the written code group              */
/* "abcdei fghj" interpreted as a binary number.                       */
/* Example: K28.5 at RD- is 001111 1010b = 0x0FA; at RD+ it is         */
/* 110000 0101b = 0x305.                                               */
/*                                                                     */
/* Running disparity is represented as an int: -1 (RD-) or +1 (RD+).   */
/* ------------------------------------------------------------------ */

#define CODEC_RD_NEG (-1)
#define CODEC_RD_POS (+1)

/* Error flags returned OR-ed by the 8b/10b decoder. */
#define CODEC_8B10B_ERR_CODE       0x01u /* code group not in the table   */
#define CODEC_8B10B_ERR_DISPARITY  0x02u /* legal code, wrong RD context  */

typedef struct {
    uint8_t  value;       /* decoded byte (0xBC for K28.5)               */
    uint8_t  is_control;  /* 1 for K symbols (only K28.x decoded here)   */
    uint8_t  errors;      /* CODEC_8B10B_ERR_* bitmask                   */
    int      rd_out;      /* running disparity after this symbol         */
} codec_8b10b_decoded_t;

/* Encode one data byte. *rd is updated in place.
 * Returns the 10-bit symbol. */
uint16_t codec_8b10b_encode(uint8_t byte, int *rd);

/* Encode K28.5 (comma). *rd is updated in place.
 * Returns 0x0FA (RD was -1) or 0x305 (RD was +1). */
uint16_t codec_8b10b_encode_k28_5(int *rd);

/* The byte value conventionally associated with K28.5. */
#define CODEC_K28_5_BYTE 0xBCu

/* Decode one 10-bit symbol against the incoming running disparity rd_in.
 * Invalid code groups set CODEC_8B10B_ERR_CODE and value/is_control are 0.
 * Only K28.5 is guaranteed as a control decode; other K28.y symbols are
 * decoded on a best-effort basis with is_control=1 (see codec.c). */
codec_8b10b_decoded_t codec_8b10b_decode(uint16_t symbol, int rd_in);

/* ------------------------------------------------------------------ */
/* Manchester                                                          */
/*                                                                     */
/* Convention (IEEE 802.3 style): data bit 1 -> chips "10" (high then  */
/* low), data bit 0 -> chips "01" (low then high). Bits are sent MSB   */
/* first. codec_manchester_encode() returns 16 chips in a uint16_t     */
/* whose MSB is the first chip transmitted.                            */
/* ------------------------------------------------------------------ */

uint16_t codec_manchester_encode(uint8_t byte);

typedef struct {
    uint8_t  bit_count;    /* bits collected for the byte in progress   */
    uint8_t  shift;        /* bits collected so far, MSB first          */
    uint8_t  have_chip;    /* 1 when the first chip of a pair is stored */
    uint8_t  first_chip;   /* stored first chip of the current pair     */
    uint32_t pair_errors;  /* invalid pairs (00 / 11) seen              */
    uint32_t bytes_out;    /* complete bytes emitted                    */
} codec_manchester_dec_t;

void codec_manchester_dec_init(codec_manchester_dec_t *dec);

/* Feed one chip (0 or 1; any nonzero value is treated as 1).
 * Returns 1 and stores the byte in *out when a byte completes,
 * 0 when more chips are needed, -1 when this chip completed an
 * invalid chip pair (00 or 11): the pair is dropped, pair_errors is
 * incremented, and the decoder resynchronises on the next pair. */
int codec_manchester_dec_feed_chip(codec_manchester_dec_t *dec,
                                   int chip, uint8_t *out);

/* 2x-oversampled input: the caller feeds raw samples at twice the chip
 * rate (4 samples per data bit). Each chip is decided by its second
 * sample (mid-chip sampling of the nominally phase-aligned stream);
 * a disagreement between the two samples of a chip increments
 * sample_disagreements but does not change the decision. */
typedef struct {
    codec_manchester_dec_t chip_dec;
    uint8_t  sample_phase;         /* 0 = first sample, 1 = second      */
    uint8_t  first_sample;         /* first sample of the current chip  */
    uint32_t sample_disagreements; /* samples within a chip that differ */
} codec_manchester_os_dec_t;

void codec_manchester_os_dec_init(codec_manchester_os_dec_t *dec);

/* Same return convention as codec_manchester_dec_feed_chip(). */
int codec_manchester_os_dec_feed_sample(codec_manchester_os_dec_t *dec,
                                        int sample, uint8_t *out);

/* ------------------------------------------------------------------ */
/* PRBS-15 - Miniscope Zero PER test mode                              */
/*                                                                     */
/* Polynomial x^15 + x^14 + 1. LFSR form used here (documented so a     */
/* host implementation can match it bit for bit): the 15-bit state     */
/* shifts left by one each step; the bit shifted in at position 0 is   */
/* state[14] XOR state[13] (before the shift); the output bit is the   */
/* outgoing state[14] (before the shift). Bytes are packed MSB first.  */
/* Period is 2^15 - 1 = 32767 bits (verified by the host test).        */
/*                                                                     */
/* PER mode reseeds per buffer: seed = (buffer_count & 0x7FFF) | 1,    */
/* and one buffer carries 40256 payload bits = 5032 bytes.             */
/* ------------------------------------------------------------------ */

#define CODEC_PRBS15_PAYLOAD_BYTES 5032u
#define CODEC_PRBS15_PAYLOAD_BITS  (CODEC_PRBS15_PAYLOAD_BYTES * 8u)

typedef struct {
    uint16_t state; /* 15-bit LFSR state, never 0 in normal operation */
} codec_prbs15_t;

uint16_t codec_prbs15_seed_for_buffer(uint32_t buffer_count);
void     codec_prbs15_init(codec_prbs15_t *p, uint16_t seed);
uint8_t  codec_prbs15_next_bit(codec_prbs15_t *p);
uint8_t  codec_prbs15_next_byte(codec_prbs15_t *p); /* 8 bits, MSB first */

/* Fill buf with the PRBS stream for buffer number buffer_count. */
void codec_prbs15_fill_buffer(uint8_t *buf, size_t len,
                              uint32_t buffer_count);

/* Compare buf against the regenerated stream for buffer_count.
 * Returns the exact number of differing bits. */
uint32_t codec_prbs15_count_errors(const uint8_t *buf, size_t len,
                                   uint32_t buffer_count);

/* Streaming checker: feed received bytes in order; the expected stream
 * is the one seeded for the buffer_count given at init. */
typedef struct {
    codec_prbs15_t gen;
    uint32_t       bit_errors;
    uint32_t       bits_checked;
} codec_prbs15_checker_t;

void codec_prbs15_checker_init(codec_prbs15_checker_t *c,
                               uint32_t buffer_count);
void codec_prbs15_checker_feed(codec_prbs15_checker_t *c,
                               const uint8_t *buf, size_t len);

/* ------------------------------------------------------------------ */
/* Paper packet                                                        */
/*                                                                     */
/* Wire format (all multi-byte fields little-endian, written/read with */
/* explicit shifts so host and target agree regardless of endianness):*/
/*                                                                     */
/*   offset 0   uint32  sync word 0xC0FFEE11 (project-specific sync    */
/*                      for THIS receiver; the paper itself uses a    */
/*                      fixed preamble + dummy words - this sync word  */
/*                      is ours, chosen and documented here)           */
/*   offset 4   uint32  header word 0: frame_index                     */
/*              uint32  header word 1: global_packet                   */
/*              uint32  header word 2: packet_in_frame                  */
/*              uint32  header word 3: timestamp                        */
/*              uint32  header word 4: pixel_count                      */
/*              uint32  header word 5: battery_raw                      */
/*              uint32  header word 6: vin_raw                          */
/*              uint32  header words 7..10: reserved (written as 0)     */
/*   offset 48  uint8[5032] payload                                    */
/*                                                                     */
/* Total wire size: 4 + 44 + 5032 = 5080 bytes. A 200x200 frame at     */
/* 8 bits/pixel is 8 packets, as in the paper.                         */
/* ------------------------------------------------------------------ */

#define CODEC_PACKET_SYNC        0xC0FFEE11u
#define CODEC_PACKET_HEADER_WORDS 11u
#define CODEC_PACKET_PAYLOAD_BYTES 5032u
#define CODEC_PACKET_WIRE_BYTES \
    (4u + CODEC_PACKET_HEADER_WORDS * 4u + CODEC_PACKET_PAYLOAD_BYTES)

typedef struct {
    uint32_t frame_index;
    uint32_t global_packet;
    uint32_t packet_in_frame;
    uint32_t timestamp;
    uint32_t pixel_count;
    uint32_t battery_raw;
    uint32_t vin_raw;
    uint32_t reserved[4];
} codec_packet_header_t;

/* Build a wire packet. Returns CODEC_PACKET_WIRE_BYTES on success,
 * 0 if out_cap is too small. */
size_t codec_packet_build(uint8_t *out, size_t out_cap,
                          const codec_packet_header_t *header,
                          const uint8_t *payload /* 5032 bytes */);

/* Parse a wire packet. Returns 0 on success, -1 on bad length,
 * -2 on bad sync word. payload_out may be NULL to parse header only. */
int codec_packet_parse(const uint8_t *in, size_t len,
                       codec_packet_header_t *header_out,
                       uint8_t *payload_out /* 5032 bytes or NULL */);

#ifdef __cplusplus
}
#endif

#endif /* CODEC_H */
