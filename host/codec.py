"""
codec.py -- line codes and packet framing for the photodiode LVDS receiver.

Implemented from the published coding rules (Widmer & Franaszek, IBM J. Res.
Dev. 27(5), 1983 -- the 8b/10b partitioned-block code), the Miniscope Zero
paper's PRBS-15 PER-test description, and this project's own packet layout.
No third-party codec code is used; the 5b/6b and 3b/4b tables below are the
standard's published tables, written out in full.

Conventions used throughout this file
--------------------------------------
* A 10-bit code is an ``int`` whose most-significant bit (bit 9) is ``a`` --
  the first bit transmitted -- and whose least-significant bit (bit 0) is
  ``j``, the last bit transmitted.  So the printed form of a code,
  e.g. K28.5 at RD=-1 is ``0011111010``, is exactly ``format(code, '010b')``,
  read left-to-right in transmission order ``abcdei fghj``.
* Running disparity (RD) is the int -1 or +1.  A fresh encoder/decoder
  starts at RD = -1, as the standard specifies.
* A byte is D.x.y with x = low 5 bits (EDCBA) and y = high 3 bits (HGF).

Manchester convention (READ THIS -- polarity is a choice, we state ours)
------------------------------------------------------------------------
THIS PROJECT:  data bit 1 -> chips (1, 0)   (high, then low: a falling
               mid-bit transition)
               data bit 0 -> chips (0, 1)   (low, then high: a rising
               mid-bit transition)
Chips are transmitted in the order written.  The decoder is the exact
inverse of the encoder under this one convention.
Note on naming: this polarity is the G. E. Thomas convention.  IEEE 802.3
assigns the opposite polarity (1 -> low-then-high).  Both are "Manchester";
they differ only in which chip order is called a 1, i.e. in an inversion of
the recovered data if mixed.  The task spec for this project explicitly
picked 1 -> (1, 0), so that is what is implemented, stated here so nobody
has to guess, and encoder/decoder are consistent with each other.

Packet framing (this project's own layout, NOT the paper's -- the paper
names the header fields and the 5032-byte payload but does not publish a
sync word)
---------------------------------------------------------------------------
    [4 x 32-bit dummy words, all zero]      (the paper's "dummy words")
    [1 x 32-bit sync word 0xC0FFEE11]       (OUR sync word, chosen for this
                                             project; it is not taken from
                                             any other protocol)
    [11 x 32-bit header words, little-endian, in this order:
        frame_idx, global_pkt, pkt_in_frame, timestamp, pixel_count,
        batt_raw, vin_raw, then 4 reserved words of zero]
    [5032-byte payload]
All 32-bit words are little-endian on the wire.  Total packet = 5096 bytes.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

# --------------------------------------------------------------------------
# 8b/10b -- sub-block tables
# --------------------------------------------------------------------------

def _b(s: str) -> int:
    return int(s, 2)


def _disp(code: int, nbits: int) -> int:
    """Disparity of a code word: (#ones - #zeros)."""
    return 2 * bin(code).count("1") - nbits


# 5b/6b table, RD=-1 column, as strings 'abcdei' in transmission order.
# The RD=+1 column is derived in _build_5b6b(): for every sub-block with
# non-zero disparity the RD=+1 form is the bitwise complement of the RD=-1
# form; for balanced (disparity-0) sub-blocks the two forms are identical,
# EXCEPT D.07, whose balanced RD=+1 form is also the complement (000111).
_5B6B_RD_MINUS = [
    "100111", "011101", "101101", "110001",  # D.00 .. D.03
    "110101", "101001", "011001", "111000",  # D.04 .. D.07
    "111001", "100101", "010101", "110100",  # D.08 .. D.11
    "001101", "101100", "011100", "010111",  # D.12 .. D.15
    "011011", "100011", "010011", "110010",  # D.16 .. D.19
    "001011", "101010", "011010", "111010",  # D.20 .. D.23
    "110011", "100110", "010110", "110110",  # D.24 .. D.27
    "001110", "101110", "011110", "101011",  # D.28 .. D.31
]
_K28_5B_RD_MINUS = "001111"  # 5b/6b code used only by K.28.y symbols


def _build_5b6b():
    table = []  # x -> (code_at_rd_minus, code_at_rd_plus)
    for x, s in enumerate(_5B6B_RD_MINUS):
        rd_minus = _b(s)
        if x == 7:
            rd_plus = rd_minus ^ 0b111111  # D.07 special balanced pair
        elif _disp(rd_minus, 6) != 0:
            rd_plus = rd_minus ^ 0b111111
        else:
            rd_plus = rd_minus
        table.append((rd_minus, rd_plus))
    return table


_5B6B = _build_5b6b()
_K28_5B = (_b(_K28_5B_RD_MINUS), _b(_K28_5B_RD_MINUS) ^ 0b111111)

# 3b/4b table for data, y -> (code_at_rd_minus, code_at_rd_plus), 'fghj'.
# D.x.3 is the balanced special pair (1100 / 0011); the rest follow the
# same complement-if-unbalanced rule as 5b/6b.
_3B4B_DATA_P7 = [  # primary D.x.7
    ("1011", "0100"), ("1001", "1001"), ("0101", "0101"), ("1100", "0011"),
    ("1101", "0010"), ("1010", "1010"), ("0110", "0110"), ("1110", "0001"),
]
_3B4B_DATA = [(_b(a), _b(c)) for a, c in _3B4B_DATA_P7]
_3B4B_A7 = (_b("0111"), _b("1000"))  # alternate D.x.7 (see encoder rule)

# D.x.A7 is used ONLY for these (x, RD-at-3b/4b-entry) combinations, to
# avoid creating a run of five equal bits (a false comma) across the
# 5b/6b -> 3b/4b boundary.  All of x = 11,13,14,17,18,20 have balanced
# 5b/6b codes, so RD at 3b/4b entry equals RD at symbol entry for them.
_A7_WHEN_RD_MINUS = frozenset({17, 18, 20})
_A7_WHEN_RD_PLUS = frozenset({11, 13, 14})

# The 12 control (K) symbols, written out in full as 10-bit codes
# (RD=-1 form, RD=+1 form).  Writing the composed codes directly avoids
# the extra K-specific 3b/4b variants (K.x.1/2/5/6/7 differ from D.x.y).
_K_CODES = {
    # byte: (name, rd_minus_code, rd_plus_code)
    0x1C: ("K28.0", _b("0011110100"), _b("1100001011")),
    0x3C: ("K28.1", _b("0011111001"), _b("1100000110")),
    0x5C: ("K28.2", _b("0011110101"), _b("1100001010")),
    0x7C: ("K28.3", _b("0011110011"), _b("1100001100")),
    0x9C: ("K28.4", _b("0011110010"), _b("1100001101")),
    0xBC: ("K28.5", _b("0011111010"), _b("1100000101")),
    0xDC: ("K28.6", _b("0011110110"), _b("1100001001")),
    0xFC: ("K28.7", _b("0011111000"), _b("1100000111")),
    0xF7: ("K23.7", _b("1110101000"), _b("0001010111")),
    0xFB: ("K27.7", _b("1101101000"), _b("0010010111")),
    0xFD: ("K29.7", _b("1011101000"), _b("0100010111")),
    0xFE: ("K30.7", _b("0111101000"), _b("1000010111")),
}
CONTROL_BYTES = {name: byte for byte, (name, _, _) in _K_CODES.items()}
K28_5 = 0xBC
K28_5_CODE_RD_MINUS = _K_CODES[K28_5][1]
K28_5_CODE_RD_PLUS = _K_CODES[K28_5][2]


def _check_rd(rd: int) -> int:
    if rd not in (-1, 1):
        raise ValueError(f"running disparity must be -1 or +1, got {rd!r}")
    return rd


def _encode_data_symbol(byte: int, rd: int):
    """Return (10-bit code, new_rd) for a data byte at the given RD."""
    x = byte & 0x1F
    y = (byte >> 5) & 0x07
    code6 = _5B6B[x][0 if rd < 0 else 1]
    d6 = _disp(code6, 6)
    rd_mid = rd if d6 == 0 else (1 if d6 > 0 else -1)
    if y == 7 and ((rd_mid < 0 and x in _A7_WHEN_RD_MINUS) or
                   (rd_mid > 0 and x in _A7_WHEN_RD_PLUS)):
        pair = _3B4B_A7
    else:
        pair = _3B4B_DATA[y]
    code4 = pair[0 if rd_mid < 0 else 1]
    d4 = _disp(code4, 4)
    rd_out = rd_mid if d4 == 0 else (1 if d4 > 0 else -1)
    return (code6 << 4) | code4, rd_out


class Encoder8b10b:
    """Stateful 8b/10b encoder.  ``rd`` is the current running disparity."""

    def __init__(self, rd: int = -1):
        self.rd = _check_rd(rd)

    def reset(self, rd: int = -1):
        self.rd = _check_rd(rd)

    def encode_symbol(self, byte: int, control: bool = False) -> int:
        if not 0 <= byte <= 0xFF:
            raise ValueError(f"byte out of range: {byte!r}")
        if control:
            if byte not in _K_CODES:
                raise ValueError(
                    f"0x{byte:02X} is not one of the 12 K symbols")
            _, rm, rp = _K_CODES[byte]
            code = rm if self.rd < 0 else rp
            d = _disp(code, 10)
            if d != 0:
                self.rd = 1 if d > 0 else -1
            return code
        code, self.rd = _encode_data_symbol(byte, self.rd)
        return code

    # Aliases -- same operation, friendlier names for call sites.
    def encode(self, byte: int, control: bool = False) -> int:
        return self.encode_symbol(byte, control)

    def encode_byte(self, byte: int) -> int:
        return self.encode_symbol(byte, False)

    def encode_k(self, byte: int) -> int:
        return self.encode_symbol(byte, True)

    def encode_bytes(self, data: bytes) -> list:
        return [self.encode_symbol(b) for b in data]

    def encode_to_bits(self, data: bytes) -> list:
        bits = []
        for code in self.encode_bytes(data):
            bits.extend(code_to_bits(code))
        return bits


def encode_8b10b(byte: int, rd: int = -1, control: bool = False):
    """One-shot encode.  Returns (code, new_rd)."""
    enc = Encoder8b10b(rd)
    code = enc.encode_symbol(byte, control)
    return code, enc.rd


def _build_decode_map():
    m = {}
    for byte in range(256):
        for rd0 in (-1, 1):
            code, _ = _encode_data_symbol(byte, rd0)
            prev = m.get(code)
            if prev is not None and prev != (byte, False):
                raise AssertionError(f"decode collision at {code:010b}")
            m[code] = (byte, False)
    for byte, (_, rm, rp) in _K_CODES.items():
        for code in (rm, rp):
            prev = m.get(code)
            if prev is not None and prev != (byte, True):
                raise AssertionError(f"K decode collision at {code:010b}")
            m[code] = (byte, True)
    return m


_DECODE_MAP = _build_decode_map()


class Decoder8b10b:
    """Stateful 8b/10b decoder.

    ``decode(code)`` returns
        (byte, is_control, code_error, disparity_error)

    * code_error: the 10-bit word is not any valid D or K code (this
      includes sub-blocks whose one-count is impossible: a 6b sub-block
      must have 2, 3 or 4 ones, a 4b sub-block 1, 2 or 3).
    * disparity_error: a sub-block's non-zero disparity points the wrong
      way for the running disparity entering that sub-block (a +2 sub-block
      received while RD=+1, or a -2 sub-block while RD=-1).  Balanced
      sub-blocks never raise it -- the D.07 / D.x.3 balanced pairs are
      legal at either RD.
    The decoder advances its RD from the *received* sub-block disparities
    (as hardware decoders do), even when an error flag is raised, and it
    still returns the looked-up byte when the code exists in the table.
    On a code_error the returned byte is 0 and is_control is False.
    """

    def __init__(self, rd: int = -1):
        self.rd = _check_rd(rd)

    def reset(self, rd: int = -1):
        self.rd = _check_rd(rd)

    def decode(self, code: int):
        if not 0 <= code <= 0x3FF:
            return (0, False, True, False)
        code6, code4 = code >> 4, code & 0x0F
        d6, d4 = _disp(code6, 6), _disp(code4, 4)
        code_error = not (2 <= bin(code6).count("1") <= 4) or \
            not (1 <= bin(code4).count("1") <= 3)
        disparity_error = False
        rd = self.rd
        if (rd < 0 and d6 < 0) or (rd > 0 and d6 > 0):
            disparity_error = True
        if d6 != 0:
            rd = 1 if d6 > 0 else -1
        if (rd < 0 and d4 < 0) or (rd > 0 and d4 > 0):
            disparity_error = True
        if d4 != 0:
            rd = 1 if d4 > 0 else -1
        self.rd = rd
        hit = _DECODE_MAP.get(code)
        if hit is None:
            return (0, False, True, disparity_error)
        byte, is_control = hit
        return (byte, is_control, code_error, disparity_error)

    def decode_codes(self, codes) -> list:
        return [self.decode(c) for c in codes]


def decode_8b10b(code: int, rd: int = -1):
    """One-shot decode.  Returns (byte, is_control, code_error,
    disparity_error, new_rd)."""
    dec = Decoder8b10b(rd)
    out = dec.decode(code)
    return (*out, dec.rd)


# --------------------------------------------------------------------------
# Bit-stream helpers and comma (K28.5) alignment
# --------------------------------------------------------------------------

def code_to_bits(code: int) -> list:
    """10 bits of a code, transmission order (a first, j last)."""
    return [(code >> s) & 1 for s in range(9, -1, -1)]


def bits_to_code(bits) -> int:
    if len(bits) != 10:
        raise ValueError("a code is exactly 10 bits")
    code = 0
    for bit in bits:
        code = (code << 1) | (int(bit) & 1)
    return code


def bytes_to_bits(data: bytes) -> list:
    bits = []
    for b in data:
        bits.extend((b >> s) & 1 for s in range(7, -1, -1))
    return bits


def bits_to_bytes(bits) -> bytes:
    if len(bits) % 8:
        raise ValueError("bit count must be a multiple of 8")
    out = bytearray()
    for i in range(0, len(bits), 8):
        v = 0
        for bit in bits[i:i + 8]:
            v = (v << 1) | (int(bit) & 1)
        out.append(v)
    return bytes(out)


_COMMA_CODES = (K28_5_CODE_RD_MINUS, K28_5_CODE_RD_PLUS)
# The 7-bit comma sequences proper: 0011111 (RD- form) and 1100000 (RD+).
_COMMA_7BIT = ("0011111", "1100000")


def find_comma(bits) -> int:
    """Return the bit offset of the first K28.5 in ``bits``, or -1.

    Primary search is for a whole 10-bit K28.5 code at some offset.  If no
    whole code survives (e.g. its 3b/4b tail was corrupted), fall back to
    the 7-bit comma sequence, whose position is the symbol start for both
    K28.5 forms (0011111... at RD=-1, 1100000... at RD=+1).
    """
    bits = [int(b) & 1 for b in bits]
    for off in range(0, len(bits) - 9):
        if bits_to_code(bits[off:off + 10]) in _COMMA_CODES:
            return off
    s = "".join(str(b) for b in bits)
    for pat in _COMMA_7BIT:
        idx = s.find(pat)
        if idx >= 0:
            return idx
    return -1


@dataclass
class StreamResult:
    symbols: list = field(default_factory=list)   # decoder tuples, in order
    data: bytes = b""        # data bytes only (control symbols removed)
    offset: int = -1         # bit offset where alignment was found
    code_errors: int = 0
    disparity_errors: int = 0
    aligned: bool = False


def decode_bitstream(bits, rd: int = -1) -> StreamResult:
    """Align on the first K28.5 comma, then decode 10-bit symbols.

    ``bits`` is any iterable of 0/1 in transmission order, at any bit
    offset.  Trailing bits that do not make a whole symbol are ignored.
    If no comma is found, returns a StreamResult with aligned=False.
    """
    bits = [int(b) & 1 for b in bits]
    off = find_comma(bits)
    if off < 0:
        return StreamResult(offset=-1, aligned=False)
    dec = Decoder8b10b(rd)
    symbols, data = [], bytearray()
    n_code_err = n_disp_err = 0
    for i in range(off, len(bits) - 9, 10):
        res = dec.decode(bits_to_code(bits[i:i + 10]))
        symbols.append(res)
        byte, is_control, ce, de = res
        n_code_err += bool(ce)
        n_disp_err += bool(de)
        if not is_control and not ce:
            data.append(byte)
    return StreamResult(symbols=symbols, data=bytes(data), offset=off,
                        code_errors=n_code_err, disparity_errors=n_disp_err,
                        aligned=True)


# Friendly aliases
decode_stream = decode_bitstream
align_and_decode = decode_bitstream
Codec8b10b = Encoder8b10b

# --------------------------------------------------------------------------
# Manchester (convention stated in the module docstring: 1 -> (1, 0))
# --------------------------------------------------------------------------

_CHIPS_FOR_BIT = {0: (0, 1), 1: (1, 0)}
_BIT_FOR_CHIPS = {(0, 1): 0, (1, 0): 1}


class ManchesterError(ValueError):
    pass


def manchester_encode_bits(bits) -> list:
    chips = []
    for bit in bits:
        chips.extend(_CHIPS_FOR_BIT[int(bit) & 1])
    return chips


def manchester_encode_bytes(data: bytes) -> list:
    return manchester_encode_bits(bytes_to_bits(data))


def manchester_decode_with_errors(chips):
    """Decode chip pairs.  Returns (bits, n_invalid_pairs).

    An invalid pair (0,0) or (1,1) is counted and its bit is taken from
    the first chip -- under our convention the first chip alone carries
    the bit value ((1, x) -> 1, (0, x) -> 0), so a single flipped second
    chip is corrected by this rule and a flipped first chip is not.
    """
    chips = [int(c) & 1 for c in chips]
    if len(chips) % 2:
        raise ManchesterError("chip count must be even")
    bits, errors = [], 0
    for i in range(0, len(chips), 2):
        pair = (chips[i], chips[i + 1])
        if pair in _BIT_FOR_CHIPS:
            bits.append(_BIT_FOR_CHIPS[pair])
        else:
            errors += 1
            bits.append(chips[i])
    return bits, errors


def manchester_decode(chips) -> list:
    """Strict decode: raises ManchesterError on any invalid chip pair."""
    bits, errors = manchester_decode_with_errors(chips)
    if errors:
        raise ManchesterError(f"{errors} invalid chip pair(s)")
    return bits


def manchester_decode_bytes(chips) -> bytes:
    return bits_to_bytes(manchester_decode(chips))


# Short aliases
manchester_encode = manchester_encode_bits

# --------------------------------------------------------------------------
# PRBS-15 (paper's PER test mode): polynomial x^15 + x^14 + 1
# --------------------------------------------------------------------------
# Fibonacci LFSR, 15-bit state.  One step: the output bit is the state MSB
# (bit 14); the feedback bit is (bit14 XOR bit13) -- the taps of
# x^15 + x^14 + 1 -- and the state shifts left, feedback entering at bit 0.
# The polynomial is primitive, so any non-zero seed cycles through all
# 32767 non-zero states.  Bytes are packed MSB-first: the first bit
# generated is the MSB of byte 0.
#
# Reseeding per buffer (paper): seed = (buffer_count mod 32768) | 1.
# The |1 guarantees a non-zero (indeed odd) seed even for buffer_count 0.

PRBS15_PERIOD = 32767


def prbs15_seed(buffer_count: int) -> int:
    return (int(buffer_count) % 32768) | 1


class PRBS15:
    def __init__(self, buffer_count: int = 0, seed: int = None):
        self.state = (prbs15_seed(buffer_count) if seed is None
                      else (int(seed) & 0x7FFF))
        if self.state == 0:
            raise ValueError("PRBS-15 seed must be non-zero")

    def next_bit(self) -> int:
        s = self.state
        out = (s >> 14) & 1
        fb = ((s >> 14) ^ (s >> 13)) & 1
        self.state = ((s << 1) & 0x7FFF) | fb
        return out

    def next_byte(self) -> int:
        v = 0
        for _ in range(8):
            v = (v << 1) | self.next_bit()
        return v

    def next_bytes(self, n: int) -> bytes:
        return bytes(self.next_byte() for _ in range(n))


def prbs15_payload(buffer_count: int, nbytes: int = 5032) -> bytes:
    """The PRBS-15 payload for one buffer, reseeded as the paper specifies."""
    return PRBS15(buffer_count).next_bytes(nbytes)


class PRBS15Checker:
    """Counts bit errors of a received payload against the regenerated
    PRBS-15 payload for the same buffer_count (the paper's PER test:
    a packet fails if the count is > 0)."""

    def bit_errors(self, payload: bytes, buffer_count: int) -> int:
        expected = prbs15_payload(buffer_count, len(payload))
        return sum(bin(a ^ b).count("1") for a, b in zip(payload, expected))

    # Aliases for call-site readability.
    def count_errors(self, payload: bytes, buffer_count: int) -> int:
        return self.bit_errors(payload, buffer_count)

    def check(self, payload: bytes, buffer_count: int) -> int:
        return self.bit_errors(payload, buffer_count)

    def is_ok(self, payload: bytes, buffer_count: int) -> bool:
        return self.bit_errors(payload, buffer_count) == 0

    def packet_failed(self, payload: bytes, buffer_count: int) -> bool:
        return not self.is_ok(payload, buffer_count)


# --------------------------------------------------------------------------
# Packet framing (layout in the module docstring)
# --------------------------------------------------------------------------

SYNC_WORD = 0xC0FFEE11          # this project's own sync word
PREAMBLE_DUMMY_WORDS = 4        # 4 x 0x00000000 before the sync word
HEADER_WORDS = 11
PAYLOAD_SIZE = 5032
_HEADER_FIELDS = ("frame_idx", "global_pkt", "pkt_in_frame", "timestamp",
                  "pixel_count", "batt_raw", "vin_raw")
PACKET_SIZE = (PREAMBLE_DUMMY_WORDS + 1 + HEADER_WORDS) * 4 + PAYLOAD_SIZE
_SYNC_LE = struct.pack("<I", SYNC_WORD)


@dataclass
class Packet:
    frame_idx: int
    global_pkt: int
    pkt_in_frame: int
    timestamp: int
    pixel_count: int
    batt_raw: int
    vin_raw: int
    payload: bytes
    reserved: tuple = (0, 0, 0, 0)
    offset: int = 0     # byte offset of the sync word in the parsed stream


def build_packet(frame_idx, global_pkt, pkt_in_frame, timestamp,
                 pixel_count, batt_raw, vin_raw, payload5032) -> bytes:
    """Build one packet.  ``payload5032`` must be exactly 5032 bytes:
    the format carries no payload-length field, so any other length
    would be unparseable, and is rejected here instead of silently."""
    payload = bytes(payload5032)
    if len(payload) != PAYLOAD_SIZE:
        raise ValueError(
            f"payload must be {PAYLOAD_SIZE} bytes, got {len(payload)}")
    fields = [frame_idx, global_pkt, pkt_in_frame, timestamp,
              pixel_count, batt_raw, vin_raw]
    words = [0] * PREAMBLE_DUMMY_WORDS + [SYNC_WORD] + \
        [int(v) & 0xFFFFFFFF for v in fields] + [0] * 4
    return struct.pack(f"<{len(words)}I", *words) + payload


def _as_bytes(stream) -> bytes:
    if isinstance(stream, (bytes, bytearray, memoryview)):
        return bytes(stream)
    seq = list(stream)
    if seq and all(isinstance(v, int) and v in (0, 1) for v in seq):
        if len(seq) % 8:
            raise ValueError("bit stream length must be a multiple of 8")
        return bits_to_bytes(seq)
    return bytes(seq)


def parse_packets(stream) -> list:
    """Hunt the sync word in a byte stream (or a 0/1 bit list, packed
    MSB-first) and parse every complete packet.  After a successful
    parse the hunt resumes after that packet, so a sync pattern inside
    a payload is never mistaken for a new packet.  A trailing partial
    packet is ignored."""
    data = _as_bytes(stream)
    packets = []
    pos = 0
    frame_len = (1 + HEADER_WORDS) * 4 + PAYLOAD_SIZE
    while True:
        idx = data.find(_SYNC_LE, pos)
        if idx < 0 or idx + frame_len > len(data):
            break
        hdr = struct.unpack_from(f"<{HEADER_WORDS}I", data, idx + 4)
        payload = data[idx + 4 + HEADER_WORDS * 4: idx + frame_len]
        packets.append(Packet(
            frame_idx=hdr[0], global_pkt=hdr[1], pkt_in_frame=hdr[2],
            timestamp=hdr[3], pixel_count=hdr[4], batt_raw=hdr[5],
            vin_raw=hdr[6], payload=payload, reserved=tuple(hdr[7:11]),
            offset=idx))
        pos = idx + frame_len
    return packets
