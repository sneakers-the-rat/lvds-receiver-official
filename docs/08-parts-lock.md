# 08 — Parts lock-in audit (rev A board, pass 76)

**Scope.** Every fitted part on the board — all 144 reference designators in
`hw/pdlvds_rx.exp13.kicad_pcb` at HEAD `9a47f58` (pass 76) — audited for
identity, footprint/land pattern, ratings vs circuit demand, and
work-together compatibility, BEFORE further routing is trusted. This audit
**reports only**: it modifies no board, schematic, or footprint file.
Fixes are separate directed work.

**Sources (primary).** `hw/circuit.py` (the authoritative circuit, per
`hw/CONNECTIONS.md`), `hw/CONNECTIONS.md`, `docs/01-requirements.md`,
`docs/02-architecture.md`, `docs/03-power.md` (rail table = the demand
source), `docs/04-risks.md`, `docs/07-d1-terminal-pair-evidence.md`
(D1 — cited, not re-derived), `datasheets/` incl. `MANIFEST.md`, the five
custom footprints in `hw/pdlvds.pretty/` (pad geometry measured from the
files), the board file itself (footprint assignment + an intra-footprint
pad-overlap scan), and manufacturer datasheets fetched for this audit:
ADN2813 Rev. C and LT3042 Rev. C (analog.com), TPS62130 SLVSAG7F and
SN65LVDS32 SLLS262R (ti.com), IRLML0030 PD-96278B (Infineon, via Mouser),
ES1J series data, USBLC6-2 DS4260 (ST, via Mouser), Abracon ASE family
data, Amphenol 12401610E4#2A product specification, SMBJ series data.
Two fetches failed and are recorded as gaps, not silently bridged: the
LT3757 datasheet (analog.com network error — the project's own copies
are truncated at the same numbers, see MANIFEST and docs/04 R-3) and
STM32H723 DS13313 (st.com unreachable — the same block the project
recorded in MANIFEST).

**Evidence standard (declared).**
- Custom footprints (`hw/pdlvds.pretty/`) and any footprint a finding
  turns on: checked at pad level against the manufacturer's pattern.
- Stock KiCad library footprints: checked at package-identity level —
  body size, pitch, pin count and (where the datasheet states it) exposed
  pad nominal — against the manufacturer's package data. Pad-for-pad
  re-measurement of JEDEC-standard library patterns was not repeated.
- Commodity passives (chip R/C/L) in low-voltage positions: no project
  source names a manufacturer part, so the rating check uses the most
  conservative rating of the footprint class (0603 resistor 75 V/0.1 W,
  0805 150 V/0.125 W, 1206 200 V/0.25 W max working voltage; 0603 MLCC
  ≥4.7 µF treated as 6.3 V class floor, small-value 0603 MLCC ≥10 V
  class floor). Any position whose demand approaches or exceeds the
  class floor, or sits on a special rail (HV, INTVCC, VBUS), got an
  individual check — those are the rows that fail below.
- A verdict of LOCKED requires: identity specified well enough to buy
  the same part again, footprint verified at the level above, ratings
  verified ≥ demand, and no work-together conflict. Anything else is
  NOT LOCKED, with the failing check and the specific lock action.

**Verdict summary.** **115 LOCKED / 29 NOT LOCKED** of 144.
- **Tier 1 — wrong or dangerous as specified (13):** D1, D2, C4, D4, U9,
  R27, Q1, T1, R29, R30, R31, R34, C31.
- **Tier 2 — not proven (identity/provenance/margin paperwork) (16):**
  U6, C17, C18, U10, R24, U13, X1, C20, C21, X2, L1, L2, FB1, FB2, D8, SH1.

## System findings

- **F-01 — D1 fitted detector is over-voltaged by design (OPEN, owner
  decision pending).** Excelitas C30737LH-500-90: VBR max 260 V vs a rail
  designed to ≈420 V with no hardware bound. Fully evidenced in
  `docs/07-d1-terminal-pair-evidence.md`; cited here, not re-derived.
- **F-02 — Two required parts do not exist on the board.** Requirement
  R9 (docs/01) demands a *hardware over-voltage clamp independent of
  firmware* and an *HV enable interlock*; docs/02 promises a "hardware
  OVP zener clamp at 440 V". The 144-part census contains **no clamp
  device on the HV rail and no interlock device anywhere** (consistent
  with docs/06's interlock finding). These are missing parts, recorded
  here because a parts audit is where an absent part surfaces.
- **F-03 — C4 contradicts the project's own assembly note.** C4 (1 µF)
  sits directly across APD_K–GND (up to ≈420 V). CONNECTIONS.md's BOM
  note requires "a 630 V 1206 in that position"; circuit.py generates a
  **0603** with no voltage rating. No 1 µF 0603 MLCC is rated near 420 V.
- **F-04 — U9's footprint shorts every pin to ground.** Measured from
  the board file: in TMP117_WSON6, pads 1–6 overlap the grounded
  exposed pad (pad 7) by 0.20 mm — the only intra-footprint overlap on
  the board. Its geometry also disagrees with TI's DRV0006B land
  pattern (see U9 row).
- **F-05 — D4 is the wrong package for its footprint.** SMBJ5.0A is a
  JEDEC DO-214AA (SMB) part; the fitted footprint is D_SMA (DO-214AC).
- **F-06 — Single standard 1206 resistors stand across the 420 V rail.**
  R31 (≈418 V continuous), R30 (420 V), R34 (≈420 V) each exceed the
  200 V max working voltage of a standard 1206 every second HV is on;
  R29 is in the same chain under fault. C31 is the low-voltage analogue:
  7.2 V INTVCC across an unspecified 0603 4.7 µF (6.3 V class floor).
- **F-07 — The HV servo's governing numbers are unverified.** LT3757
  FBX reference (taken as 1.6 V), RT value for 250 kHz (R24 24.9 kΩ),
  and the SENSE current-limit threshold are truncated in both of the
  project's datasheet copies (MANIFEST; docs/04 R-3) and this audit's
  manufacturer fetch failed. The FBX number sets the entire
  DAC→voltage map including the 420 V ceiling used in docs/03.
- **F-08 — MCU documentation rests on a symbol library, not the
  datasheet.** STM32H723ZGT6 pin map provenance is ST's KiCad symbol
  (cross-checked against two secondary tables, MANIFEST Stage-7);
  DS13313 was unreachable for the project and for this audit, so the
  VDD/VDDA ranges and the VCAP capacitor requirement (C17/C18) are
  unverified from the manufacturer document.
- **F-09 — Neither frequency source is a specified part.** X1 is
  "24MHz" with no part number (USB3300 demands CL 20 pF typ / ESR
  ≤30 Ω from its Table 5-8; C20/C21 realize ≈14–16 pF); X2 is "25MHz
  OSC" with no full Abracon ordering code (the ASE family is ordered
  with a supply-voltage option).
- **F-10 — Magnetics are unspecified.** T1 has no manufacturer or part
  number anywhere (design intent exists only as sim parameters), on a
  custom footprint matching no identified production transformer.
  L1/L2/FB1/FB2 have values and footprints but no rated-current spec.
- **F-11 — +VA dropout margin is unverified.** docs/03's claim
  (LT3042 dropout ≈60 mV at 40 mA, so +VA holds to VBUS ≈4.7 V) could
  not be confirmed from the LT3042 datasheet read in this audit, which
  brackets dropout at 220–350 mV over 50–200 mA. Worst-case headroom is
  150 mV (VBUS 4.75 V − 4.6 V). See U13 row.
- **F-12 — The HV switch pair is marginal and self-contradictory.**
  Q1 (IRLML0030, VDSS 30 V) sees ≈26.1 V spike-free off-state stress
  (87% of rating) with no clamp fitted anywhere; and its gate resistor
  R27 is 10 Ω in CONNECTIONS.md but 10 kΩ in circuit.py — the
  as-generated value cannot switch the FET at 250 kHz.
- **F-13 — Loose identities.** D8's wavelength is 740 nm in circuit.py
  and CONNECTIONS.md but 630 nm in docs/02 and docs/04, with no part
  number in any source. SH1 (shield can, required by R10) names no
  production can for its custom 26×20 footprint.

## Work-together checks (summary; detail in the rows)

- **Supply domains** — every consumer checked against the docs/03 rail
  table: +3V3D 3.296 V, +3V3D_CDR ≈3.3 V, +3V3A 3.32 V, +VA 4.6 V,
  −VA ≈−5.4 V, +5V 4.75–5.25 V, INTVCC 7.2 V, PHY_1V8 1.8 V.
  All COMPATIBLE except: U13's dropout margin at worst-case VBUS
  (UNVERIFIED, F-11); C31's capacitor rating on INTVCC (F-06); and the
  OPA657 check, which PASSES on the datasheet's own terms — TI
  specifies its supply as a *total* (recommended 8/10/12 V), and
  +4.6/−5.4 V is exactly 10.0 V total. U12's inverting TPS62130 was
  verified pin-by-pin against its datasheet absolute maximums referred
  to its own ground (NEG_RAW): all pins within limits, including EN
  (rated VIN+0.3, tied to VIN potential).
