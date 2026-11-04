"""
digital_sim.py -- end-to-end digital link simulation for the photodiode
LVDS receiver.

    random bytes -> 8b/10b encode -> 50 Mbps bit stream -> channel
    -> comma realignment + 8b/10b decode -> error counts

plus the paper's PRBS-15 packet-error-rate (PER) method, and the paper's
Manchester path (8 Mbps data, 16 Mbaud chips) under the same channel.

CHANNEL MODEL -- what it is, and what it is NOT (read before quoting any
number from this file)
---------------------------------------------------------------------------
This is an honest, deliberately simplified decision-level model, not a
waveform simulation:

* Each transmitted bit is sampled once, at an instant offset from the
  centre of its unit interval (UI) by a Gaussian timing error
  dt ~ N(0, sigma_j).  sigma_j is an absolute time (default 2 ns, the
  project's R4 added-jitter budget); its size in UI is what matters, so
  the same 2 ns costs the 20 ns UI of the 50 Mbps path 0.10 UI but the
  62.5 ns chip of the Manchester path only 0.032 UI.
* The eye opening at that offset is modelled with a raised-cosine-like
  factor  eye(dt) = cos^2(pi * dt / 2)  for |dt| < 1 UI, else 0
  (dt in UI).  eye(0)=1, eye(0.5 UI)=0.5, eye(1 UI)=0.  This is the
  worst-case (alternating-neighbour) eye; a bit whose neighbours agree
  with it would in reality be sampled with a larger margin.
* Amplitude noise at the decision instant is Gaussian with sigma_v.
  SNR here is an *amplitude* ratio at the slicer:  A = 1 (normalised),
  sigma_v = 10**(-SNR_dB/20).  The per-bit error probability is then
      p_err(bit) = Q( A * eye(dt) / sigma_v ),   Q = Gaussian tail.
  Each bit is flipped independently with its own p_err (a Bernoulli draw).
* There is no bandlimiting/ISI calculation, no clock-recovery loop, no
  bit insertion/deletion (the channel flips bits, it never slips one),
  and the analog front end is not modelled at all (see link_budget.py).
  So the BER figures are "what this decision model gives", useful for
  comparing codings/rates and for sanity-checking the codec at scale --
  not a prediction of the hardware's measured BER.

Checks printed (and written to results/digital_sim.txt):
  (a) codec error-free at zero noise/jitter over 1,000,000 bits;
  (b) measured channel BER non-increasing with SNR over the sweep
      (the sweep reuses one jitter/uniform draw for every SNR point --
      common-random-number variance reduction -- so each point's error
      set is a subset of the previous point's, and monotonicity is a
      property of the model, not of sampling luck);
  (c) simulated PER vs the analytic PER = 1 - (1-BER)**40256 for
      independent bit errors, within a stated statistical bound
      (|sim - analytic| <= 4 * binomial sigma of the packet count);
  (d) at the SNR where A/sigma_v = 6 (SNR = 20*log10(6) = 15.56 dB,
      centre-of-eye BER = Q(6) ~= 1e-9), the measured BER over a
      1,000,000-bit run is < 1e-6 (with the jitter-reduced eye the
      model-mean BER there is ~2.5e-8, an expected ~0.025 errors in
      1e6 bits, so observing 0 is consistent).

Run:  python3 sim/digital_sim.py     (stdlib + numpy; matplotlib for the
optional plot, skipped with a note if unavailable)
Outputs: results/digital_sim.txt  (+ results/digital_sim.png if possible)
"""

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "host"))
import codec as c

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

LINE_RATE = 50e6            # 8b/10b line rate, bit/s
UI_S = 1.0 / LINE_RATE      # 20 ns
MC_DATA_RATE = 8e6          # Manchester data rate (paper's mode), bit/s
MC_CHIP_UI_S = 1.0 / (2 * MC_DATA_RATE)   # 62.5 ns per chip
SIGMA_J_S = 2e-9            # Gaussian timing-jitter sigma, seconds
A = 1.0                     # normalised eye amplitude at the slicer
PAYLOAD_BITS = 5032 * 8     # 40256, the paper's buffer size

