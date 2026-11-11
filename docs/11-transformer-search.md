# docs/11 — T1 transformer: broad off-the-shelf search and selection

Date: 2026-11-10. Trigger: the user rejected the controlled custom wind
(docs/09 F-10 resolution) as impractical to source in small quantities and
ordered a broad search beyond the first attempt. This file is the search
record and the selection. The converter redesign around the selected part
is proved separately (the HV clamp checker plus the new reachability
calculation) before the part is swapped into the design.

## What the part has to do (the spec any candidate is judged against)

From docs/09 (T1 winding spec) and the HV redesign (docs/07):

- Flyback transformer for the LT3757 converter, +5 V input.
- Output rail: up to 253.21 V nominal demand / 259.40 V worst-case
  (C30737 build); the mutually exclusive S8664 stuffing variant wants a
  430 V-class rail. Feedback divider senses the final rail, so the
  set-point clamp (docs/07 condition (b)) is topology-independent — but
  the converter must be *able* to reach 259.40 V.
- Original spec point: turns ratio 1:20, Lp 47 µH ±10 % at 250 kHz,
  Isat ≥ 2.6 A, leakage ≤ 500 nH target, hipot 1500 VAC
  primary–secondary, winding system rated ≥ 500 V working (the
  secondary stands at the HV rail).
- The load is tiny: the feedback divider (7.68 MΩ) draws ≈33 µA at
  253 V; total rail load < 100 µA, i.e. ≈15–25 mW. The 2.6 A saturation
  figure in the original spec follows the LT3757's maximum current
  limit with the originally fitted sense resistor — it is a *limit*,
  not an operating point. A redesign may lower the current limit (R28)
  and the switching duty point (turns ratio, secondary rectifier
  topology) to fit a catalog part, provided every bound is re-proved.
- Small-quantity practicality is a hard requirement: distributor stock
  at quantity 1, no factory quote, no custom or semi-custom winding.

## Candidates examined

### 1. Coilcraft LPR6235-253PMRC (coupled inductor, SEPIC/flyback use)
Turns ratio **1:20** exactly; inductance 25.0 µH ±20 % (at 10 kHz);
Isat 0.7 A (10 % drop, SEPIC connection); isolation **300 V**.
Verdict: **reject.** The isolation is the disqualifier — 300 V hipot
against a 253–430 V secondary working voltage and the project's
1500 VAC spec — and Isat is far below the original operating envelope.
(Source: Coilcraft product page, read 2026-11-10.)

### 2. Coilcraft Hexa-Path HP/HPH series (configurable, 6 × 1:1 windings)
Windings can be series/parallel combined to a 1:5 step-up. Per-winding
inductances 3.8–202 µH; Isat (base) 0.04–1.95 A depending on variant.
Isolation **500 Vrms** between windings.
Verdict: **reject** on isolation (500 Vrms < 1500 VAC spec).
(Source: Coilcraft Hexa-Path series pages, 2026-11-10.)

### 3. Eaton (formerly Coilcraft) Versa-Pac VP/VPH series
Same configurable 6-winding concept; L(base) 3.2–201.6 µH.
Isolation **500 VAC**.
Verdict: **reject** on isolation.
(Source: Eaton Technical Data 4301, 2017.)

### 4. Würth WE-FLEX (standard flexible transformer, EFD20)
6 identical windings, configurable; insulation test **500 VAC**.
Verdict: **reject** on isolation.
(Source: Würth datasheet 749196501.)

### 5. Allied Components AEFD20-3892 (EFD20 PoE flyback)
Lp 42 µH ±10 % at 250 kHz — near the original inductance — but
primary-to-secondary isolation only **500 VAC** (the 1500 VAC figure on
its datasheet is primary-to-auxiliary).
Verdict: **reject** on isolation.
(Source: Allied datasheet AEFD20-3892, 2016.)

### 6. Allied Components AEFD20-3782 (EFD20 flyback)
Turns ratio 2.76:1:1.17 (step-down), primary–secondary hipot 1000 VAC.
Verdict: **reject** — wrong direction and below the isolation spec.
(Source: Allied datasheet AEFD20-3782.)

### 7. Datatronics Romoland 4260-2757 (HV flyback, SMT)
Purpose-built high-voltage flyback: turns ratio 1:6, dielectric
withstand **3500 Vrms**, 300 V peak output class, 10 W, 500 kHz,
25.4 × 33 mm. Electrically this class of part fits.
Verdict: **reject on sourcing** — military/aerospace line, "consult
factory" pricing, no distributor stock at small quantity. That is the
custom-quote trap the user excluded, in a catalog costume.
(Sources: Datatronics datasheet 4260-2757; Electronic Design product
coverage, 2008.)