- **Shared buses** — I2C: ADN2813 at 0x40 (SADDR5=GND) vs TMP117 at
  0x48 (ADD0=GND): distinct, COMPATIBLE; bus speed bounded by the
  ADN2813's 400 kHz SCK max; pull-ups R20/R21 fitted. SPI: one slave
  (DAC8562, SYNC = PA15) — no chip-select conflict. TMP117 ALERT
  (open-drain) has its pull-up: R22 goes to +3V3D (verified in
  circuit.py, not a series resistor).
- **Interfaces** — CDR input range 10–1250 Mb/s vs the 16 Mbaud
  Manchester chip stream and the 50 Mb/s 8b/10b target: COMPATIBLE
  (R6 met by the part). REFCLK 25 MHz vs ADN2813's 10–160 MHz,
  single-ended drive datasheet-sanctioned: COMPATIBLE. LMH7220 LVDS
  (250–400 mV diff, 1.125–1.325 V CM) AC-coupled into ADN2813
  (3.3 mV pp sensitivity, 2.0 V max diff, internal 100 Ω):
  COMPATIBLE. ADN2813 LVDS out → SN65LVDS32 (±100 mV thresholds,
  100 Mb/s rating): COMPATIBLE. ULPI: USB3300 sources the 60 MHz
  CLKOUT, the STM32's OTG-HS ULPI consumes it — direction and rate
  correct; no MCU crystal is fitted, by design. Crystal load: see
  X1/C20/C21 rows (accuracy COMPATIBLE, identity UNVERIFIED).
  Comparator input window (−0.2..VCC−2 = −0.2..+2.6 V at VCC 4.6 V)
  contains both idle points (0 V direct path, 2.3 V post-amp path);
  the R3 overload swing can leave it — already open as docs/04 R-1.

## Full table

Columns: Identity (as specified in project sources) · Footprint vs
manufacturer land pattern · Ratings vs demand · Work-together ·
Verdict. "Stock" = KiCad library footprint, package-identity check per
the declared standard.

| Ref | Identity | Footprint | Ratings vs demand | Work-together | Verdict |
|---|---|---|---|---|---|---|

