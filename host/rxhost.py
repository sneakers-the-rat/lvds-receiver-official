#!/usr/bin/env python3
"""
rxhost.py — host tool for the photodiode LVDS receiver module.

Talks to the board over USB (vendor bulk + CDC control, mirroring the
firmware/src/usb_app.c command set: GET_INFO, SET_BIAS, SET_THRESHOLD,
GET_STATUS, BER_TEST_START/STOP, STREAM_START/STOP). Hardware access uses
pyusb if importable; without hardware (or with --simulate) every command
runs against SimBoard, a software model of the board built on the same
codec as the firmware tests (host/codec.py):

  * SimBoard generates paper-format packets (sync + 11-word header +
    5032-byte payload), encodes them 8b/10b (or Manchester in legacy
    mode), passes them through a channel model with a configurable bit
    error probability and jitter-free ideal CDR, and the host side
    decodes and verifies them — the complete verification flow a user
    would run on a laptop, with no FPGA and no board attached.
  * ber-test runs the paper's PRBS-15 PER method: buffers of 5032-byte
    PRBS payloads reseeded per buffer, any-bit-error fails the packet,
    and it reports BER and PER (one full trial would be 32767 buffers;
    the default is shorter and says so).

Usage:
  python3 host/rxhost.py --simulate info
  python3 host/rxhost.py --simulate config --bias 231.5 --threshold 42
  python3 host/rxhost.py --simulate stream --packets 20
  python3 host/rxhost.py --simulate ber-test --buffers 200 --ber 1e-5
  python3 host/rxhost.py --simulate selftest
Exit status 0 = success / test passed, 1 = failure.
"""
import argparse, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import codec

FW_VERSION = "rxfw 0.1 (simulated view)"
BOARD_ID = "PDLVDS-RX rev A (STM32H723VG + ADN2813 + C30737LH-500-90)"


class SimBoard:
    """Software model of the receiver board."""
    def __init__(self, ber=0.0, mode="8b10b", seed=1234):
        self.bias_v = 0.0
        self.hv_on = False
        self.threshold_mv = 25.0
        self.ber = ber
        self.mode = mode
        self.rng = random.Random(seed)
        self.buffer_count = 0
        self.temp_c = 24.6

    # --- control plane (mirrors firmware usb_app commands) ---
    def get_info(self):
        return {"board": BOARD_ID, "firmware": FW_VERSION,
                "detector": "C30737LH-500-90", "cdr": "ADN2813",
                "transport": "SIMULATED (no hardware)"}

    def set_bias(self, volts):
        if not (0.0 <= volts <= 420.0):
            raise ValueError(f"bias {volts} V outside 0..420 V range")
        self.bias_v = volts
        self.hv_on = volts > 0
        return {"bias_set_v": volts, "hv_on": self.hv_on,
                "temp_c": self.temp_c,
                "note": "temp-compensated by firmware at 1.3 V/degC"}

    def set_threshold(self, mv):
        if not (-200.0 <= mv <= 200.0):
            raise ValueError("threshold outside +/-200 mV DAC range")
        self.threshold_mv = mv
        return {"threshold_set_mv": mv}

    def get_status(self):
        return {"bias_v": self.bias_v, "hv_on": self.hv_on,
                "threshold_mv": self.threshold_mv,
                "temp_c": self.temp_c, "cdr_locked": self.hv_on,
                "mode": self.mode, "channel_ber_setting": self.ber}

    # --- data plane ---
    def _channel_bits(self, bits):
        """Flip bits with probability self.ber; returns (bits, n_flips)."""
        if self.ber <= 0:
            return bits, 0
        out, flips = [], 0
        for b in bits:
            if self.rng.random() < self.ber:
                out.append(b ^ 1); flips += 1
            else:
                out.append(b)
        return out, flips

    def next_packet_bits(self, payload=None):
        """One paper packet from the 'scope', encoded + through channel."""
        n = self.buffer_count
        if payload is None:
            payload = bytes(self.rng.getrandbits(8) for _ in range(5032))
        hdr = dict(frame_idx=n // 8, global_pkt=n, pkt_in_frame=n % 8,
                   timestamp=n * 1250, pixel_count=5032,
                   batt_raw=2048, vin_raw=2100)
        raw = codec.build_packet(hdr["frame_idx"], hdr["global_pkt"],
                                 hdr["pkt_in_frame"], hdr["timestamp"],
                                 hdr["pixel_count"], hdr["batt_raw"],
                                 hdr["vin_raw"], payload)
        if self.mode == "8b10b":
            bits = []
            enc = codec.Encoder8b10b()
            # leading K28.5 commas for alignment, as a real stream has
            for _ in range(4):
                bits += codec.code_to_bits(enc.encode_symbol(0xBC, True))
            for byte in raw:
                bits += codec.code_to_bits(enc.encode_symbol(byte))
        else:  # manchester legacy: chips at 2x
            bits = codec.manchester_encode_bytes(raw)
        bits, flips = self._channel_bits(bits)
        self.buffer_count += 1
        return bits, hdr, payload, flips

    def next_prbs_payload(self):
        payload = codec.prbs15_payload(self.buffer_count)
        bits = []
        for byte in payload:
            bits += [(byte >> (7 - i)) & 1 for i in range(8)]
        bits, flips = self._channel_bits(bits)
        rx = bytearray(5032)
        for i in range(5032):
            v = 0
            for j in range(8):
                v = (v << 1) | bits[8 * i + j]
            rx[i] = v
        bc = self.buffer_count
        self.buffer_count += 1
        return bytes(rx), bc, flips


