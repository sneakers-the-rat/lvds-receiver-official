# docs/12 — HV converter redesign around the WE-FLEX HV transformer

Date: 2026-11-10. Follows docs/11 (search + selection). This file is
the redesign record: the exact circuit that replaces the custom-wind
flyback, and the proof that it works. The proof is executable:
`sim/check_hv_flex.py` (23 checks, all PASS at this commit) alongside
the unchanged `sim/run_hv_clamp.py` (still PASS — the set-point bound
never depended on the transformer).

## What changes, in one paragraph

T1 becomes the Würth WE-FLEX HV 749196518 connected as a 1:5 flyback
(one winding primary, five in series as the secondary), the single
rectifier diode D5 is replaced by a two-cell Cockcroft–Walton ladder,
and the current-sense resistor R28 rises from 0.05 Ω to 0.15 Ω so the
LT3757's peak current limit (≤0.80 A worst case) sits below the
catalog part's saturation figure. Everything else in the converter —
LT3757, 250 kHz, feedback divider, DAC set-point transfer, SHDN
re-ratio, J5 interlock, OVP stack, post-filter — is untouched.

## Why the ladder (the honest arithmetic)

A flyback secondary winding does not swing symmetrically: with the
dot end of the string at GND it sits at −N·Vin while the switch is on
and at +Vf during flyback, where volt-second balance gives
Vf = N·Vin·D/(1−D). One Cockcroft–Walton cell therefore delivers
Vf + N·Vin = N·Vin/(1−D), **not** 2·Vf. (The first sketch of this
design, in docs/11 as originally written, priced a "doubler" at
2·Vf and D ≈ 0.835; that was wrong for this waveform and docs/11 is
corrected.) With N = 5 and Vin = 5 V:

- 1 cell: Vout = 25/(1−D) → 259.40 V needs D = 0.904, and the
  S8664 variant's 420 V needs D = 0.940 — on top of the LT3757's
  Dmax (0.945 at 250 kHz from its 220 ns typical minimum off-time).
  Not enough margin.
- **2 cells: Vout = 50/(1−D)** → 259.40 V needs D = 0.807; 420 V
  needs D = 0.881. Off-times 732–476 ns against the 220 ns typical
  minimum. Chosen.
- The plain 1:5 rectifier with no ladder needs D = 0.910 / 0.943.
  Rejected, same reason.

## Winding map (datasheet schematic, rev 001.001)

Windings: N1 = 1(dot)–2, N2 = 3(dot)–4, N3 = 5(dot)–6,
N4 = 12(dot)–11, N5 = 10(dot)–9, N6 = 8(dot)–7.

| Pins | Connection |
|---|---|
| 1 (dot) | +5 V (PRI_A, as before) |
| 2 | FLY_PRI (Q1 drain node, as before) |
| 3 (dot) | GND — start of the secondary string |
| 4 – 5 | link net HV_S1 |
| 6 – 12 | link net HV_S2 |
| 11 – 10 | link net HV_S3 |
| 9 – 8 | link net HV_S4 |
| 7 | HV_SEC — far end of the string, positive during flyback |

## The ladder (replaces D5)

| Part | Connection | Stands at |
|---|---|---|
| C52, 100 nF 630 V | HV_SEC → HV_M1 | N·Vin ≈ 26 V |
| D12, ES1J | GND → HV_M1 (clamp) | ≤ Vout/2 |
| D13, ES1J | HV_M1 → HV_M2 | ≤ Vout/2 |
| C53, 100 nF 630 V | HV_M2 → GND | Vout/2 |
| C54, 100 nF 630 V | HV_M1 → HV_M3 | Vout/2 |
| D14, ES1J | HV_M2 → HV_M3 (clamp) | ≤ Vout/2 |
| D15, ES1J | HV_M3 → HV_RAW | ≤ Vout/2 |
| C32, 100 nF 630 V | HV_RAW → GND (existing reservoir) | Vout |