| C1 | 0.4 pF NP0, 0402 (TIA feedback) | C_0402 stock — MATCH (package class) (board: `C_0402_1005Metric`) | WITHIN: ≤ ≈3.5 V across it | Note: docs/02 quotes Cf as 0.35 pF (§TIA) and 0.45 pF (deviation #4); circuit.py fits 0.4 pF discrete — value-provenance scatter in the docs, the part itself is a standard value | **LOCKED** |
| C2 | 100 nF, 0603 (+VA decoupling) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) (5.25 V max rail exposure) | — | **LOCKED** |
| C3 | 100 nF, 0603 (−VA decoupling) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) (5.5 V max rail exposure) | — | **LOCKED** |
| C4 | 1 µF MLCC, 0603 — **no voltage rating specified** | C_0603 as generated — **CONFLICT**: CONNECTIONS.md's BOM note requires a 630 V 1206 in this position; circuit.py generates 0603 (board: `C_0603_1608Metric`) | **EXCEEDS**: wired directly across APD_K–GND = up to ≈420 V continuous; no 1 µF 0603 MLCC is rated anywhere near 420 V (HV 0603 series stop ≈250 V at far smaller capacitances) — F-03 | Decouples the HV node at the TIA end of the board | **NOT LOCKED** |
| C5 | 1 nF, 0603 | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | AC-couples TIA_OUT to the post-amp input | **LOCKED** |
| C6 | 10 µF, 0805 (VMID reservoir) | C_0805 stock — MATCH (package class) (board: `C_0805_2012Metric`) | WITHIN: 2.3 V demand vs 6.3 V class floor | — | **LOCKED** |
| C7 | 100 nF, 0603 | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| C8 | 100 nF, 0603 (AC coupling, CMP_QP→CDR) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN: ≤ LVDS CM ≈1.3 V + signal | COMPATIBLE: τ = 100 Ω × 100 nF = 10 µs vs worst CID 125 ns (16 Mbaud) / 100 ns (50 Mb/s) — droop negligible (ADN2813 guidance) | **LOCKED** |
| C9 | 100 nF, 0603 (AC coupling, CMP_QN→CDR) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN: ≤ ≈1.3 V | As C8 | **LOCKED** |
| C10 | 100 nF, 0603 (U3 decoupling) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| C11 | 100 nF, 0603 (threshold filter) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | THR_FILT node ≤ ≈2.6 V | **LOCKED** |
| C12 | 1 µF, 0603 (VREF decoupling) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN: VREF node ≈2.5 V | Deviation noted: ADN2813 guidance is 0.1 µF at VREF (pin 3); 1 µF fitted — larger bypass on a DC bias node, no conflict | **LOCKED** |
| C13 | 100 nF, 0603 (SLICEP/N coupling) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | AC-couples slice pins to GND = zero slice offset, per circuit intent | **LOCKED** |
| C14 | 100 nF, 0603 (REFCLKN coupling) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Single-ended REFCLK configuration (datasheet-sanctioned) | **LOCKED** |
| C15 | 0.47 µF, 0603 (loop filter CF1–CF2) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN: low-voltage node | Value is the datasheet's own spec condition (CF = 0.47 µF) — exact | **LOCKED** |
| C16 | 100 nF, 0603 (U5 decoupling) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| C17 | 2.2 µF, 0603 (VCAP) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | **UNVERIFIED (dependent)**: value and the ≈1.3 V-class VCAP rail are the project's design data; ST's VCAP capacitance requirement is part of the same un-read DS13313 — one lock action with U6 | VCAP pair with C18 | **NOT LOCKED** |
| C18 | 2.2 µF, 0603 (VCAP) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | **UNVERIFIED (dependent)**: as C17 | VCAP pair with C17 | **NOT LOCKED** |
| C19 | 100 nF, 0603 (NRST) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| C20 | 33 pF, 0402 (XI load) | stock chip pattern — MATCH (package class) (board: `C_0402_1005Metric`) | WITHIN (LV class demand, docs/03 rails) | **Paired with X1**: as fitted it under-loads a 20 pF-CL crystal (≈14–16 pF realized); lock = specify the crystal CL and recompute (for CL 20 pF, ≈28 pF class caps), or specify a 12–14 pF-CL crystal for the fitted 18 pF | **NOT LOCKED** |
| C21 | 18 pF, 0603 (XO load) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | As C20 | **NOT LOCKED** |
| C22 | 4.7 µF, 0402 (VDDA1.8 reservoir) — shrunk 0603→0402 at pass 210 for the CAP-district F channel (C20 precedent) | stock chip pattern — MATCH (package class) (board: `C_0402_1005Metric`) | WITHIN: 1.8 V vs 6.3 V class floor | Datasheet asks 4.7 µF low-ESR ∥ 0.1 µF at VDDA1.8 — C22+C23 fitted as specified | **LOCKED** |
| C23 | 100 nF, 0603 (VDDA1.8 HF) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Pairs with C22 per datasheet | **LOCKED** |
| C24 | 100 nF, 0402 (PHY decoupling) — shrunk 0603→0402 at pass 210 for the CAP-district F channel (C20 precedent) | stock chip pattern — MATCH (package class) (board: `C_0402_1005Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| C25 | 10 µF, 0805 (+5V bulk) | C_0805 stock — MATCH (package class) (board: `C_0805_2012Metric`) | WITHIN: 5.25 V max vs 6.3 V class floor | — | **LOCKED** |
| C26 | 100 nF, 0603 (DAC VREF decoupling) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Internal-reference decoupling per datasheet practice | **LOCKED** |
| C27 | 100 nF, 0603 (DAC decoupling) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| C28 | 100 nF, 0402 (X2 decoupling) — shrunk 0603→0402 AND relocated (73.5,20.5)→(73.25,20.75) at pass 210 to close +3V3D join 2 | stock chip pattern — MATCH (package class) (board: `C_0402_1005Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| C29 | 10 nF, 0603 (VC compensation) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | With R23 | **LOCKED** |
| C30 | 100 nF, 0603 (SS) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Soft-start timing | **LOCKED** |
| C31 | 4.7 µF, 0603 (INTVCC bypass) — **no voltage rating specified** | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | **EXCEEDS the class floor**: sits on INTVCC = 7.2 V; commodity 0603 4.7 µF MLCCs are commonly 6.3 V-rated — below the rail. The value is right (LT3757 requires ≥4.7 µF, MANIFEST); the rating is the gap. Lock = specify a ≥10 V-rated 4.7 µF part — F-06 | Bypasses the rail that drives Q1's gate | **NOT LOCKED** |
| C32 | 100 nF **630 V**, 1206 (HV_RAW reservoir) | C_1206 stock — MATCH (package class) (board: `C_1206_3216Metric`) | WITHIN: 630 V specified in the value itself vs 420 V demand (1.5×) | HV_RAW node with D5/R29 | **LOCKED** |
| C33 | 100 nF **630 V**, 1206 (APD_K reservoir) | C_1206 stock — MATCH (package class) (board: `C_1206_3216Metric`) | WITHIN: 630 V specified vs 420 V demand | The APD_K node capacitor (contrast C4, same node, 0603) | **LOCKED** |
| C34 | 1 nF, 0603 (FBX filter) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN: 1.6 V node | — | **LOCKED** |
| C35 | 10 µF, 0805 (+5V bulk at HV input) | C_0805 stock — MATCH (package class) (board: `C_0805_2012Metric`) | WITHIN: 5.25 V max vs 6.3 V class floor | LT3757 input bulk (docs/03) | **LOCKED** |
| C36 | 3.3 nF, 0603 (SS/TR) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Soft-start for U11 | **LOCKED** |
| C37 | 10 µF, 0805 (+5V input bulk) | C_0805 stock — MATCH (package class) (board: `C_0805_2012Metric`) | WITHIN: 5.25 V max vs 6.3 V class floor | — | **LOCKED** |
| C38 | 22 µF, 0805 (+3V3D output) | C_0805 stock — MATCH (package class) (board: `C_0805_2012Metric`) | WITHIN: 3.3 V vs 6.3 V class floor | — | **LOCKED** |
| C39 | 3.3 nF, 0603 (SS/TR, referenced to NEG_RAW) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN: SS pin ≤ VIN rel. IC ground | Correctly referenced to the IC's own ground net | **LOCKED** |
| C40 | 22 µF, 0805 (−VA output, GND side +) | C_0805 stock — MATCH (package class) (board: `C_0805_2012Metric`) | WITHIN: 5.5 V across it vs 6.3 V class floor | Output reservoir for the −5.5 V raw rail | **LOCKED** |
| C41 | 22 µF, 0805 (+3V3D bulk) | C_0805 stock — MATCH (package class) (board: `C_0805_2012Metric`) | WITHIN: ≤5.25 V exposure vs 6.3 V class floor | — | **LOCKED** |
| C42 | 4.7 µF, 0603 (SET capacitor, +VA) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN: stands at VOUT 4.6 V vs 6.3 V class floor | 4.7 µF is the datasheet's typical CSET value | **LOCKED** |
| C43 | 4.7 µF, 0603 (PGFB capacitor, +VA) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN: ≤5.25 V exposure vs 6.3 V class floor | PGFB network for U13 | **LOCKED** |
| C44 | 4.7 µF, 0603 (IN bypass, +3V3A) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN: 5.25 V max vs 6.3 V class floor | — | **LOCKED** |
| C45 | 4.7 µF, 0603 (SET capacitor, +3V3A) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN: stands at 3.32 V vs 6.3 V class floor | Datasheet-typical CSET value | **LOCKED** |
| C46 | 4.7 µF, 0603 (PGFB capacitor, +3V3A) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN: ≤5.25 V exposure vs 6.3 V class floor | PGFB network for U14 | **LOCKED** |
| C47 | 100 nF, 0603 (MCU decoupling) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| C48 | 100 nF, 0603 (MCU decoupling) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| C49 | 4.7 µF, 0603 (+3V3A bulk at MCU) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN: 3.32 V vs 6.3 V class floor | — | **LOCKED** |
| C50 | 100 nF, 0603 (CDR decoupling) | stock chip pattern — MATCH (package class) (board: `C_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| C51 | 10 µF, 0805 (CDR bulk) | C_0805 stock — MATCH (package class) (board: `C_0805_2012Metric`) | WITHIN: 3.3 V vs 6.3 V class floor | — | **LOCKED** |
| D1 | Excelitas C30737LH-500-90, LCC-6 (primary detector) | pdlvds:C30737LH_LCC6 (custom) — UNVERIFIED: datasheet land pattern is graphical (Fig. 10); pad-for-pad comparison not completable (docs/07). Board pads measured: 1.3×0.6 mm, columns ±0.85 mm, rows −1.1/0/+1.1 mm — consistent with MANIFEST's extracted package parameters, no further (board: `C30737LH_LCC6`) | **EXCEEDS**: VBR 180 typ / 260 max V (datasheet Table 1) vs rail ceiling ≈420 V with no hardware bound — F-01, docs/07 (OPEN, owner decision) | Shares the unbounded rail with the D2 population; missing OVP clamp/interlock = F-02 | **NOT LOCKED** |
| D2 | Hamamatsu S8664-20K (DNP alternate), TO-5 can | pdlvds:S8664_TO5 (custom) — MATCH: pads (+2.54,0)/(−2.54,0)/(0,+2.54) mm = datasheet φ5.08 mm pin circle; lead identity verified from datasheet p.4 drawing (MANIFEST Stage-7b) (board: `S8664_TO5`) | **EXCEEDS (conditional)**: VBR typ 400 / max 500 V (datasheet table) vs the same unbounded 420 V ceiling — the F-01 family in milder form; DNP, binds only if this population is fitted | Its ≈400 V Vbr is the reason the rail reaches 420 V (docs/02) | **NOT LOCKED** |
| D3 | ST USBLC6-2SC6, SOT-23-6 | SOT-23-6 stock — MATCH (ST DS4260 pinout verified pin-for-pin: 1 I/O1, 2 GND, 3 I/O2, 4 I/O2p, 5 VBUS, 6 I/O1p) (board: `SOT-23-6`) | WITHIN: VRWM 5.25 V — leakage is specified at exactly the rail's 5.25 V max (150 nA max); VBR 6 V | COMPATIBLE: Ci/o 2.5 typ/3.5 max pF is the USB 2.0 HS protection class; protects DP/DM + VBUS as designed (R11) | **LOCKED** |
| D4 | SMBJ5.0A TVS (JEDEC DO-214AA / SMB) | **MISMATCH**: fitted footprint is D_SMA = DO-214AC (SMA), a narrower body than the part's DO-214AA — the part will not land correctly on these pads. Lock = footprint → D_SMB, or part → SMAJ5.0A (DO-214AC) — F-05 (board: `D_SMA`) | WITHIN on voltage: VRWM 5.0 V, VBR 6.40–7.00 V, VC 9.2 V @ 65.3 A, 600 W (SMBJ series data, Littelfuse/Vishay/Bourns agree) vs the 5.0–5.25 V rail. Note: the 9.2 V clamp level vs U7's VBUS-pin abs max 5.5 V — surge coordination UNVERIFIED (D3 is the connector-side device) | Rail surge protection behind F1 | **NOT LOCKED** |
| D5 | ES1J ultrafast rectifier, SMA (DO-214AC) | D_SMA stock — MATCH (DO-214AC is this part's package) (board: `D_SMA`) | WITHIN: VRRM 600 V vs 420 V + ringing (1.43× margin); IF(AV) 1 A vs µA load + capacitor-charge pulses; trr 35 ns at 250 kHz | Secondary rectifier into C32/HV_RAW | **LOCKED** |
| D6 | Green LED, 0603 (PWR) | LED_0603 stock — MATCH (package class) (board: `LED_0603_1608Metric`) | WITHIN: ≈1.3 mA via R44 from +3V3D | Power indicator | **LOCKED** |
| D7 | Green LED, 0603 (STAT) | LED_0603 stock — MATCH (package class) (board: `LED_0603_1608Metric`) | WITHIN: ≈1.3 mA via R45 from MCU PC9 | Status indicator | **LOCKED** |
| D8 | BIST source LED, 1206 — **wavelength in dispute, no part number** | LED_1206 stock — MATCH (package class) (board: `LED_1206_3216Metric`) | **UNVERIFIED**: circuit.py and CONNECTIONS.md call it a **740 nm** source; docs/02 and docs/04 (bring-up step 10) call it **630 nm**. No manufacturer part number exists in any source, so there is nothing to rate. Drive is fine either way (R46 100 Ω from +3V3D, MCU PC8 sinks ≈14–20 mA class). Lock = choose the wavelength, name the part (the paper's two emitters are the documented candidates), correct the losing documents — F-13 | The BIST self-test's expected photocurrent at D1 depends on which wavelength is actually fitted (D1 responds to both, differently) | **NOT LOCKED** |
| F1 | PTC fuse 1.1 A hold, 1812 | Fuse_1812 stock — MATCH (package class) (board: `Fuse_1812_4532Metric`) | WITHIN: hold 1.1 A vs worst-case board draw 0.72 A (docs/03); 1812 PTC class voltage rating ≥8 V vs 5.25 V | Front of the +5V tree | **LOCKED** |
| FB1 | 600 Ω@100 MHz ferrite, 0805 (+3V3D→+3V3D_CDR) | stock chip pattern — MATCH (package class) (board: `L_0805_2012Metric`) | **UNVERIFIED**: carries the ADN2813's 155 mA max (docs/03); no manufacturer part or rated current exists in any project source — lock = specify a ferrite rated ≥500 mA | Rail filter for the CDR island | **NOT LOCKED** |
| FB2 | 600 Ω@100 MHz ferrite, 0805 (−VA filter) | stock chip pattern — MATCH (package class) (board: `L_0805_2012Metric`) | **UNVERIFIED**: carries the OPA657's V− current (14.5 mA, docs/03); no manufacturer part or rated current in any project source. Lock = name a ≥200 mA-rated 0805 ferrite — F-10 | Turns NEG_RAW (−5.5 V) into −VA (≈−5.4 V at load) | **NOT LOCKED** |
| J1 | Amphenol 12401610E4#2A USB-C receptacle (identity carried by the footprint; circuit.py value is generic — amend it to the MPN) | USB_C_Receptacle_Amphenol_12401610E4-2A — MATCH (manufacturer-named library model) (board: `USB_C_Receptacle_Amphenol_12401610E4-2A`) | WITHIN: contact current rating 5 A, voltage rating 100 V (Amphenol product specification) vs demand ≤1.1 A (PTC-limited) at 5 V | COMPATIBLE: UFP sink with R18/R19 Rd fitted (R11) | **LOCKED** |
| J2 | Pin header 2×3, 2.54 mm (LVDS out) | PinHeader_2x03_P2.54 stock — MATCH (generic) (board: `PinHeader_2x03_P2.54mm_Vertical`) | WITHIN: carries LVDS pairs + GND at ≤1.4 V | External LVDS data/clock pairs (R4) | **LOCKED** |
| J3 | SMA test input (Amphenol 132134 vertical) | SMA_Amphenol_132134_Vertical — MATCH (manufacturer-named library model; identity carried by the footprint, circuit.py value is generic) (board: `SMA_Amphenol_132134_Vertical`) | WITHIN: 50 Ω RF connector; demand is bench signal injection | Parallel electrical injection path for docs/05 tests | **LOCKED** |
| J4 | Pin header 2×5, 1.27 mm (SWD) | PinHeader_2x05_P1.27 stock — MATCH (generic) (board: `PinHeader_2x05_P1.27mm_Vertical`) | WITHIN: 3.3 V logic | Rescue programming path (R7) | **LOCKED** |
| L1 | 2.2 µH inductor, 0805 — **no manufacturer part number** | stock chip pattern — MATCH (package class) (board: `L_0805_2012Metric`) | **UNVERIFIED**: no saturation-current specification exists in the project. Demand at the documented load is modest (≈0.58 A peak: 0.48 A budget + ≈0.2 A ripple at 2.5 MHz), provable by a *specified* 0805 part — but U11's switch limit (≈3 A class) would saturate an arbitrary 0805 under fault/startup. Lock = name a part with Isat ≥1.5 A — F-10 | U11 power stage (2.2 µH is the datasheet's typical value) | **NOT LOCKED** |
| L2 | 2.2 µH inductor, 0805 — **no manufacturer part number** | stock chip pattern — MATCH (package class) (board: `L_0805_2012Metric`) | **UNVERIFIED**: as L1 (identity/rating paperwork); demand here is small — the inverting stage feeds a 15 mA rail — but no Isat spec exists. Same lock action as L1 — F-10 | U12 power stage | **NOT LOCKED** |
| MH1 | Mounting hole 3.2 mm (M3) | MountingHole_3.2mm_M3 stock — MATCH (mechanical) (board: `MountingHole_3.2mm_M3`) | WITHIN: GND-connected by design | Board corner | **LOCKED** |
| MH2 | Mounting hole 3.2 mm (M3) | MountingHole_3.2mm_M3 stock — MATCH (mechanical) (board: `MountingHole_3.2mm_M3`) | WITHIN: GND-connected by design | Board corner | **LOCKED** |
| MH3 | Mounting hole 3.2 mm (M3) | MountingHole_3.2mm_M3 stock — MATCH (mechanical) (board: `MountingHole_3.2mm_M3`) | WITHIN: GND-connected by design | Board corner | **LOCKED** |
| MH4 | Mounting hole 3.2 mm (M3) | MountingHole_3.2mm_M3 stock — MATCH (mechanical) (board: `MountingHole_3.2mm_M3`) | WITHIN: GND-connected by design | Board corner | **LOCKED** |
| MH5 | Mounting hole 2.7 mm (M2.5, lens holder) | MountingHole_2.7mm_M2.5 stock — MATCH (mechanical) (board: `MountingHole_2.7mm_M2.5`) | WITHIN: unconnected by design | Lens standoff flanking D1 (docs/02 optics) | **LOCKED** |
| MH6 | Mounting hole 2.7 mm (M2.5, lens holder) | MountingHole_2.7mm_M2.5 stock — MATCH (mechanical) (board: `MountingHole_2.7mm_M2.5`) | WITHIN: unconnected by design | Lens standoff flanking D1 | **LOCKED** |
| Q1 | Infineon IRLML0030, SOT-23 (Micro3) | SOT-23 stock — MATCH (JEDEC TO-236; pinout G/S/D as wired) (board: `SOT-23`) | **EXCEEDS (marginal, unclamped)**: VDSS 30 V (PD-96278B) vs off-state drain stress = VIN 5 V + reflected (420 + VF)/20 ≈ 26.1 V = 87% of rating *before* any leakage-inductance spike — and no RCD/TVS clamp parts exist anywhere in the design. Current is fine: ID 5.3 A vs ≤ ≈2–3 A peak class; RDS(on) max 40 mΩ @ VGS 4.5 V, gate driven at 7.2 V. Lock = fit a ≥60 V SOT-23 MOSFET of similar Qg/RDS(on), or add a primary clamp and prove the spike ≤24 V (80% derating) — F-12 | Switched by U10 via R27; source sense via R28 | **NOT LOCKED** |
| R1 | 3.3 kΩ, 0603 (TIA feedback) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN: sees TIA output swing ≤ ≈3.5 V, µW dissipation | Sets Rf with C1 (link-budget design point) | **LOCKED** |
| R2 | 1 kΩ, 0603 | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Post-amp input network | **LOCKED** |
| R3 | 806 Ω, 0603 | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Gain set with R4: 1+806/200 = 5.03 (docs/02) | **LOCKED** |
| R4 | 200 Ω, 0603 | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Gain set with R3 | **LOCKED** |
| R5 | 10 kΩ, 0603 (VMID divider) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | VMID = +VA/2 ≈ 2.3 V with R6 | **LOCKED** |
| R6 | 10 kΩ, 0603 (VMID divider) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | VMID = +VA/2 ≈ 2.3 V with R5 | **LOCKED** |
| R7 | 0 Ω link, 0603 (fitted — direct path) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (carries CMP_IN signal only) | Fit exactly one of R7/R8 (CONNECTIONS; docs/04 R-10) | **LOCKED** |
| R8 | 0 Ω link, 0603 (DNP — post-amp path) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (no demand while DNP) | Fit exactly one of R7/R8 | **LOCKED** |
| R9 | 100 kΩ, 0603 (hysteresis feedback) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Sets ≈8 mV hysteresis around U3 (docs/02) | **LOCKED** |
| R10 | 1 kΩ, 0603 (baseline network) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Feeds THR_FILT with C11 | **LOCKED** |
| R11 | 49.9 Ω, 0603 (DNP) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | No demand while DNP | Optional J3 termination | **LOCKED** |
| R12 | 10 kΩ, 0603 (THRADJ) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Sets LOS trip mid-range (datasheet: 0 Ω → 16.5 mV, 100 kΩ → 3.5 mV); docs/04 R-13's '0 Ω' text is stale vs circuit.py | **LOCKED** |
| R13 | 100 Ω, 0603 (LVDS termination) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | 100 Ω = TIA/EIA-644 termination at U5 ch1 (R4) | **LOCKED** |
| R14 | 100 Ω, 0603 (LVDS termination) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | 100 Ω termination at U5 ch2 | **LOCKED** |
| R15 | 10 kΩ, 0603 (NRST pull-up) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| R16 | 10 kΩ, 0603 (BOOT0 pull-down) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | ROM DFU entry path (R7 requirement) | **LOCKED** |
| R17 | 12 kΩ 1%, 0603 (RBIAS) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Datasheet-exact value for USB3300 RBIAS (12 kΩ ±1% to GND) | **LOCKED** |
| R18 | 5.1 kΩ, 0603 (CC1 Rd) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | 5.1 kΩ Rd = USB-C UFP advertisement value | **LOCKED** |
| R19 | 5.1 kΩ, 0603 (CC2 Rd) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | As R18 | **LOCKED** |
| R20 | 4.7 kΩ, 0603 (I2C pull-up SCL) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Bus pull-up; bus = U4 (≤400 kHz) + U9 on 3.3 V | **LOCKED** |
| R21 | 4.7 kΩ, 0603 (I2C pull-up SDA) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | As R20 | **LOCKED** |
| R22 | 10 kΩ, 0603 (TMP117 ALERT pull-up) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Verified as a pull-up to +3V3D (circuit.py line 205) — the open-drain ALERT is correctly terminated | **LOCKED** |
| R23 | 10 kΩ, 0603 (VC compensation) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | LT3757 VC network with C29 | **LOCKED** |
| R24 | 24.9 kΩ, 0603 (RT — sets switching frequency) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | **UNVERIFIED function**: its value is claimed to give 250 kHz from the LT3757 RT table — one of F-07's three truncated numbers. The resistor itself is a standard part; the lock action is the same single datasheet read as U10 | **NOT LOCKED** |
| R25 | 100 kΩ, 0603 (SHDN divider top) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN: ≤3.8 V across it | Divider with R26 delivers ≈1.24 V vs the 1.22 V threshold (docs/03; risk docs/04 R-8) | **LOCKED** |
| R26 | 33 kΩ, 0603 (SHDN divider bottom) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN: ≈1.24 V across it | MCU PC7 pulls this node down to disable HV (docs/06) | **LOCKED** |
| R27 | Gate series resistor — **value in dispute** | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | The part class is fine either way; the *value* is the failure | **CONFLICT between the two authoritative sources**: CONNECTIONS.md says GATE → R27 **10 Ω** → Q1; circuit.py (which generates the board) fits **10 kΩ**. At 250 kHz (4 µs period) with Q1's gate charge 2.6 nC, a 10 kΩ series resistor cannot slew the gate — the as-generated value is functionally incompatible with the converter's own switching demand. Lock = resolve the conflict (10 Ω class is the conventional intent) and regenerate — F-12 | **NOT LOCKED** |
| R28 | 0.05 Ω, 1206 (primary current sense) | stock chip pattern — MATCH (package class) (board: `R_1206_3216Metric`) | WITHIN: steady-state HV load is µA-class; the peak is set by U10's current limit — for any threshold in the part's plausible class (≤150 mV → ≤3 A) pulse power ≤0.45 W at low duty in a pulse-rated 1206 position. (The exact threshold is F-07-unverified; no plausible value stresses this part) | SENSE node to U10 pin 6 | **LOCKED** |
| R29 | '10k HV', 1206 (post-filter series) | stock chip pattern — MATCH (package class) (board: `R_1206_3216Metric`) | **EXCEEDS under fault**: steady-state drop is ≈1 V (computed from K-node currents), but the part sits in series in the 420 V chain — a C33/APD short puts the full rail across a standard 1206 (200 V class max working voltage). Its own value string says 'HV' yet no HV-rated part is specified. Lock = ≥500 V-class 1206 or two series 1206 — F-06 | Filter with C33 (10 kΩ/100 nF) | **NOT LOCKED** |
| R30 | 4.7 MΩ bleeder, 1206 | stock chip pattern — MATCH (package class) (board: `R_1206_3216Metric`) | **EXCEEDS (continuous)**: the full APD_K voltage (up to ≈420 V) stands across this single standard 1206 (200 V class) whenever HV is on. Power is fine (37 mW) — voltage is the failure. Lock = two series 1206 (2× 2.35 MΩ keeps the 4.7 MΩ total and the <10 s bleeder spec, docs/03) or a ≥500 V-rated part — F-06 | R9 bleeder: 420 V → <60 V in ≈0.9 s (docs/03) | **NOT LOCKED** |
| R31 | 7.68 MΩ divider top, 1206 | stock chip pattern — MATCH (package class) (board: `R_1206_3216Metric`) | **EXCEEDS (continuous)**: divider current 420/(7.68 MΩ + 49.9 kΩ) ≈ 54 µA puts ≈418 V across this single standard 1206 (200 V class). Lock = split the top leg into a series string (e.g. 3× 2.56 MΩ) or an HV-rated part; the ratio — and thus the set-point math — is unchanged — F-06 | Divider with R32 + DAC injection R33 sets V_FBX (docs/03) | **NOT LOCKED** |
| R32 | 49.9 kΩ, 0603 (divider bottom) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN: stands at V_FBX ≈1.6 V | With R31/R33 | **LOCKED** |
| R33 | 71.5 kΩ, 0603 (DAC injection) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN: between HV_DAC (≤2.5 V) and HV_FBX (1.6 V) | Couples U8 VOUTB into the HV servo (docs/03 map) | **LOCKED** |
| R34 | '10M HV probe', 1206 | stock chip pattern — MATCH (package class) (board: `R_1206_3216Metric`) | **EXCEEDS (continuous)**: with TP1 unloaded (normal operation) essentially the full ≈420 V stands across this single standard 1206 (200 V class). Lock = series string or HV-rated part, as R30 — F-06 | Feeds the TP1 HV test point | **NOT LOCKED** |
| R35 | 312 kΩ, 0603 (FB divider top) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Sets +3V3D with R36 (verified in U11 row) | **LOCKED** |
| R36 | 100 kΩ, 0603 (FB divider bottom) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | With R35 | **LOCKED** |
| R37 | 10 kΩ, 0603 (PG pull-up) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | PG_3V3 to MCU PB9 | **LOCKED** |
| R38 | 587 kΩ, 0603 (inverting FB top, to system GND) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN: ≈4.7 V across it, µW | Sets −VA with R39 (verified in U12 row) | **LOCKED** |
| R39 | 100 kΩ, 0603 (inverting FB bottom, to NEG_RAW) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | With R38 | **LOCKED** |
| R40 | 46 kΩ, 0603 (SET, +VA) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | 100 µA × 46 kΩ = 4.60 V — ISET verified from the datasheet (99–101 µA) | **LOCKED** |
| R41 | 1 kΩ, 0603 (ILIM, +VA) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Sets the 125 mA limit (see U13) | **LOCKED** |
| R42 | 33.2 kΩ, 0603 (SET, +3V3A) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | 100 µA × 33.2 kΩ = 3.32 V | **LOCKED** |
| R43 | 1 kΩ, 0603 (ILIM, +3V3A) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Sets the 125 mA limit (see U14) | **LOCKED** |
| R44 | 1 kΩ, 0603 (D6 ballast) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| R45 | 1 kΩ, 0603 (D7 ballast) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | — | **LOCKED** |
| R46 | 100 Ω, 0603 (D8 ballast) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | WITHIN (LV class demand, docs/03 rails) | Sets D8 pulse current (docs/04 step 10) | **LOCKED** |
| RJ1 | 0 Ω link, 0603 (DNP) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | No demand while DNP; fitted state carries APD bias µA — WITHIN | Bridges D2 anode pads to APD_A; fit only with D2 | **LOCKED** |
| RJ2 | 0 Ω link, 0603 (DNP) | stock chip pattern — MATCH (package class) (board: `R_0603_1608Metric`) | No demand while DNP; fitted state carries APD bias µA — WITHIN | Bridges D2 cathode pads to APD_K; fit only with D2 | **LOCKED** |
| SH1 | RF shield can — **no manufacturer part named** | pdlvds:SHIELD_CAN_26x20 (custom; 4 pads 2.4×2.4 mm at (±12, ±9) mm) — **UNVERIFIED**: no production can is identified, so wall fit and height over the AFE stack (U1 SOIC + passives) are unprovable. Lock = name a production 26×20-class can and verify its footprint + height ≥ the tallest part under it — F-13 (board: `SHIELD_CAN_26x20`) | Mechanical/EMI part (R10: shield over the analogue frontend for the 6.63 MHz QSCR environment) | Covers D1/U1/U2/U3 island | **NOT LOCKED** |
| T1 | 'Flyback xfmr 1:20' — **no manufacturer, no part number, in any project source** | pdlvds:XFMR_FLYBACK_6P (custom; pads ±3.5 mm columns, 2.54 mm pitch, 2.0×1.4 mm) — **UNVERIFIED by construction**: matches no identified production transformer (board: `XFMR_FLYBACK_6P`) | **UNVERIFIED**: design intent exists only as simulation parameters (sim/hv_design.py: N=20, Lp=47 µH, 250 kHz). Saturation current, leakage inductance, and winding voltage withstand of any real part are unprovable; docs/02 even describes a '1:10' transformer — the sources disagree on the part class. Lock = specify a production flyback transformer (or a controlled custom-wind spec) with Lp ≈47 µH, Isat above the LT3757 current-limit peak, and insulation for the reflected 420 V secondary, on a footprint drawn from its datasheet — F-10 | Couples U10/Q1 primary to the D5/C32 secondary | **NOT LOCKED** |
| TP1 | Test point pad 1.5 mm (HV probe) | TestPoint_Pad_D1.5mm stock — MATCH (mechanical) (board: `TestPoint_Pad_D1.5mm`) | WITHIN as a pad; its exposure path is R34's row | HV measurement point (docs/05 §5) | **LOCKED** |
| TP2 | Test point pad 1.5 mm (DBG_TX) | TestPoint_Pad_D1.5mm stock — MATCH (mechanical) (board: `TestPoint_Pad_D1.5mm`) | WITHIN: 3.3 V logic | — | **LOCKED** |
| TP3 | Test point pad 1.5 mm (DBG_RX) | TestPoint_Pad_D1.5mm stock — MATCH (mechanical) (board: `TestPoint_Pad_D1.5mm`) | WITHIN: 3.3 V logic | — | **LOCKED** |
| U1 | TI OPA657N (OPA657), SOIC-8 | SOIC-8 stock — MATCH (datasheet D package 4.90×3.91 mm; pinout per MANIFEST) (board: `SOIC-8_3.9x4.9mm_P1.27mm`) | WITHIN: demand is a *total* supply of 4.6−(−5.4) = 10.0 V; the datasheet specifies supply as a total — recommended VS 8/10/12 V, abs max ±6.5 V bipolar (13 V). docs/03's asymmetric-rail claim verified against SBOS197 §7.1/§7.3 | COMPATIBLE: +IN at GND = TIA virtual ground; APD reverse bias appears across D1 as designed | **LOCKED** |
| U2 | TI THS4304DBV, SOT-23-5 | SOT-23-5 stock — MATCH (DBV pinout per MANIFEST) (board: `SOT-23-5`) | WITHIN: single-supply range 2.7–5.0 V vs +VA 4.6 V; abs max VS +6.0 V | COMPATIBLE: VMID bias 2.3 V inside its input CM range; output CM 2.3 V inside U3's −0.2..+2.6 V window (0.3 V headroom) | **LOCKED** |
| U3 | TI LMH7220MK, TSOT-23-6 | TSOT-23-6 stock — MATCH (pinout per MANIFEST; TSOT-6 has no hysteresis pin — external R9 network per docs/02 deviation 3) (board: `TSOT-23-6`) | WITHIN: supply range 2.7–12 V vs +VA 4.6 V; abs max VCC−GND 13.5 V | COMPATIBLE at the design point: LVDS out VOD 250–400 mV / VOS 1125–1325 mV (TIA/EIA-644, meets R4) into U4's AC-coupled inputs. Input window −0.2..VCC−2 = −0.2..+2.6 V at VCC 4.6 V contains both idle points (0 V direct, 2.3 V post-amp); note the R3 overload swing can drive IN+ below −0.2 V — already open as docs/04 R-1 | **LOCKED** |
| U4 | Analog Devices ADN2813ACPZ, LFCSP-32 | QFN-32-1EP_5x5mm_P0.5_EP3.1x3.1 — MATCH: datasheet outline 5.00 SQ body, 0.50 BSC pitch, exposed pad 3.10 SQ (2.95–3.25) = footprint EP 3.1×3.1 mm (board: `QFN-32-1EP_5x5mm_P0.5mm_EP3.1x3.1mm`) | WITHIN: VCC 3.0/3.3/3.6 V vs +3V3D_CDR ≈3.3 V; current 139 typ/155 max mA in the docs/03 budget | COMPATIBLE ×4: data rate 10–1250 Mb/s covers the 16 Mbaud Manchester chip stream and 50 Mb/s 8b/10b (R6); REFCLK 25 MHz inside 10–160 MHz, single-ended drive datasheet-sanctioned; inputs accept U3's 250–400 mV diff (sensitivity 3.3 mV pp, max diff 2.0 V, internal 100 Ω); LVDS outputs match U5. I2C 0x40 (SADDR5=GND) distinct from U9's 0x48. Note: docs/04 R-13 says THRADJ 'fitted at 0 Ω' — circuit.py (authoritative) fits 10 kΩ (R12) | **LOCKED** |
| U5 | TI SN65LVDS32D, SOIC-16 | SOIC-16 stock — MATCH (datasheet D package 9.90×3.91 mm; pin table verified pin-for-pin incl. G/G̅ enables; unused ch3/4 inputs parked on rails, outputs NC) (board: `SOIC-16_3.9x9.9mm_P1.27mm`) | WITHIN: single 3.3 V supply vs 3.296 V rail; abs max VCC 4 V | COMPATIBLE: input thresholds ±100 mV max vs ADN2813's 250–400 mV drive; rated 100 Mb/s ≥ 50 Mb/s design and 16 Mbaud; LVTTL outputs feed MCU 3.3 V inputs | **LOCKED** |
| U6 | ST STM32H723ZGT6, LQFP-144 | LQFP-144_20x20mm_P0.5 stock — MATCH at package level (JEDEC LQFP-144); pin name→number map provenance = installed KiCad symbol library, cross-checked against ST community + mbed tables (MANIFEST Stage-7 addendum) — not the ST datasheet (board: `LQFP-144_20x20mm_P0.5mm`) | **UNVERIFIED in part**: VDD/VDDA ranges and the VCAP capacitor requirement rest on DS13313, unreachable from this environment (project-recorded block, MANIFEST; this audit's fetch failed identically). Design runs VDD 3.296 V / VDDA 3.32 V, the family's nominal 3.3 V point — F-08 | COMPATIBLE: ULPI — U7 sources the 60 MHz clock, the MCU's OTG-HS ULPI consumes it (direction correct); PC2_C/PC3_C analog-switch closure is firmware bring-up (docs/04 R-6), not a part conflict; no HSE fitted, by design | **NOT LOCKED** |
| U7 | Microchip USB3300-EZK, QFN-32 | QFN-32-1EP_5x5mm_P0.5_EP3.1x3.1 — MATCH at package level (datasheet: 32-pin QFN 5×5 mm, 0.5 mm pitch, EP = main GND, wired to GND) (board: `QFN-32-1EP_5x5mm_P0.5mm_EP3.1x3.1mm`) | WITHIN: VDD3.3 3.0/3.3/3.6 V vs +3V3A 3.32 V; VBUS pin max 5.5 V vs ≤5.25 V; −40..+85 °C | COMPATIBLE: sources 60 MHz CLKOUT to the MCU ULPI; RBIAS 12 kΩ 1% is the datasheet value (R17); REG_EN at +3V3A enables internal regulators (PHY_1V8 is its output, C22/C23 per datasheet); ID=GND is the device-mode strap — bring-up check docs/04 R-7, not a rating conflict | **LOCKED** |
| U8 | TI DAC8562SDGS, VSSOP-10 | VSSOP-10_3x3mm_P0.5 stock — MATCH (DGS package; pinout per MANIFEST) (board: `VSSOP-10_3x3mm_P0.5mm`) | WITHIN: AVDD 2.7–5.5 V vs +3V3D 3.296 V; outputs used 0–2.5 V ≤ AVDD | COMPATIBLE: SPI ≤50 MHz, logic domain = AVDD = MCU's 3.3 V; POR zero-scale output is the documented HV-demand interaction, sequenced by SHDN (docs/03, docs/04 R-8) — a system note, not a part defect | **LOCKED** |
| U9 | TI TMP117NAI, WSON-6 (DRV) | **MISMATCH — measured from the board file**: pads 1–6 overlap the exposed pad (pad 7, GND) by 0.20 mm in X (signal pads span to 0.30 mm of centre; the EP spans to 0.50 mm) — on copper, all six pins short to the grounded thermal pad. The footprint is the only intra-footprint overlap on the board. Geometry also disagrees with TI's DRV0006B land-pattern callouts (datasheet: pads 0.45×0.30 mm, 0.65-class pitch callouts, (1.95) span) vs the footprint's 0.50 mm pitch, ±0.575 mm columns, 0.55×0.28 mm pads. Lock = redraw from DRV0006B and re-verify — F-04 (board: `TMP117_WSON6`) | WITHIN: V+ 1.8–5.5 V vs +3V3A 3.32 V; ±0.1 °C grade serves the APD tempco compensation (R9) | COMPATIBLE: I2C 0x48 (ADD0=GND) distinct from U4's 0x40; ALERT is open-drain and its pull-up is fitted (R22 → +3V3D) | **NOT LOCKED** |
| U10 | Analog Devices (Linear Technology) LT3757EMSE, MSOP-10E | MSOP-10-1EP_3x3mm_P0.5_EP1.68x1.88 stock — MATCH at package level (MSE pin functions cross-verified from two independent datasheet copies, MANIFEST; EP = GND, wired) (board: `MSOP-10-1EP_3x3mm_P0.5mm_EP1.68x1.88mm`) | WITHIN where verified: VIN 2.9–40 V vs 5 V; INTVCC 7.2 V internal regulator; SHDN/UVLO 1.22 V falling threshold vs divider 1.24 V (marginal by design — docs/04 R-8). **UNVERIFIED**: the FBX reference (taken as 1.6 V), the RT value for 250 kHz, and the SENSE current-limit threshold — truncated in both project datasheet copies and this audit's analog.com fetch failed. The FBX number sets the whole DAC→voltage map including the ≈420 V ceiling — F-07 | Gate drive INTVCC 7.2 V is inside Q1's VGS ±20 V and above its 4.5 V RDS(on) test point — levels COMPATIBLE (the series resistor is R27's finding) | **NOT LOCKED** |
| U11 | TI TPS62130RGT, QFN-16 (VQFN RGT) | QFN-16-1EP_3x3mm_P0.5_EP1.45x1.45 — MATCH at package level (datasheet RGT 3×3 mm; pinout per SLVSAG7 Table 6-1 as wired) (board: `QFN-16-1EP_3x3mm_P0.5mm_EP1.45x1.45mm`) | WITHIN: VIN range 3–17 V vs 5 V; output capability 3 A vs 0.48 A documented budget (docs/03); EN tied to VIN (abs max VIN+0.3 — at the pin's own rail, legal) | COMPATIBLE: VFB 0.8 V × (1 + 312k/100k) = 3.296 V set point verified against the datasheet reference | **LOCKED** |
| U12 | TI TPS62130RGT, QFN-16 (inverting −VA) | QFN-16-1EP_3x3mm_P0.5_EP1.45x1.45 — MATCH at package level (as U11) (board: `QFN-16-1EP_3x3mm_P0.5mm_EP1.45x1.45mm`) | WITHIN — verified pin-by-pin against SLVSAG7 §7.1 referred to the IC's own ground (NEG_RAW, −5.5 V): AVIN/PVIN sit at 10.5 V rel. ground ≤ 20 V; FB at 0.8 V, VOS/FSW/DEF at 0 V rel. ground ≤ 7 V; SS/TR ≤ VIN+0.3; PG left NC by design (docs/04 R-11) | COMPATIBLE: topology is the datasheet's §10.3.3 inverting circuit (MANIFEST); EN is tied to the +5 V system rail, which is exactly VIN potential referred to IC ground — inside its VIN+0.3 rating (the classic inverting-buck trap, checked and clear). Set point: 0.8 × (587+100)/100 = 5.496 V ≈ −5.5 V raw, ≈−5.4 V after FB2 (docs/03) | **LOCKED** |
| U13 | Analog Devices LT3042EDD, DFN-10 (+VA LDO) | DFN-10-1EP_3x3mm_P0.5_EP1.55x2.48 — MATCH at package level (datasheet DD 3×3 mm DFN-10, EP = GND pin 11, wired) (board: `DFN-10-1EP_3x3mm_P0.5mm_EP1.55x2.48mm`) | WITHIN on range and current: IN 1.8–20 V vs 5 V; ISET 99/100/101 µA verified → +VA = 100 µA × 46 kΩ = 4.6 V; ILIM (R41 1 kΩ) 125 mA per MANIFEST's scale vs 38 mA load (passes at 100 mA under the alternate scale reading too); PGFB tied to IN is inside its −0.3..22 V pin rating; COUT 22 µF ≥ 4.7 µF minimum. **UNVERIFIED: dropout margin** — docs/03 asserts ≈60 mV typ at 40 mA so regulation holds to VBUS ≈4.7 V, but the Rev. C datasheet read in this audit brackets dropout at 220–350 mV over 50–200 mA (350 mV typ @ 200 mA is the headline figure) and the 40 mA point could not be confirmed from the extracted table. Worst-case headroom is 4.75 − 4.6 = 150 mV: if true dropout at 38 mA exceeds it, +VA sags at low VBUS (graceful — U1's total supply stays ≥ its 8 V minimum — but +VA leaves its set point). Lock = confirm dropout at 38 mA from the datasheet curve, or lower the +VA set point / record the sag as accepted — F-11 | Feeds U1/U2/U3 (the analogue island) | **NOT LOCKED** |
| U14 | Analog Devices LT3042EDD, DFN-10 (+3V3A LDO) | DFN-10-1EP_3x3mm_P0.5_EP1.55x2.48 — MATCH at package level (as U13) (board: `DFN-10-1EP_3x3mm_P0.5mm_EP1.55x2.48mm`) | WITHIN: as U13 (IN range, ISET → 3.32 V via R42 33.2 kΩ — also the datasheet's own typical-application value; ILIM 125 mA vs 80 mA load); dropout is a non-issue here: headroom 4.75 − 3.32 = 1.43 V ≫ dropout under any reading | Feeds U7, U9, MCU VDDA (docs/03 budget ≈80 mA) | **LOCKED** |
| X1 | 24 MHz crystal, 3225 — **no manufacturer part number** | Crystal_SMD_3225-4Pin stock — MATCH by package class (board: `Crystal_SMD_3225-4Pin_3.2x2.5mm`) | **UNVERIFIED**: USB3300 Table 5-8 demands a fundamental parallel-resonant crystal, CL 20 pF typ, ESR ≤30 Ω, ±500 ppm total budget; with no MPN the fitted crystal's CL/ESR are unprovable — and this is the PHY's only clock source (no fallback) — F-09 | Load network C20/C21 realizes ≈14–16 pF (18 pF series pair + 3 pF/pin XI/XO capacitance + strays) vs the 20 pF spec point; estimated pull is tens of ppm, inside the ±500 ppm budget — COMPATIBLE on accuracy, but crystal + caps lock only as a specified set | **NOT LOCKED** |
| X2 | '25MHz OSC' — Abracon ASE family implied by the footprint, **no full part number** | Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5 — MATCH (the family's 3.2×2.5 pattern) (board: `Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm`) | **UNVERIFIED**: the ASE family is ordered with a supply-voltage option (3.3 V standard; 1.8/2.5 V variants exist across the family) — an unnamed part could be a wrong-voltage variant that either fails to start at 3.3 V or is over-voltaged by it. Lock = specify the full 3.3 V CMOS ordering code — F-09 | COMPATIBLE on interface: pinout as wired matches Abracon's table (1 OE, 2 GND, 3 OUT, 4 Vdd); 25 MHz inside U4's REFCLK range 10–160 MHz; CMOS output into REFCLKP with REFCLKN AC-coupled is datasheet-sanctioned single-ended drive | **NOT LOCKED** |

## Land-pattern verification status (the UNVERIFIED list)

- **UNVERIFIED — no manufacturer pattern could be checked:**
  - **D1** (pdlvds:C30737LH_LCC6) — datasheet land pattern is a
    graphical figure; pad-for-pad comparison not completable from
    reachable sources (docs/07). Board pads (1.3×0.6 mm, columns
    ±0.85 mm, rows −1.1/0/+1.1 mm, measured this audit) are consistent
    with the package parameters extracted in MANIFEST, no further.
  - **T1** (pdlvds:XFMR_FLYBACK_6P) — no manufacturer part exists in
    any source, so there is no pattern to check against.
  - **SH1** (pdlvds:SHIELD_CAN_26x20) — no production can named.
- **MISMATCH — checked and wrong:** **U9** TMP117_WSON6 (pads 1–6
  overlap the EP by 0.20 mm; pitch/columns/pads inconsistent with TI
  DRV0006B callouts) and **D4** on D_SMA (DO-214AC pattern; the part
  is DO-214AA).
- **MATCH at pad level:** D2 S8664_TO5 (datasheet pin circle
  φ5.08 mm, Stage-7b correction re-measured this audit); U4/U7 QFN-32
  exposed pad (datasheet 3.10 SQ vs footprint 3.1×3.1 mm).
- **Package-identity level only** (stock library footprints; body,
  pitch, pin count checked, pads not re-measured): SOIC-8, SOIC-16,
  SOT-23, SOT-23-5, SOT-23-6, TSOT-23-6, VSSOP-10, MSOP-10-1EP,
  DFN-10-1EP, QFN-16-1EP, QFN-32-1EP (body/pitch), LQFP-144,
  Crystal_SMD_3225-4Pin, Oscillator_SMD_Abracon_ASE, the Amphenol
  USB-C and SMA manufacturer-named models, pin headers, and all
  0402/0603/0805/1206/1812 chip patterns.

## Evidence index (principal claims → primary record)

- Board census 144 = circuit.py census 144, identical designator sets;
  per-ref footprint/value map: `docs/08-evidence/board_map.json`
  (extracted from `hw/pdlvds_rx.exp13.kicad_pcb` this audit).
- U9 pad overlap 0.20 mm ×: pad geometry parsed from the board file
  and from `hw/pdlvds.pretty/TMP117_WSON6.kicad_mod`
  (`docs/08-evidence/footprint-pads.txt`); the overlap scan covered
  all 144 board footprints — U9 is the only hit. TI pattern callouts:
  `datasheets/tmp117.txt`, EXAMPLE BOARD LAYOUT DRV0006B (pads
  6× (0.45)×(0.3), "4X (0.65)", span (1.95)).
- D1 VBR/ceiling: `docs/07-d1-terminal-pair-evidence.md` (cited).
- D2 VBR typ 400 / max 500 V, pin circle: `datasheets/s8664.txt`
  characteristics table; MANIFEST Stage-7b (drawing p.4 read).
- OPA657 total-supply framing: `datasheets/opa657.txt` §7.1
  ("Supply voltage (Total Bipolar Supplies) ±6.5 V"), §7.3
  ("VS Total supply voltage 8 / 10 / 12 V").
- LMH7220 ranges: `datasheets/lmh7220.txt` (supply 2.7–12 V;
  VOD 250/330/400 mV; VO 1125/1225/1325 mV; VRI −0.2..VCC−2).
- THS4304 supply: `datasheets/ths4304.txt` (single 2.7–5 V; abs max
  VS +6.0 V).
- DAC8562 AVDD 2.7–5.5 V: `datasheets/dac8562.txt`.
- TMP117 V+ 1.8–5.5 V; ALERT open-drain ("requires a pullup"):
  `datasheets/tmp117.txt`. R22 = pull-up to +3V3D: `hw/circuit.py`
  line 205.
- USB3300: VDD3.3 3.0/3.3/3.6 V; VBUS max 5.5 V; crystal Table 5-8
  (24 MHz fundamental, CL 20 pF typ, ESR ≤30 Ω, ±500 ppm); XI/XO pin
  capacitance 3 pF typ: `datasheets/usb3300.txt`.
- ADN2813: data rate 10–1250 Mb/s; VCC 3.0/3.3/3.6 V; 139/155 mA;
  sensitivity 3.3 mV pp; max diff input 2.0 V; LVDS out 250–400 mV /
  VOS 1125–1275 mV; REFCLK 10–160 MHz, single-ended allowed; outline
  5.00 SQ, 0.50 BSC, EP 3.10 SQ (2.95–3.25): ADN2813 Rev. C datasheet
  (analog.com, fetched this audit). I2C address 0x40 at SADDR5=0:
  MANIFEST (Rev. C text).
- SN65LVDS32: single 3.3 V supply; 100 Mb/s (SN65LVDS32); ±100 mV
  thresholds; SOIC-16 D 9.90×3.91 mm; pin table: SLLS262R (ti.com,
  fetched this audit).
- TPS62130: VIN 3–17 V; abs max AVIN/PVIN 20 V, EN/SS −0.3..VIN+0.3,
  DEF/FSW/FB/PG/VOS −0.3..7 V (all w.r.t. the IC's ground terminal);
  VFB 0.8 V; pin table 6-1: SLVSAG7F (ti.com, fetched this audit).
  Inverting topology = its §10.3.3 (MANIFEST).
- LT3042: IN 1.8–20 V; ISET 99/100/101 µA; dropout rows 220–350 mV
  (50–200 mA) and 350 mV typ @ 200 mA headline; min COUT 4.7 µF;
  PGFB pin −0.3..22 V; DD package EP = GND pin 11: LT3042 Rev. C
  (analog.com, fetched this audit). ILIM scale 125 mA·kΩ: MANIFEST
  (full-text read) — loads pass under the 100 mA·kΩ reading too.
- LT3757 verified subset (MSOP-10 MSE pin functions, EP=GND,
  SHDN/UVLO 1.22 V falling, INTVCC 7.2 V, bypass ≥4.7 µF, VIN
  2.9–40 V): MANIFEST (two independent datasheet copies).
- IRLML0030: VDS 30 V, ID 5.3 A @ TA 25 °C, RDS(on) max 40 mΩ
  @ VGS 4.5 V, Qg 2.6 nC @ 4.5 V, Micro3/SOT-23: Infineon
  PD-96278B (via Mouser, this audit).
- ES1J: VRRM 600 V, IF(AV) 1.0 A, trr 35 ns, DO-214AC: ES1J series
  datasheet data (onsemi/Vishay class-identical).
- SMBJ5.0A: VRWM 5.0 V, VBR 6.40–7.00 V, VC 9.2 V @ 65.3 A, 600 W,
  DO-214AA: SMBJ series datasheets (Littelfuse/Vishay/Bourns
  agree). DO-214AC = SMA vs DO-214AA = SMB: JEDEC package
  registrations as encoded in the KiCad Diode_SMD library names
  (D_SMA fitted per board map).
- USBLC6-2SC6: pinout (1 I/O1, 2 GND, 3 I/O2, 4 I/O2p, 5 VBUS,
  6 I/O1p), VRWM 5.25 V, VBR 6 V, Ci/o 2.5 typ/3.5 max pF: ST
  DS4260 Rev. 6/7 (via Mouser, this audit).
- Abracon ASE family: pin function table (1 OE, 2 GND, 3 OUT,
  4 Vdd) and orderable supply-voltage options: Abracon ASE/ASEK
  series datasheets (this audit).
- Amphenol 12401610E4#2A: current rating 5 A, voltage rating 100 V,
  24 positions, USB 3.2 Gen2: Amphenol CS product specification
  (this audit).
- T1 design intent (N=20, Lp=47 µH, 250 kHz): `sim/hv_design.py`
  lines 32–33. Absence of any T1/clamp/interlock part: census of
  `hw/circuit.py` PARTS = board census (above).
- R27 conflict: `hw/CONNECTIONS.md` ("GATE (7) -> R27 10 Ω") vs
  `hw/circuit.py` (R27 = "10k").
- C4 conflict: `hw/CONNECTIONS.md` AFE note (630 V 1206 required) vs
  `hw/circuit.py` (C4 = 1uF, C_0603) and board map (C_0603_1608Metric).
- Demand numbers: `docs/03-power.md` rail table and budgets;
  `docs/01-requirements.md` R4/R6/R9/R11.

## Not verified (gaps, with the source tried)

- LT3757 FBX reference, RT table, SENSE threshold — datasheet PDF
  fetch from analog.com failed (network error); the project's two
  copies truncate the same numbers (MANIFEST, docs/04 R-3).
- STM32H723ZGT6 VDD/VDDA ranges and VCAP requirement — DS13313
  fetch from st.com failed; project recorded the same block
  (MANIFEST). Pin *map* rests on the KiCad symbol + two secondary
  cross-checks, not on the ST document.
- TMP117 DRV0006B rendered drawing — the MISMATCH verdict rests on
  (a) the footprint's own measured self-overlap (primary, from the
  board file) and (b) land-pattern callouts in the extracted
  datasheet text that do not reconcile with the footprint's
  geometry; a rendered-drawing read at fix time should confirm the
  exact corrected pattern.
- LT3042 dropout at exactly 38–40 mA — the datasheet's dropout
  *curve* is graphical; the extracted table brackets 50–200 mA.
- USB3300 exposed-pad exact dimensions — package-identity check
  only (body/pitch/pin count from `datasheets/usb3300.txt`).
- TPS62130 switch current-limit exact value — not needed for any
  verdict as framed (L1/L2 turn on the absence of a specified
  inductor, not on the limit's third digit).
- Abracon ASE 25 MHz ordering-code table specifically — family-level
  evidence (ASE/ASEK) establishes that supply voltage is an orderable
  option; the exact 25.000 MHz code string was not pulled.



## Parts-fix outcome (branch `parts-fix`, record: docs/09-parts-fix.md)

The directed fixes for this audit were executed on branch
`parts-fix`; the per-finding closure record with evidence is
**docs/09-parts-fix.md**. Summary: F-02 (clamp half: S8664 stack
fitted; C30737 no-window finding recorded), F-03, F-04, F-05,
F-06, F-07 (with R24 refitted — the RT suspicion was correct),
F-09, F-10, F-11 (closed as a recorded residual risk in docs/03),
F-12, F-13 are CLOSED. Still open: F-01's land-pattern condition
(docs/07 (a); its rail-bound half (b) now PASSES — see the docs/07
amendment) and F-08 (DS13313 still unreachable; U6/C17/C18 stay
UNVERIFIED). Flagged sub-items: T1 provisional land pattern, SH1
clip-land conversion, D8 package outline — all listed in docs/09.
This audit's rows are not re-verdicted here; the re-audit is the
audit owner's.