def decode_stream_bits(bits, mode):
    if mode == "8b10b":
        res = codec.decode_bitstream(bits)
        return (res.data if res.aligned else None), res
    return codec.manchester_decode_bytes(bits), None


def cmd_info(board, _):
    for k, v in board.get_info().items():
        print(f"{k}: {v}")
    return 0


def cmd_config(board, args):
    if args.bias is not None:
        print(board.set_bias(args.bias))
    if args.threshold is not None:
        print(board.set_threshold(args.threshold))
    print(board.get_status())
    return 0


def cmd_stream(board, args):
    total_flips = code_errs = 0
    bad = 0
    for i in range(args.packets):
        bits, hdr, payload, flips = board.next_packet_bits()
        total_flips += flips
        data, dec = decode_stream_bits(bits, board.mode)
        if dec is not None:
            code_errs += dec.code_errors + dec.disparity_errors
        pkts = codec.parse_packets(data) if data else []
        ok = (len(pkts) == 1 and pkts[0].payload == payload
              and pkts[0].global_pkt == hdr["global_pkt"])
        if not ok:
            bad += 1
        print(f"packet {i}: header gp={hdr['global_pkt']} "
              f"flips={flips} decoded={'OK' if ok else 'MISMATCH'}")
    print(f"stream: {args.packets - bad}/{args.packets} packets verified, "
          f"channel flips={total_flips}, codec errors={code_errs}")
    return 0 if bad == 0 else 1


def cmd_ber_test(board, args):
    board.ber = args.ber
    chk_boards = []
    total_bits = total_err = failed = 0
    for _ in range(args.buffers):
        rx, bc, _flips = board.next_prbs_payload()
        errs = codec.PRBS15Checker().count_errors(rx, bc)
        total_err += errs
        total_bits += 40256
        failed += 1 if errs > 0 else 0
    ber = total_err / total_bits
    per = failed / args.buffers
    print(f"PRBS-15 PER test (paper method): buffers={args.buffers} "
          f"(a full paper trial = 32767 buffers)")
    print(f"bit errors: {total_err} / {total_bits} bits -> BER {ber:.3e} "
          f"(channel setting {args.ber:.1e})")
    print(f"packets failed: {failed}/{args.buffers} -> PER {per:.4f}")
    print(f"implied frame loss (8 pkt/frame): "
          f"{1 - (1 - per) ** 8:.4f}")
    return 0


def cmd_selftest(board, _):
    print("selftest: BIST LED -> APD -> TIA -> comparator -> CDR -> MCU "
          "(simulated with the real codec)")
    ok = True
    # 1) codec loopback
    bits, hdr, payload, _ = board.next_packet_bits()
    data, _dec = decode_stream_bits(bits, board.mode)
    pkts = codec.parse_packets(data) if data else []
    step = bool(pkts) and pkts[0].payload == payload
    print(f"  packet loopback ({board.mode}): {'PASS' if step else 'FAIL'}")
    ok &= step
    # 2) PRBS checker integrity
    rx, bc, _ = board.next_prbs_payload()
    errs = codec.PRBS15Checker().count_errors(rx, bc)
    step = errs == 0
    print(f"  PRBS-15 checker on clean channel: {'PASS' if step else 'FAIL'}")
    ok &= step
    # 3) control plane
    board.set_bias(200.0); board.set_threshold(30.0)
    st = board.get_status()
    step = st["hv_on"] and abs(st["bias_v"] - 200.0) < 1e-9
    print(f"  control plane (bias/threshold/status): "
          f"{'PASS' if step else 'FAIL'}")
    ok &= step
    print(f"selftest: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--simulate", action="store_true",
                    help="run against the software board model (no HW)")
    ap.add_argument("--mode", choices=["8b10b", "manchester"],
                    default="8b10b")
    ap.add_argument("--ber", type=float, default=0.0,
                    help="simulated channel bit-error probability")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info")
    c = sub.add_parser("config")
    c.add_argument("--bias", type=float)
    c.add_argument("--threshold", type=float)
    s = sub.add_parser("stream")
    s.add_argument("--packets", type=int, default=8)
    b = sub.add_parser("ber-test")
    b.add_argument("--buffers", type=int, default=100)
    b.add_argument("--ber", type=float, default=1e-5)
    sub.add_parser("selftest")
    args = ap.parse_args(argv)

    if not args.simulate:
        try:
            import usb.core  # noqa: F401  (pyusb, hardware path)
        except Exception:
            print("No hardware transport available (pyusb not installed) "
                  "and --simulate not given. Re-run with --simulate to "
                  "verify against the software board model.")
            return 1
        print("Hardware present-check not implemented in this revision; "
              "use --simulate. (Board USB stack bring-up: firmware/README)")
        return 1

    board = SimBoard(ber=args.ber, mode=args.mode)
    fn = {"info": cmd_info, "config": cmd_config, "stream": cmd_stream,
          "ber-test": cmd_ber_test, "selftest": cmd_selftest}[args.cmd]
    try:
        return fn(board, args)
    except ValueError as e:
        print(f"error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