(D12–D15 / C52–C54 are the designators assigned in circuit.py;
the ladder caps are the same 100 nF 630 V 1206 class as C32.)

New nets HV_S1–HV_S4 and HV_M1–HV_M3 join the HV net class (peaks up
to 210 V on the ladder nodes in the S8664 variant).

## Proof summary (sim/check_hv_flex.py, all PASS)

- **Duty**: every demanded rail (116.07 / 253.21 / 259.40 V C30737;
  420 V S8664) at Vin = 4.75 / 5.0 / 5.25 V sits at D = 0.548–0.887,
  off-time ≥ 452 ns vs the 220 ns typical minimum.
- **Saturation**: Ilim max = 120 mV / 0.15 Ω = 0.80 A < I_SAT BASE
  0.93 A typ under the conservative reading (one winding's figure
  applied to the primary alone). The ampere-turn reading (six
  windings share one core; the base figure is specified with all
  windings driven) gives a further ~6×, but the design does not
  depend on it: this datasheet (Midcom rev 001.001) does not print
  the scaling footnote, so it is not claimed.
- **Operating point**: full-load rail draw 22.5 mW (divider 8.3 mW +
  bleeder 13.6 mW + APD allowance) → primary peak ≈ 120 mA;
  on-time 408 ns > 220 ns minimum.
- **Volt-seconds**: worst 18.4 Vµs vs 123.4 Vµs capability.
- **Q1 drain** (steady, spike excluded): 25.9 V (C30737 worst case),
  42.0 V (S8664) vs 60 V rating.
- **Stresses**: every ladder diode blocks ≤ Vout/2 = 210 V vs 600 V;
  ladder caps ≤ 210 V vs 630 V class; reservoir ≤ 420 V vs 630 V.
- **Startup**: rail energy 49 mJ charges in ≥ 49 ms at the typical
  current limit; the soft-start ramp governs in practice.
- **Leakage**: referred ≈ 0.29 µH typ, inside the custom wind's
  ≤ 0.50 µH target.

## Known residuals, stated plainly

- **Leakage spike on Q1 is unclamped in both designs.** The custom
  wind had no drain clamp either. Spike *energy* scales with
  L·I²: the new design's worst case (0.29 µH at 0.80 A ≈ 93 nJ) is
  ~15× below the old one's (0.50 µH at 2.4 A ≈ 1.44 µJ), and drain
  steady peaks are comparable (25.9 V vs 26.5 V class). The S8664
  variant's 42.0 V steady peak is the tightest number in the
  redesign; it rides on the same bench-verification list as the rest
  of the HV section (docs/05).
- **Light-load pulse behaviour at the bottom of the range.** The
  minimum on-time pulse of the new (smaller) inductance delivers
  ≈27 nJ; at 116 V the rail load is ≈4.8 mW < the ≈6.8 mW that
  continuous minimum pulses would deliver at 250 kHz, so the loop
  will occasionally skip cycles at the lowest bias settings (the old
  47 µH design's minimum was ≈3.2 mW and it did not need to). The
  R29/C33 + C4 post-filter stands between this and the APD node;
  bias ripple is already a bench-list item (docs/05).
- Isat and the minimum on/off times are **typical** datasheet
  figures, as they were for the custom-wind design's margins; the
  checker demands ≥2× off-time margin and a sub-1.0 saturation
  ratio precisely because they are typicals.

## What the swap step must touch

circuit.py (T1 entry + pin map, R28 value, D5 out, D12–D15 / C52–C54
in), CONNECTIONS.md HV section, gen_schematic.py regeneration with
the identity snapshot re-proved, a new 12-pin footprint drawn from
the datasheet's printed land pattern (pads 3.50 × 2.25 mm, pitch
3.00 mm, columns 26.20 mm apart — no raster-only figure this time),
the board's HV district re-laid, both referees re-run, and the slot
census re-run near the HV slot. docs/08/docs/09 F-10 text superseded
by docs/11 + this file.
