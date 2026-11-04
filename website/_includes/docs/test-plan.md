## 05 — Bench test plan

Verification of a built rev A board against `docs/01-requirements.md`.
Every test names its requirement, equipment, procedure and pass
criterion. Predictions quoted are from the simulations in `results/`
so a measurement can be compared against the model, not just the
requirement. Safety first: §5 (HV) procedures apply whenever the APD
bias is on.

### Equipment

- Calibrated optical power meter (NIR head, 740 nm calibration point)
- 740 nm and 630 nm sources (LED or laser + driver), fibre or
  free-space launch with known spot size at the APD plane
- Variable optical attenuator, ≥40 dB range, calibrated at 740 nm
- Oscilloscope ≥500 MHz with a differential probe (LVDS eye/jitter)
- HV probe (1000:1, rated ≥600 V) and a DMM
- Current-limited bench supply + USB-C breakout (bring-up), then a
  plain laptop USB port (the product use case)
- Function/pattern generator able to drive the SMA test input with a
  50 Mbps 8b/10b or PRBS pattern (electrical injection tests)
- Host PC with the repo: `host/rxhost.py` is the test driver for all
  BER/PER tests (its `ber-test` replicates the paper's PRBS-15 method)

### 1. Sensitivity (R2)

**Pass: BER ≤ 1e-6 at ≥ −34 dBm average power at 740 nm on the bare
APD. Prediction (link budget): −45.6 dBm — expect ~11 dB of margin.**

1. Dark reading: cap the APD, record receiver noise floor behaviour
   (no CDR lock expected; LOS state noted for R-13 in docs/04).
2. Launch 740 nm, 50 Mbps 8b/10b PRBS-15 payload stream. Set power at
   the APD plane with the meter, then attenuate in 1 dB steps.
3. At each step run `rxhost.py ber-test` for ≥1e8 bits (at BER 1e-6
   that is ~100 expected errors; do not accept a "zero errors in 1e6
   bits" point as a 1e-6 measurement).
4. Record the power where BER crosses 1e-6. Repeat at 630 nm
   (prediction −44.3 dBm) and in Manchester mode — 8 Mbps, 16 Mbaud,
   the paper's transmitted format at its full rate — for a sanity point.

### 2. BER waterfall and PER (paper method)

**Pass: waterfall is a smooth slope (no cliff — a cliff implicates
LOS squelch, docs/04 R-13), and PER matches the analytic
PER = 1 − (1 − BER)^40256 within statistics.**

1. From the §1 sweep, tabulate BER vs power from 1e-3 to below 1e-9.
   Compare the curve's slope with `results/link_budget.png`: the model
   predicts ~1.3 dB between the 1e-6 and 1e-9 points.
2. PER, exactly per the paper: one trial = 32,767 buffers (one full
   PRBS-15 phase cycle), packet = 40,256 bits, any bit error fails the
   packet; average 5 trials. `rxhost.py ber-test` implements this;
   use its full-trial mode for the record measurements (the quick
   defaults used in CI smoke tests are labelled as such in its output).

### 3. Coverage (paper benchmark)

**Benchmark, not a hard requirement: the paper's single receiver
covered ~700 cm² of lateral area at PER 1e-3 (≈0.8% frame loss for
8-packet frames). Prediction for this design in lens mode: ~564 cm²
at 0.5 m height (geometric model; diffuse light understates both
sides of the comparison).**

1. Lens fitted (25 mm), source at 0.5 m above the receiver plane,
   PER 1e-3 threshold criterion from §2.
2. Raster the receiver laterally; map the area inside which
   PER ≤ 1e-3. Report the area and the shape (the model predicts a
   cone-limited disc).
3. Bare mode: repeat coarsely, then the diffuse check — source aimed
   at a translucent barrier/wall, receiver off-axis, confirm packet
   reception on scattered light (the paper's maze result says the
   original link works partly this way; wide-FOV bare mode exists for
   exactly this reason).

### 4. Analogue front end (R1)

**Pass: TIA −3 dB bandwidth ≥ 50 MHz (predictions: 138 MHz link
budget, 154 MHz ngspice); no peaking resonance visible in the swept
response; step response settles within 1 UI (20 ns; ngspice says
3.3 ns to 5%).**

1. Electrical injection at the SMA (APD capped/disconnected per the
   board's injection network): swept sine 1–200 MHz into the TIA,
   measure comparator-input swing or the post-stage test point;
   extract −3 dB frequency and any peaking.
2. Step response: fast edge in, observe settling at the same node.
3. Noise: input-referred noise via output noise with input dark,
   compare with 0.57 mV rms at the TIA output (both models agree
   within 0.02 dB — a large deviation means an assembly or bias
   problem, e.g. the asymmetric-rail point in docs/04 R-9).

### 5. HV bias (R9) — safety procedures mandatory

**Pass: settable 150–420 V; step resolution ≤ 0.5 V (the DAC map gives
≈0.42 V/code); ripple at the APD ≤ 20 mVpp (post-filter prediction is
µV-level analytically, 2.9 mVpp in the switching sim — either way the
limit has wide margin, so a failure means a real defect); bleeder
420 → <60 V in <10 s after disable (sim ≈0.9–1.3 s); temperature
compensation tracks 1.3 V/°C.**

Safety: HV probe only, one-hand rule, no rework with bias on, confirm
bleeder decay on the meter before touching the HV island, every time.

1. Calibration run from bring-up step 9 (docs/04): demanded vs
   measured voltage across the range → true DAC map (closes R-3).
2. Ripple: scope + HV probe at the APD cathode node, AC-coupled,
   20 MHz bandwidth limit off; record mVpp at 150/285/420 V.
3. Bleeder: disable at 420 V, time to <60 V. Repeat 3×.
4. Temp comp: log TMP117 temperature and measured Vbr-tracking —
   chill/heat the APD environment over ~10 °C and confirm the bias
   moves ≈1.3 V/°C in the compensating direction.

### 6. LVDS output and jitter (R4)

**Pass: TIA/EIA-644-A levels (VOD 250–400 mV into 100 Ω, VOS ≈1.2 V);
added jitter < 2 ns pk-pk (0.1 UI); prediction 1.2 ns pk-pk.**

1. Terminate the LVDS data output in 100 Ω at the scope diff probe.
2. Transmit a 1010… pattern at 50 Mbps; measure eye height/width and
   total jitter at BER-relevant crossings; subtract the source
   pattern's own jitter contribution measured at the SMA injection
   point (electrical loopback) to isolate the receiver's added jitter.
3. Repeat through the CDR path (recovered clock + data) and confirm
   the MCU-captured stream is error-free at high power for 1e9 bits.

### 7. Overload and recovery (R3) — the open item

**Pass: correct reception at +0 dBm, and recovery to BER ≤ 1e-6
within 10 UI (200 ns) after a +0 dBm burst ends.**

1. Burst test: alternate +0 dBm bursts (100 µs) with a −40 dBm
   1e-6-level signal; count post-burst bit errors with timestamps from
   the capture stream; convert the error run length to UI.
2. If recovery exceeds 10 UI, record the measured number in docs/04
   R-1 with the trace — do not tune it away silently; the requirement
   owner decides whether the mitigation (input clamp / Rf change)
   goes into rev B.

### 8. USB and host verification

**Pass: the module enumerates on an arbitrary laptop with no driver
install; `rxhost.py info` returns sane state; sustained streaming
carries the full 40 Mbps payload rate with zero packet loss over
1e6 packets; the complete verify flow runs with no FPGA attached
(the original user requirement).**

1. Cold-plug into a laptop that has never seen the device. Record
   enumeration time and descriptors.
2. `rxhost.py info`, `config` (bias + threshold readback vs set),
   `selftest` — all against real hardware (no `--simulate`).
3. Throughput: stream mode at full rate from an optical source,
   1e6 packets, host-side loss count must be zero; repeat over a
   hub and over USB-C→A adapter (the "random laptop" matrix).
4. BIST: `selftest` with the on-board LED loopback, no external
   source connected.

### 9. Manchester mode — the transmitted signal

**Pass: lock and error-free decode of an 8 Mbps Manchester stream
(16 Mbaud chips), the paper's uplink format.**

1. Pattern generator (or a second board's BIST pattern) emitting
   Manchester per IEEE 802.3 convention at 16 Mbaud.
2. Confirm CDR lock (ADN2813 range covers it), decode via the
   firmware Manchester path, 1e8 chips without a framing error at
   high power; then a short sensitivity spot-check vs §1.

### Record-keeping

Results land in `results/bench/` as dated files named
`<test>-<YYYYMMDD>.txt` (plus scope captures as PNG), each stating the
board serial, firmware commit hash (`git rev-parse HEAD` of the
firmware build), and equipment used. A test that fails is recorded
with its data and cross-referenced from `docs/04-risks.md` — failures
are results too.