SEED = 20261103


def qfunc(x):
    return 0.5 * np.vectorize(math.erfc, otypes=[float])(np.asarray(x) / math.sqrt(2.0))


def eye_factor(dt_ui):
    """Raised-cosine-like worst-case eye opening, dt in UI."""
    dt = np.abs(np.asarray(dt_ui, dtype=float))
    return np.where(dt < 1.0, np.cos(np.pi * dt / 2.0) ** 2, 0.0)


def per_bit_error_prob(snr_db, dt_ui):
    sigma_v = A * 10.0 ** (-snr_db / 20.0)
    return qfunc(A * eye_factor(dt_ui) / sigma_v)


# --------------------------------------------------------------------------
# 8b/10b path
# --------------------------------------------------------------------------

def encode_stream(data: bytes, leading_commas: int = 4):
    """Bytes -> bit list, preceded by K28.5 commas for alignment."""
    enc = c.Encoder8b10b()
    bits = []
    for _ in range(leading_commas):
        bits += c.code_to_bits(enc.encode_symbol(c.K28_5, control=True))
    for b in data:
        bits += c.code_to_bits(enc.encode_symbol(b))
    return bits


def run_8b10b_once(data, snr_db, rng, sigma_j_s=SIGMA_J_S,
                   dt_ui=None, uniforms=None):
    """One pass through the channel model + decoder.

    If dt_ui / uniforms are supplied they are reused verbatim (the sweep
    uses this for common-random-number monotonicity).  Returns a dict of
    counts.  Channel BER counts flipped bits; byte errors compare the
    decoded data bytes against ``data`` (a lost comma alignment counts
    every byte as an error, as it should).
    """
    bits = encode_stream(data)
    tx = np.array(bits, dtype=np.int8)
    n = len(tx)
    if dt_ui is None:
        dt_ui = rng.normal(0.0, sigma_j_s / UI_S, n)
    if uniforms is None:
        uniforms = rng.random(n)
    p_err = per_bit_error_prob(snr_db, dt_ui)
    flips = uniforms < p_err
    rx = tx ^ flips.astype(np.int8)
    res = c.decode_bitstream([int(v) for v in rx])
    if res.aligned and res.offset % 10 == 0:
        # Byte errors are counted per symbol slot, NOT by comparing
        # res.data (which drops code-errored symbols and would shift
        # every following byte out of place, inflating the count to
        # ~100% after the first dropped symbol).  The transmitted stream
        # starts on a symbol boundary, so a true comma lock lands at a
        # multiple of 10; that tells us exactly how many of the 4
        # leading comma slots precede the data (a comma corrupted into
        # a data-looking symbol still occupies its slot).  A lock at a
        # non-multiple of 10 can only be a false comma inside corrupted
        # data: positional correspondence is lost, every byte counts as
        # an error, and that is reported as-is rather than hidden.
        k = 4 - res.offset // 10
        slots = res.symbols[k:] if 0 <= k <= len(res.symbols) else []
        if len(slots) == len(data):
            byte_errors = sum(
                1 for (byte, is_ctrl, ce, _de), orig in zip(slots, data)
                if ce or is_ctrl or byte != orig)
        else:
            byte_errors = len(data)
    else:
        byte_errors = len(data)
    return {
        "bits": n, "bit_errors": int(flips.sum()),
        "ber": float(flips.mean()), "analytic_ber": float(p_err.mean()),
        "byte_errors": int(byte_errors),
        "byte_error_rate": byte_errors / len(data) if data else 0.0,
        "code_errors": res.code_errors, "disp_errors": res.disparity_errors,
        "aligned": bool(res.aligned), "offset": res.offset,
    }


# --------------------------------------------------------------------------
# PRBS-15 PER test (paper's method)
# --------------------------------------------------------------------------