### 8. HV module route — XP Power (EMCO) AG series
Proportional DC-to-HVDC modules explicitly marketed for APD bias.
AG025P-12: 0–250 V max output — **below** this design's 253.21 V
nominal top of rail, so the C30737 build cannot reach its set-point.
AG05P-5 reaches 500 V from a 5 V input, but the output is proportional
and unregulated (±10 % class), the part costs ≈$73 in singles, and
adopting it discards the LT3757 loop and the docs/07 set-point clamp
argument wholesale.
Verdict: **reject** — the 250 V model cannot reach the rail; the
500 V model is a converter replacement, not a transformer replacement,
at ~6× the selected part's price.
(Sources: XP Power AG datasheet; DigiKey/Farnell listings, 2026-11-10.)

### 9. Würth WE-FLEX **HV** (EFD20, order code 749196518) — SELECTED
Six identical windings on an EFD20 frame, connectable in series and
parallel on the PCB; **insulation test voltage 1500 VAC, all
windings** — the one configurable family that meets the original
isolation spec. Datasheet figures for 749196518 (Würth Elektronik
Midcom, rev. 001.001, 2023-09-20):

- L(base) 22.3 µH ±20 % per winding (100 kHz)
- Turns ratio 1:1:1:1:1:1
- Saturation current (base) 0.93 A typ (ΔL/L < 10 %); the datasheet's
  scaling rule gives the per-winding saturation for partial drive as
  6 × Isat(base) / (number of driven windings)
- Rated current (base) 1.35 A typ; RDC(base) 102 mΩ max
- Volt-second capability (base) 123.4 Vµs max
- Leakage inductance (base) 0.24 µH typ
- Envelope 29.5 × 21.5 mm, height 12 mm, 12 SMD pins; the datasheet
  prints a recommended land pattern (the footprint is provable from
  the manufacturer's drawing — no raster-only figure this time)

Sourcing: **DigiKey lists 749196518 in stock (38 pcs) at $12.36 in
quantity 1 (cut tape), standard package 120** — a genuine
click-to-buy catalog part (DigiKey crawl 2026-10-22; recheck at order
time). Sibling variant 749196517 (9.9 µH, Isat 1.35 A) is electrically
attractive but Mouser shows it non-stocked with a 21-week factory
lead — the 518 is the stockable one.

## Selection and the redesign it implies

**T1 becomes Würth 749196518**, windings connected on the PCB as
**1 primary : 5 secondary in series (1:5)** with a **secondary voltage
doubler** replacing the single rectifier diode. Effective step-up
1:10 at the rectifier. Design consequences, each to be proved in the
redesign step before the swap lands:

- CCM duty at 253.21 V: the doubler needs a secondary amplitude of
  ≈126.6 V, i.e. D/(1−D) = 126.6/(5 × 5 V) = 5.06 → **D ≈ 0.835** at
  250 kHz — inside the LT3757's maximum-duty envelope (Dmax falls with
  frequency; verified against the datasheet in the redesign proof).
  Reachability of the 259.40 V worst-case demand needs D ≈ 0.838.
- Reflected secondary voltage at the primary: 126.6/5 ≈ 25.3 V;
  Q1 drain ≈ 5 + 25.3 + leakage spike — the fitted 60 V MOSFET keeps
  its margin class (original design: 430/20 ≈ 21.5 V reflected).
- Primary peak current is re-limited by R28 to **0.5 A**
  (from the 2.4 A class): energy per cycle at the limit is
  ½ · 22.3 µH · 0.5² ≈ 2.8 µJ → ≈0.7 W throughput ceiling at
  250 kHz, ≈30× the rail's worst-case draw. Saturation margin:
  0.5 A limit vs 0.93 A base saturation (all-driven figure, the
  conservative reading) = 1.9×.
- Volt-seconds on the primary winding: 5 V × (0.835/250 kHz)
  ≈ 16.7 Vµs vs the 123.4 Vµs capability — 7× margin.
- Doubler stresses: each diode blocks 2 × secondary amplitude ≈ 253 V
  (C30737 build) — the fitted ES1J class (600 V) stands; each doubler
  capacitor stands at the secondary amplitude ≈127 V — the fitted
  630 V film class stands.
- The S8664 (DNP alternate) build at 430 V would need D ≈ 0.896 with
  the doubler; disposition (acceptable at the LT3757's Dmax, or a
  tripler stuffing option) is settled in the redesign proof.
- Footprint: new 12-pin footprint drawn from the datasheet's printed
  land pattern; envelope grows from 23.11 × 26.1 mm (old EFD20 frame)
  to 29.5 × 21.5 mm — the HV district is re-laid and re-refereed.

What does **not** change: LT3757, switching frequency (250 kHz, R24),
the feedback divider and DAC set-point transfer (the docs/07 clamp
bound 259.40 V ≤ 260 V is untouched — it never depended on the
transformer), the SHDN re-ratio, the interlock, and the HV creepage
rules on the board.
