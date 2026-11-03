"""
test_codec.py -- tests for host/codec.py.

Runnable two ways:
    python3 host/test_codec.py      (plain asserts, prints PASS lines)
    pytest  host/test_codec.py      (the same checks as test_* functions)

Standard library only.
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import codec as c


# ---------------------------------------------------------------- 8b/10b --

def test_exhaustive_round_trip_both_rd():
    """All 256 data bytes x both starting RDs: encode -> decode is the
    identity, with no error flags, and encoder/decoder RDs agree."""
    for rd0 in (-1, 1):
        for byte in range(256):
            enc = c.Encoder8b10b(rd0)
            code = enc.encode_symbol(byte)
            assert enc.rd in (-1, 1)
            dec = c.Decoder8b10b(rd0)
            out = dec.decode(code)
            assert out == (byte, False, False, False), \
                (rd0, byte, format(code, "010b"), out)
            assert dec.rd == enc.rd


def test_all_k_codes_both_rd():
    """All 12 supported K codes x both starting RDs round-trip."""
    assert len(c.CONTROL_BYTES) == 12
    for byte in c.CONTROL_BYTES.values():
        for rd0 in (-1, 1):
            enc = c.Encoder8b10b(rd0)
            code = enc.encode_symbol(byte, control=True)
            dec = c.Decoder8b10b(rd0)
            out = dec.decode(code)
            assert out == (byte, True, False, False), (byte, rd0, out)
            assert dec.rd == enc.rd
    # K28.5's two published forms, checked literally.
    assert format(c.Encoder8b10b(-1).encode_symbol(0xBC, True), "010b") \
        == "0011111010"
    assert format(c.Encoder8b10b(1).encode_symbol(0xBC, True), "010b") \
        == "1100000101"
    # A non-K byte requested as control must be refused.
    try:
        c.Encoder8b10b().encode_symbol(0x00, control=True)
    except ValueError:
        pass
    else:
        raise AssertionError("control encode of a data byte not refused")


def test_known_data_vectors():
    """Spot vectors taken from the published tables (not from this code):
    D0.0, D31.1 (the standard's worked example)."""
    assert format(c.Encoder8b10b(-1).encode_symbol(0x00), "010b") \
        == "1001110100"
    assert format(c.Encoder8b10b(1).encode_symbol(0x00), "010b") \
        == "0110001011"
    assert format(c.Encoder8b10b(-1).encode_symbol(0x3F), "010b") \
        == "1010111001"   # D31.1, RD=-1
    assert format(c.Encoder8b10b(1).encode_symbol(0x3F), "010b") \
        == "0101001001"   # D31.1, RD=+1


def test_disparity_invariant_long_stream():
    """Over a long mixed stream: RD stays in {-1,+1}, the cumulative
    (ones - zeros) at every symbol boundary stays in {-1,+1} (for a
    stream started at cumulative -1), the running disparity inside a
    symbol never exceeds +-2 in magnitude beyond its start, the max run
    of equal bits is <= 5, and the whole stream round-trips."""
    rng = random.Random(1234)
    data = bytes(rng.randrange(256) for _ in range(20000))
    for start_rd, start_cum in ((-1, -1), (1, 1)):
        enc, dec = c.Encoder8b10b(start_rd), c.Decoder8b10b(start_rd)
        cum, run, last = start_cum, 0, None
        max_run = 0
        for byte in data:
            code = enc.encode_symbol(byte)
            assert enc.rd in (-1, 1)
            for bit in c.code_to_bits(code):
                cum += 1 if bit else -1
                assert -3 <= cum <= 3  # bounded inside the symbol too
                run = run + 1 if bit == last else 1
                last = bit
                max_run = max(max_run, run)
            assert cum in (-1, 1), cum       # symbol-boundary invariant
            assert cum == enc.rd
            out = dec.decode(code)
            assert out == (byte, False, False, False)
        assert max_run <= 5, max_run


def test_code_and_disparity_errors():
    # All-zero and all-one words are not valid codes.
    for bad in (0b0000000000, 0b1111111111):
        byte, is_ctrl, ce, de = c.Decoder8b10b().decode(bad)
        assert ce, (bad, (byte, is_ctrl, ce, de))
    # A valid code sent against the wrong RD: D0.0 encoded at RD=+1 has
    # a -2 first sub-block, which a decoder sitting at RD=-1 must flag
    # as a disparity error (the byte itself still decodes).
    code = c.Encoder8b10b(1).encode_symbol(0x00)
    byte, is_ctrl, ce, de = c.Decoder8b10b(-1).decode(code)
    assert (byte, is_ctrl, ce) == (0x00, False, False)
    assert de


def test_comma_alignment_bit_shifted():
    """A stream beginning with K28.5, shifted by 0..9 filler bits, is
    found at exactly the shift and decodes back to the payload."""
    payload = b"Hello, 8b10b world!"
    for shift in range(10):
        enc = c.Encoder8b10b()
        bits = []
        for _ in range(2):
            bits += c.code_to_bits(enc.encode_symbol(c.K28_5, control=True))
        for b in payload:
            bits += c.code_to_bits(enc.encode_symbol(b))
        shifted = [0] * shift + bits
        assert c.find_comma(shifted) == shift, shift
        res = c.decode_bitstream(shifted)
        assert res.aligned and res.offset == shift, (shift, res.offset)
        assert res.data == payload, (shift, res.data)
        assert res.code_errors == 0 and res.disparity_errors == 0
        assert res.symbols[0][0] == c.K28_5 and res.symbols[0][1] is True


# -------------------------------------------------------------- Manchester --

def test_manchester_round_trip_random():
    rng = random.Random(99)
    bits = [rng.randrange(2) for _ in range(10000)]
    chips = c.manchester_encode_bits(bits)
    assert len(chips) == 20000
    # Our stated convention, checked literally: 1 -> (1,0), 0 -> (0,1).
    assert c.manchester_encode_bits([1, 0]) == [1, 0, 0, 1]
    assert c.manchester_decode(chips) == bits
    data = bytes(rng.randrange(256) for _ in range(1024))
    assert c.manchester_decode_bytes(c.manchester_encode_bytes(data)) == data


def test_manchester_invalid_pairs():
    bits, errors = c.manchester_decode_with_errors([0, 0, 1, 1, 1, 0])
    assert errors == 2
    assert bits == [0, 1, 1]  # invalid pairs take the first chip's value
    try:
        c.manchester_decode([0, 0])
    except c.ManchesterError:
        pass
    else:
        raise AssertionError("strict decode accepted an invalid pair")


# ------------------------------------------------------------------ PRBS --

def test_prbs_determinism_and_seed_rule():
    p1 = c.prbs15_payload(7)
    assert p1 == c.prbs15_payload(7)             # deterministic
    assert len(p1) == 5032                        # default size
    assert p1 != c.prbs15_payload(8)
    # Seed rule, including the wraparound: seed = (count mod 32768) | 1.
    assert c.prbs15_seed(0) == 1
    assert c.prbs15_seed(2) == 3
    assert c.prbs15_seed(32767) == 32767
    assert c.prbs15_seed(32768) == 1
    assert c.prbs15_payload(32768) == c.prbs15_payload(0)
    assert c.prbs15_payload(32769) == c.prbs15_payload(1)
    assert c.prbs15_payload(5, 16) == c.prbs15_payload(5, 16)
    assert len(c.prbs15_payload(5, 16)) == 16
    # LFSR period is the full 2^15 - 1 (primitive polynomial).
    g = c.PRBS15(0)
    start = g.state
    steps = 0
    while True:
        g.next_bit()
        steps += 1
        if g.state == start:
            break
    assert steps == 32767, steps


def test_prbs_checker_counts_injected_errors():
    checker = c.PRBS15Checker()
    payload = bytearray(c.prbs15_payload(5))
    assert checker.bit_errors(bytes(payload), 5) == 0
    # Flip exactly N distinct bits, for several N.
    rng = random.Random(7)
    positions = rng.sample(range(len(payload) * 8), 1000)
    for n in (1, 17, 100, 1000):
        mod = bytearray(c.prbs15_payload(5))
        for pos in positions[:n]:
            mod[pos // 8] ^= 1 << (7 - (pos % 8))
        got = checker.bit_errors(bytes(mod), 5)
        assert got == n, (n, got)
        assert checker.packet_failed(bytes(mod), 5)
    assert not checker.packet_failed(c.prbs15_payload(5), 5)


# ----------------------------------------------------------------- packet --

def test_packet_build_and_parse():
    payload = c.prbs15_payload(3)
    pkt = c.build_packet(frame_idx=42, global_pkt=1000, pkt_in_frame=3,
                         timestamp=0xDEADBEEF, pixel_count=40000,
                         batt_raw=3700, vin_raw=5000, payload5032=payload)
    assert len(pkt) == c.PACKET_SIZE == 5096
    assert pkt[:16] == b"\x00" * 16                       # dummy words
    assert pkt[16:20] == c.SYNC_WORD.to_bytes(4, "little")
    assert c.SYNC_WORD == 0xC0FFEE11
    # Two packets behind garbage, parsed back exactly.
    pkt2 = c.build_packet(43, 1001, 4, 0xDEADBEF0, 40000, 3690, 4990,
                          c.prbs15_payload(4))
    found = c.parse_packets(b"\xDE\xAD\xBE" + pkt + pkt2)
    assert len(found) == 2
    p = found[0]
    assert (p.frame_idx, p.global_pkt, p.pkt_in_frame, p.timestamp,
            p.pixel_count, p.batt_raw, p.vin_raw) == \
        (42, 1000, 3, 0xDEADBEEF, 40000, 3700, 5000)
    assert p.payload == payload and p.reserved == (0, 0, 0, 0)
    assert p.offset == 3 + 16
    assert found[1].global_pkt == 1001
    assert found[1].payload == c.prbs15_payload(4)
    # Bit-list input (packed MSB-first) parses the same.
    assert c.parse_packets(c.bytes_to_bits(pkt))[0].frame_idx == 42
    # A sync pattern inside the payload is not a false packet start.
    evil = bytearray(c.prbs15_payload(9))
    evil[100:104] = c.SYNC_WORD.to_bytes(4, "little")
    found = c.parse_packets(c.build_packet(1, 2, 0, 3, 4, 5, 6, bytes(evil)))
    assert len(found) == 1 and found[0].payload == bytes(evil)
    # Wrong payload length is rejected at build time.
    try:
        c.build_packet(0, 0, 0, 0, 0, 0, 0, b"too short")
    except ValueError:
        pass
    else:
        raise AssertionError("short payload not rejected")


# -------------------------------------------------------------------- main --

_TESTS = [v for k, v in sorted(globals().items())
          if k.startswith("test_") and callable(v)]

if __name__ == "__main__":
    for t in _TESTS:
        t()
        print(f"PASS {t.__name__}")
    print(f"PASS: all {len(_TESTS)} codec tests passed")