def per_test(rng, lines):
    """Simulated PER vs analytic PER for independent bit errors.

    Packet outcomes are drawn as full (n_packets, 40256) Bernoulli bit
    arrays -- not a binomial shortcut -- so the "any bit differs" rule is
    applied to actual bits.  In parallel, a few packets per point are
    built as real PRBS-15 payloads, flipped at the drawn positions, and
    run through codec.PRBS15Checker: its count must equal the number of
    flipped bits, and its packet-failed verdict must match the array's.
    """
    n_packets = 600
    ok_all = True
    lines.append("")
    lines.append("PRBS-15 PER test (paper method: 5032-byte payload, "
                 "40256 bits, packet fails if any payload bit differs)")
    lines.append(f"  {'BER_in':>9} {'PER_analytic':>13} {'PER_sim':>9} "
                 f"{'packets':>8} {'4sigma_tol':>11}  verdict")
    checker = c.PRBS15Checker()
    for ber_in in (1e-5, 2e-5, 5e-5):
        flips = rng.random((n_packets, PAYLOAD_BITS)) < ber_in
        errs_per_pkt = flips.sum(axis=1)
        sim_per = float((errs_per_pkt > 0).mean())
        analytic = 1.0 - (1.0 - ber_in) ** PAYLOAD_BITS
        tol = 4.0 * math.sqrt(analytic * (1.0 - analytic) / n_packets)
        ok = abs(sim_per - analytic) <= tol
        ok_all &= ok
        # Physical cross-check with the real PRBS payload + checker.
        for pkt_i in range(4):
            bc = 1000 + pkt_i
            payload = bytearray(c.prbs15_payload(bc))
            idx = np.flatnonzero(flips[pkt_i])
            for bitpos in idx:
                payload[bitpos // 8] ^= 1 << (7 - (bitpos % 8))
            counted = checker.bit_errors(bytes(payload), bc)
            assert counted == len(idx), (counted, len(idx))
            assert checker.packet_failed(bytes(payload), bc) == (len(idx) > 0)
        lines.append(f"  {ber_in:9.1e} {analytic:13.6f} {sim_per:9.6f} "
                     f"{n_packets:8d} {tol:11.6f}  "
                     f"{'within bound' if ok else 'OUTSIDE BOUND'}")
    lines.append("  (PRBS15Checker cross-check on 12 physically built "
                 "packets: bit-error counts exact, fail verdicts agree)")
    return ok_all


# --------------------------------------------------------------------------
# Manchester path (the paper's mode)
# --------------------------------------------------------------------------

def run_manchester(rng, snr_db, n_bits=100_000, sigma_j_s=SIGMA_J_S):
    data_bits = rng.integers(0, 2, n_bits)
    chips = np.array(c.manchester_encode_bits([int(v) for v in data_bits]),
                     dtype=np.int8)
    dt_ui = rng.normal(0.0, sigma_j_s / MC_CHIP_UI_S, len(chips))
    p_err = per_bit_error_prob(snr_db, dt_ui)
    flips = rng.random(len(chips)) < p_err
    rx_chips = chips ^ flips.astype(np.int8)
    bits_out, invalid = c.manchester_decode_with_errors(
        [int(v) for v in rx_chips])
    bit_errors = int(np.sum(np.array(bits_out) != data_bits))
    return {
        "chip_ber": float(flips.mean()), "bit_errors": bit_errors,
        "ber": bit_errors / n_bits, "invalid_pairs": invalid,
        "analytic_chip_ber": float(p_err.mean()),
    }


# --------------------------------------------------------------------------

def main():
    rng = np.random.default_rng(SEED)
    lines = []
    checks = []

    def log(s=""):
        lines.append(s)
        print(s)

    log("Digital link simulation -- photodiode LVDS receiver")
    log("Model: simplified decision-level (per-bit Q(eye(dt)/sigma_v) with")
    log("Gaussian timing jitter; flips only, no slip, no ISI calculation).")
    log("See sim/digital_sim.py docstring for what the model is/is not.")
    log(f"50 Mbps path: UI = {UI_S * 1e9:.1f} ns, jitter sigma = "
        f"{SIGMA_J_S * 1e9:.1f} ns ({SIGMA_J_S / UI_S:.3f} UI), A = {A}")
    log(f"Manchester path: 8 Mbps data / 16 Mbaud chips, chip = "
        f"{MC_CHIP_UI_S * 1e9:.1f} ns, same jitter sigma "
        f"({SIGMA_J_S / MC_CHIP_UI_S:.3f} chip)")

    # (a) zero-noise codec run over 1e6 bits ------------------------------
    rng_a = np.random.default_rng(SEED + 1)
    data_a = rng_a.integers(0, 256, 100_000, dtype=np.uint8).tobytes()
    bits_a = encode_stream(data_a, leading_commas=1)
    assert len(bits_a) >= 1_000_000
    res_a = c.decode_bitstream(bits_a)
    ok_a = (res_a.aligned and res_a.data == data_a
            and res_a.code_errors == 0 and res_a.disparity_errors == 0)
    checks.append(("(a) zero-noise codec, 1e6 bits", ok_a))
    log("")
    log(f"(a) zero noise/jitter: {len(bits_a)} bits "
        f"({len(data_a)} data bytes + K28.5), decoded identical: "
        f"{res_a.data == data_a}, code errors {res_a.code_errors}, "
        f"disparity errors {res_a.disparity_errors}")

    # (b) SNR sweep, common random numbers --------------------------------
    n_sweep_bytes = 20_000                      # 200,040 bits per point
    data_s = np.random.default_rng(SEED + 2).integers(
        0, 256, n_sweep_bytes, dtype=np.uint8).tobytes()
    n_bits_s = (n_sweep_bytes + 4) * 10
    rng_crn = np.random.default_rng(SEED + 3)
    dt_crn = rng_crn.normal(0.0, SIGMA_J_S / UI_S, n_bits_s)
    uni_crn = rng_crn.random(n_bits_s)
    snrs = [0, 3, 6, 9, 12, 15]
    sweep = []
    for snr in snrs:
        r = run_8b10b_once(data_s, snr, rng_crn, dt_ui=dt_crn,
                           uniforms=uni_crn)
        sweep.append((snr, r))
    log("")
    log("BER vs SNR sweep, 8b/10b at 50 Mbps (200040 bits/point, "
        "common random numbers across points)")
    log(f"  {'SNR_dB':>7} {'sigma_v':>8} {'BER_meas':>11} "
        f"{'BER_analytic':>13} {'bit_err':>8} {'byte_err_rate':>14} "
        f"{'code_err':>9} {'aligned':>8}")
    for snr, r in sweep:
        log(f"  {snr:7.1f} {A * 10 ** (-snr / 20):8.4f} {r['ber']:11.3e} "
            f"{r['analytic_ber']:13.3e} {r['bit_errors']:8d} "
            f"{r['byte_error_rate']:14.3e} {r['code_errors']:9d} "
            f"{str(r['aligned']):>8}")
    bers = [r["ber"] for _, r in sweep]
    ok_b = all(b2 <= b1 for b1, b2 in zip(bers, bers[1:]))
    checks.append(("(b) BER monotonic non-increasing with SNR", ok_b))
    log(f"  measured BER sequence monotonic non-increasing: {ok_b}")
    for snr, r in sweep:
        if r["aligned"] and r["offset"] % 10 != 0:
            log(f"  note: at SNR {snr:.0f} dB all four leading commas were "
                f"corrupted and the comma hunt locked onto a false K28.5 "
                f"at bit offset {r['offset']} (not a multiple of 10), so "
                f"the byte error rate for that point is 1.0 by loss of "
                f"alignment, not by per-symbol errors.")

    # (c) PER vs analytic ---------------------------------------------------
    per_lines = []
    ok_c = per_test(np.random.default_rng(SEED + 4), per_lines)
    for s in per_lines:
        log(s)
    checks.append(("(c) PER sim vs analytic within 4-sigma bound", ok_c))

    # (d) Q = 6 operating point --------------------------------------------
    snr_q6 = 20.0 * math.log10(6.0)
    rng_d = np.random.default_rng(SEED + 5)
    data_d = rng_d.integers(0, 256, 100_000, dtype=np.uint8).tobytes()
    # ^ 100,000 data bytes -> 1,000,040 bits with the leading commas
    r_d = run_8b10b_once(data_d, snr_q6, np.random.default_rng(SEED + 6))
    ok_d = r_d["ber"] < 1e-6
    checks.append(("(d) BER < 1e-6 at Q=6 SNR over 1e6 bits", ok_d))
    log("")
    log(f"(d) Q=6 point: SNR = {snr_q6:.2f} dB (A/sigma_v = 6, centre-eye "
        f"BER = Q(6) = 9.9e-10); run = {r_d['bits']} bits, "
        f"bit errors = {r_d['bit_errors']}, measured BER = {r_d['ber']:.3e}, "
        f"model-mean BER = {r_d['analytic_ber']:.3e} (expected error count "
        f"in this run ~= {r_d['analytic_ber'] * r_d['bits']:.3f}, counting "
        f"the jitter-reduced eye; at the un-jittered centre-eye BER Q(6) "
        f"~= 1e-9 it would be ~0.001).  Observing 0 errors is consistent "
        f"with both, and the < 1e-6 criterion allows at most 1 error in "
        f"a run of this length.")

    # Manchester path (the paper's mode) --------------------------------------
    mc_snr = 6.0
    mc = run_manchester(np.random.default_rng(SEED + 7), mc_snr)
    ref = dict(sweep)[mc_snr]
    log("")
    log(f"Manchester path (paper's mode) at SNR = {mc_snr:.0f} dB, same "
        f"{SIGMA_J_S * 1e9:.0f} ns jitter sigma and same sigma_v:")
    log(f"  chip rate 16 Mbaud, chip BER measured {mc['chip_ber']:.3e} "
        f"(model mean {mc['analytic_chip_ber']:.3e}), invalid chip pairs "
        f"{mc['invalid_pairs']}, decoded bit BER {mc['ber']:.3e} "
        f"({mc['bit_errors']} bit errors / 100000 bits)")
    log(f"  comparison, 50 Mbps 8b/10b path at the same SNR: channel BER "
        f"{ref['ber']:.3e}, byte error rate {ref['byte_error_rate']:.3e}")
    log("  the Manchester path's advantage here is time margin only: its "
        "62.5 ns chip is 3.125x the 20 ns UI, so the same absolute jitter "
        "is a 3.125x smaller fraction of the interval it must decide in.")

    # Verdicts ---------------------------------------------------------------
    log("")
    all_ok = True
    for name, ok in checks:
        log(f"{'PASS' if ok else 'FAIL'}: {name}")
        all_ok &= ok
    log("PASS: digital_sim -- all checks passed" if all_ok
        else "FAIL: digital_sim -- see FAIL lines above")

    os.makedirs(RESULTS, exist_ok=True)
    txt_path = os.path.join(RESULTS, "digital_sim.txt")
    with open(txt_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    # Optional plot ----------------------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        xs = [s for s, _ in sweep]
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.semilogy(xs, [max(r["ber"], 1e-7) for _, r in sweep], "o-",
                    label="measured channel BER")
        ax.semilogy(xs, [r["analytic_ber"] for _, r in sweep], "s--",
                    label="model-mean BER, E[Q(eye/sigma_v)]")
        ax.axhline(1e-6, color="grey", lw=0.8)
        ax.set_xlabel("SNR at slicer (dB, amplitude ratio 20*log10(A/sigma_v))")
        ax.set_ylabel("BER")
        ax.set_title("8b/10b at 50 Mbps -- BER vs SNR (simplified model)")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(RESULTS, "digital_sim.png"), dpi=120)
        print("plot: results/digital_sim.png")
    except Exception as exc:  # plot is optional; the .txt is the record
        print(f"plot skipped: {exc}")

    print(f"wrote {txt_path}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
