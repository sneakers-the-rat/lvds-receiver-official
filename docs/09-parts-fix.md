# 09 — Parts-fix closure record (docs/08 findings F-01…F-13)

Branch `parts-fix` on base `57a1150` (the merge that already carried
the HV set-point clamp and J5 interlock). Every fix below closed
against primary evidence: manufacturer datasheet text, the
regenerated-netlist check, or a committed proof script. Datasheet
extracts and fetched PDFs live in `results/partsfix/datasheets/`;
proof outputs in `results/partsfix/`.

## Regeneration evidence (hw/gen_schematic.py → kicadxml → hw/check_netlist.py)

| State | Parts | Connected pins | Nets | Expected connections | Verdict |
|---|---|---|---|---|---|
| Baseline (57a1150) | 145 | 632 | 213 | 533 | PASS |
| After batch A (values/footprints) | 145 | 634 | 217 | 531 | PASS |
| After batch B (HV strings + OVP) | 152 | 648 | 223 | 545 | PASS |

The checker verifies the netlist matches `hw/circuit.py` exactly;
all three runs PASS (`results/partsfix/netlist-*.txt`).

## Per-finding closure

**F-01 (D1 over-voltage) — rail bound CLOSED by the merged clamp;
docs/07 gate re-run in this branch.** Condition (b) now PASSES
(≈252 V nominal / ≈258 V worst-case at D1's terminals vs the
260 V rating; derivation re-run byte-identical, ngspice agrees —
see the amendment appended to docs/07). Condition (a), the
manufacturer land-pattern comparison, remains UNVERIFIED, so the
exemption still does not ship and the two audit lines stay. The
D1 row's remaining blocker is (a) only.

**F-02 (missing OVP clamp + interlock) — CLOSED with one recorded
negative.** The interlock half was delivered by the merged clamp
(J5 in the PC7 path; divider alone can never enable). The clamp
half is population-split:
- *C30737 fit:* a clamp must not conduct at the worst-case maximum
  demand, 259.40 V, and must conduct below the lowest absolute
  maximum on the rail, D1's 260 V VBR max. The window
  (259.40, 260.00) is 0.6 V wide; no real clamp device has a
  tolerance band inside it. **No clamp is fitted for this
  population — recorded as a finding, not papered over.** Its
  protection is the hardware set-point bound (259.40 V worst-case)
  plus the interlock. (docs/02's old "440 V" promise was also
  arithmetically wrong for both fits: 440 V × 0.95 = 418 V <
  429.47 V, so that clamp would have conducted during normal
  worst-case S8664 operation.)
- *S8664 fit:* window = (429.47 V worst-case demand, 500 V =
  D2's VBR max, the lowest rating on that rail; other rail parts
  are 600–630 V class or ≥700 V strings). Fitted: **D9 SMBJ5384B
  (160 V) + D10/D11 SMBJ5383B (150 V)**, all ±5%, DO-214AA —
  460 V nominal, band 437–483 V, inside the window with 7.5 V /
  17 V margins. Stack sits on HV_RAW upstream of R29 so APD_K
  can never exceed it. Series impedance ≈990 Ω at test current
  softens the knee under the converter's ~10 mA fault delivery
  (clamp point ≲493 V < 500 V); per-device fault dissipation
  ≈1.5 W is transient-duty against the SMBJ ≈1.38 W @25 °C
  board rating — recorded, accepted for a fault-only path.
  **DNP in the standard C30737 build; fit only with the S8664
  population.**

**F-03 (C4) — CLOSED.** No 1 µF 630 V MLCC exists in any case
(Murata 630 V tops at 0.22 µF/2220 X7R; TDK 0.15 µF/1210; KEMET HV
X7R family 560 nF max — manufacturer data in
`results/partsfix/datasheets/` research notes). C4 is now the
**Panasonic ECWFD2J105JB**: 1 µF, 630 V, metallized polypropylene
film, radial TH 25.3×8.4×18.5 mm, 15 mm pitch, on the new custom
footprint `ECWFD_1uF_630V` (holes Ø1.1 mm cover the family's
≤1.0 mm leads). CONNECTIONS.md's "630 V 1206" note is corrected
to the fitted truth. Note: ECW-F(D) derates 1.0 %/°C above 85 °C.

**F-04 (U9 TMP117 footprint) — CLOSED.** Footprint redrawn from
TI SNOSD82D DRV0006B: signal pads 0.45×0.30 mm at x = ±0.975
(1.95 span), 0.65 mm row pitch; exposed-pad land 1.0×1.6 mm =
the package outline's exposed thermal pad (1±0.1 × 1.6±0.1).
The p.40/p.41 datasheet pages were read as rendered drawings
(also resolving pin numbering: left column top→bottom 1,2,3;
right column 4 bottom / 5 mid / 6 top — matches circuit.py).
Proof: `results/partsfix/tmp117_pad_geometry.py` parses the
footprint file and verifies every callout plus **zero pairwise
pad overlaps** (min signal-to-EP clearance 0.250 mm) — PASS,
output committed (`tmp117-pad-geometry.txt`).

**F-05 (D4) — CLOSED.** Footprint D_SMA → **D_SMB** (DO-214AA),
the package the SMBJ5.0A actually is. Part unchanged (its surge
data was already verified by the audit).

**F-06 (HV resistors + C31) — CLOSED.**
- R29: 2× **KOA HV73V1J 5.00 kΩ** (0603) in series = 10.00 kΩ
  (new R47, net HV_R29M). HV73V1J max working 350 V; worst fault
  (full S8664 rail across the string) = 214.7 V/element ✓.
- R30: 2× **KOA HV73V2B 2.35 MΩ** (1206) = 4.70 MΩ total (new
  R48, net HV_R30M); bleeder discharge spec unchanged (same total
  R, same rail capacitance). HV73V2B max working 800 V.
- R31: three-element string, below (F-06's divider leg).
- R34: single **KOA HV73V2B 10 MΩ** (1206, 800 V class; the
  HV73V F/G range reaches 10 MΩ inclusive).
- C31: **Samsung CL10J475KP8N3NC** — 4.7 µF, **10 V**, ±10%,
  0603 (Samsung spec sheet). On the 7.2 V INTVCC rail that is
  72% of rating; DC-bias derating of a 4.7 µF X5R-class 0603 is
  real but the LT3757's ≥4.7 µF INTVCC requirement has the
  datasheet's own margin here — noted, accepted.

**F-06/F-08 divider leg (R31 string) — CLOSED with proof.**
R31+R49+R50 = **2.94 MΩ + 2.37 MΩ + 2.37 MΩ, Vishay TNPV1210,
±0.1% each** (E192 values; 1210 case required — TNPV1206 tops at
2 MΩ; TNPV1210 max operating 1000 V, range to 3.01 MΩ).
`results/partsfix/r31_string_check.py`: nominal total is exactly
7.68 MΩ; enumerating all 2³ tolerance corners, the total band is
7.67232–7.68768 MΩ — identical to the single-part ±0.1% model the
merged derivation stacked; feeding the extreme total through the
merged `transfer()` reproduces **259.40 V worst-high (≤260 V
bound holds)** and 429.47 V for the S8664 fit; worst per-element
stress is 164.6 V (S8664 rail) vs the 1000 V rating. The merged
derivation itself was re-run unchanged: output byte-identical to
`results/hvfix/derivation.txt`.

**F-07 (LT3757 FBX/RT/SENSE) — CLOSED; one fitted value was
wrong.** The full LT3757 datasheet (Rev. G) was obtained and read
(`results/partsfix/datasheets/lt3757.txt`):
- FBX regulation **1.569 / 1.600 / 1.631 V** — the derivation's
  corners exactly; FBX pin current **100 nA max** ✓.
- SENSE current-limit threshold **100/110/120 mV** → peak across
  R28 0.05 Ω = 2.0/2.2/**2.4 A max**. This sets T1's Isat spec.
- RT Table 1: 24.9 kΩ sits between the 400 kHz (30.9 kΩ) and
  600 kHz (19.6 kΩ) rows at ≈500 kHz — **the audit's suspicion
  was correct: the fitted R24 never gave 250 kHz.** R24 refitted
  **53.6 kΩ** (two interpolations of Table 1 agree ≈53.6–53.7 kΩ
  for 250 kHz; typical-value basis, recorded as such).
docs/04 R-3 carries the resolution note.

**F-08 (DS13313 / U6 / C17 / C18) — CLOSED 2026-11-10.**
Earlier state (superseded): st.com datasheet curl failed (no
file); the AN5419 curl failed identically; ST community material
corroborated the fitted values but was secondary evidence, so
U6/C17/C18 stayed UNVERIFIED and no value was changed.
Resolution, on primary evidence read 2026-11-10:
- **AN5419 Rev 2 (May 2020), Table 2, read in full from st.com**
  (browser route; the direct curl still stalls from this
  network): for the LDO-enabled configuration — the H723's only
  configuration, its VDDLDO being internally tied to VDD and the
  part having no SMPS pins — the VCAP requirement is **2.2 µF,
  ESR < 100 mΩ, for VCAP1 and the same for VCAP2**. The
  connect-together language applies to VCAP3 (absent on this
  package) and to the LDO-disabled bypass mode (not used;
  firmware never sets the PWR bypass bit — it touches only
  PWR_CR3's USB33DEN). C17/C18 are 2.2 µF ceramics, one per pin,
  exactly as specified; ceramic ESR is far below 100 mΩ.
- **Pin numbers from ST's own symbol data**: exact-block
  extraction of `STM32H723ZGTx` from the installed KiCad 8
  library (MCU_ST_STM32H7.kicad_sym) gives 144 pins with **VCAP
  on pins 71 and 106 only** — the design connects C18 → pin 71
  (net VCAP2) and C17 → pin 106 (net VCAP1), as generated and
  netlist-verified. This also settles the variant question: the
  design as built is the ZG (LQFP-144); the MANIFEST's VG
  (LQFP-100) fallback note records a superseded design phase.
- No value or footprint changed. U6, C17, C18 are VERIFIED.
  Residual: the DS13313 PDF itself is still not archived in
  datasheets/ (st.com direct download stalls; the AN5419 PDF
  likewise could not be archived although its full text was
  read). The two F-08 questions the finding actually turned on —
  which pins are VCAP, and what capacitor each needs — are
  answered by the two ST sources above.

**F-09 (X1/X2) — CLOSED.**
- X1 = **ECS-240-20-5PDN-TR** (ECS CSM-7/HC-49US SMD): 24.0000 MHz,
  **CL 20 pF**, **ESR 30 Ω**, ±30 ppm — point-for-point against
  USB3300 Table 5-8 (CL 20 pF typ, ESR ≤30 Ω, ±500 ppm budget).
  Mainstream 3225 crystals all fail the ESR line (NDK NX5032GA
  70 Ω, Epson TSX-3225 40 Ω, TXC 50–60 Ω), hence the larger case:
  footprint → Crystal_SMD_HC49-SD, pins 4→2 (case unpinned).
- C20/C21 recomputed **as a set** for CL 20 pF with the
  USB3300's 3 pF XI/XO pin capacitance: CL = (C+3)/2 + stray;
  C = 33 pF gives (33+3)/2 + ~2 pF ≈ 20 pF (stray 1–4 pF →
  CL 19.5–21 pF, pulling far inside the ±500 ppm budget). The
  audit's "≈28 pF class" estimate would realize ≈17.5 pF with
  these parasitics and under-load the crystal; 33 pF is fitted.
- X2 = **ASE-25.000MHZ-L-R-T**: Abracon ASE series is the 3.3 V
  CMOS family (Vdd 3.135/3.3/3.465 V per its datasheet; the 1.8 V
  sibling is ASE3 — not used). Suffixes: L = −40…+85 °C,
  R = ±25 ppm, T = tape/reel 1000. Footprint unchanged.

**F-10 (magnetics) — CLOSED; T1 land pattern flagged (below).**
- T1: no production 1:20 / 47 µH flyback transformer exists in
  the searched catalogs (Coilcraft's flyback families stop at
  ~1:2.4 step-up class; Würth's flyback guides are step-down
  Fly-Buck parts), so T1 is a **controlled custom wind** on a
  named standard frame — full specification below.
- L1 = L2 = **Murata DFE201612E-2R2M=P2**: 2.2 µH ±20%,
  **Isat 2.4 A** (≥1.5 A requirement ✓), Itemp 1.8 A, DCR max
  0.116 Ω, shielded metal-alloy 2.0×1.6 mm. Footprint →
  L_Murata_DFE201610P (Murata's DFE 2016 land; the fitted
  generic 0805 land was the wrong case size for this family).
- FB1 = **Murata BLM21PG601SN1D**: 600 Ω ±25% @100 MHz, rated
  1400 mA @85 °C (≥500 mA ✓; it carries ADN2813's 155 mA max).
- FB2 = **Murata BLM21SP601SN1D**: 600 Ω ±25%, 2300 mA
  (≥200 mA ✓).

**F-11 (U13 dropout) — CLOSED as a recorded residual risk.**
LT3042 datasheet (Rev. C) EC table: dropout at ILOAD 1–50 mA =
**220 typ / 270 max mV** (350 mV typ at 200 mA). docs/03's
"≈60 mV typical" claim is not supported by the datasheet and is
corrected there: +VA regulation holds at nominal VBUS (400 mV
headroom) but not at VBUS min (150 mV), where +VA ≈ 4.53 V —
inside every load's operating range. The design consequence is
accepted and written down in docs/03 rather than re-architected.

**F-12 (Q1 + R27) — CLOSED.**
- Q1 = **Infineon IRLML0060TRPBF**: VDSS **60 V**, SOT-23
  (Micro3), RDS(on) max 92 mΩ @10 V (116 mΩ @4.5 V), Qg 2.5 nC
  @4.5 V — vs the incumbent IRLML0030's 30 V / Qg 2.6 nC: same
  gate charge class, same footprint and 1=G/2=S/3=D pinout,
  2.3× the voltage margin over the ≈26.5 V spike-free stress
  (the leakage spike still lands on the FET; 60 V absorbs what
  30 V could not). Gate drive 7.2 V (INTVCC) is inside its
  ±16 V VGS max and above its 4.5 V RDS(on) test point.
- R27 = **10 Ω** in circuit.py (CONNECTIONS.md and gate-charge
  physics agree; the correction is noted in CONNECTIONS.md).

**F-13 (D8 + SH1) — CLOSED with two flagged sub-items.**
- D8 = **Ushio Epitex SMT740**, 740 nm (the decided wavelength);
  docs/02 and docs/04 corrected from 630 nm. Sub-item CLOSED
  2026-11-10: a complete datasheet (Ushio Opto Semiconductors,
  SMT740 data sheet 2019.03, 7 pp., 177,263 bytes with EOF) was
  obtained and now sits at results/partsfix/datasheets/smt740.pdf
  replacing the truncated copy. Reading it changed the design:
  the SMT740 is **not** a 1206 — it is a PLCC-style top LED,
  body 3.2 (lead axis) x 2.7 x 1.8 mm, overall lead span 3.5,
  lens dia 2.4, terminals 2.2 +-0.1 wide with a 0.8 +-0.2 flat
  contact from each body end face; anode mark = chamfered corner
  at the anode end. The fitted LED_1206_3216Metric footprint was
  therefore wrong and has been replaced by pdlvds:SMT740_3227
  (pads 1.20 x 2.30 at +-1.35, covering the contact zone plus a
  toe fillet; pin 1 = K, pin 2 = A at the chamfer end), and D8
  was moved +0.25/+0.35 mm on the board with its BIST_DRV via
  re-laid (pass 224; DRC delta +1 Power-band item at 0.225, no
  clearance below the 0.20 binding rule). Electricals from the
  same sheet: VF 1.9 min / 2.2 typ at IF = 50 mA, VFP 3.8 V at
  500 mA; ratings IF 75 mA, IFP 500 mA, PD 170 mW. The R46
  100 ohm drive from +3V3D therefore delivers (3.3 - VF)/100 =
  11-14 mA (the earlier ≈20 mA estimate assumed a lower VF) —
  comfortably inside every rating; no value change.
- SH1 = **Harwin S02-25200300**: production can, 25×20 mm,
  **3.0 mm internal height** (Harwin EMC catalog) over the
  tallest part beneath it, U1 OPA657 SOIC-8 at 1.75 mm max
  (TI package drawing) — height VERIFIED. Sub-item: the Harwin
  can mounts on S1001 clips, not on the fitted footprint's four
  2.4×2.4 solder pads, and the can is 25×20 vs the footprint's
  26×20 outline. **Convert SHIELD_CAN_26x20 to S1001 clip lands
  at 25×20 before placement** (routing-lane list, below); the
  clip land dimensions are on Harwin catalog pp.178/178a, which
  were not in the fetched extract, so no geometry was invented
  here.
  **Superseded as built (pass 223, 2026-11-10):** when the
  conversion was executed, measurement showed the 25×20 can
  centred on the AFE also covered D1, the photodiode — a solid
  can there would blind the receiver — and no 25×20 placement
  covers U1+U2 while excluding both D1 and U3. As built: the
  smaller stock can **S02-20150300 (20×15×3.0)** on **five**
  S1001-46R clips (the sixth position has no lawful window)
  over U1/U2 only, D1 west of the can wall in the clear;
  R8/C7/C44/C2 relocated. Record: scratch/work/finish/sh1_plan.md.

## T1 controlled winding specification (custom wind, F-10)

Winder/frame: **Würth Elektronik EFD20 10-terminal SMT package,
order code 070-4290** (Würth bobbin-packages datasheet: envelope
23.11 max × 26.1 max × 10.92 max mm; core 150-2124, Ae 31 mm²,
le 47 mm, Ve 1457 mm³), wound by Würth's custom transformer
service or any winder building to this spec on that frame.

- Primary inductance Lp = 47 µH ±10% (measured at 250 kHz, 0 A bias)
- Turns ratio 1:20 (primary:secondary), polarity: dot at the +5V
  end of the primary, dot at the GND end of the secondary
  (as wired in CONNECTIONS.md)
- Saturation: Lp drop ≤20% at **2.6 A** peak (above the LT3757's
  2.4 A max current-limit peak across R28; reference build
  N_pri ≈14 turns on Ae 31 mm² gives B_pk ≈0.26 T at 2.4 A —
  the winder may adjust turns/gap to meet Lp/Isat)
- Leakage inductance ≤500 nH target (sandwich/interleaved wind);
  first-article measurement of the Q1 drain spike is a bring-up
  item (docs/05) — no snubber is fitted in rev A
- Insulation: functional, hipot 1500 VAC primary–secondary;
  winding system rated ≥500 V working (secondary stands at the
  430 V-class rail; reflected primary voltage 430/20 ≈ 21.5 V)
- Pinout (defined by this spec): 1 = PRI_A (+5V), 2 = PRI_B
  (FLY_PRI), 9 = SEC_B (GND), 10 = SEC_A (HV_SEC); 3–8 not
  connected (terminals may be fitted unconnected or omitted)

## Open / flagged items carried forward

All five items originally carried here are closed:

1. T1 footprint — superseded: the fitted transformer is now the
   Würth WE-FLEX HV 749196518 on the manufacturer's recommended
   land pattern (docs/11, docs/12; pass 222).
2. SH1 clip-land conversion — done as pass 223, at 20×15 rather
   than 25×20 for the D1 reason recorded under F-13 above.
3. D8/SMT740 outline + VF — closed 2026-11-10 (see F-13 above;
   pass 224).
4. U6/C17/C18 (F-08) — CLOSED 2026-11-10 (AN5419 + ST symbol
   data; see the F-08 entry).
5. D1 docs/07 condition (a) — CLOSED 2026-11-10 (land pattern
   proven from Figure 10; see docs/07).

What remains open on the project lives in docs/00-status.md
(VID/PID registration before distribution, the DM_PHY width
asymmetry, and the bench list in docs/05 — nothing on paper
substitutes for a built board).

## For the routing lane — re-sync list

New designators: **R47** (R29 string 2/2), **R48** (R30 string
2/2), **R49, R50** (R31 string 2/3, 3/3), **D9, D10, D11** (OVP
stack, DNP standard build).
New nets: HV_R29M, HV_R30M, HV_R31A, HV_R31B, HV_OVP1, HV_OVP2.
Footprint changes:
- U9 TMP117_WSON6 — redrawn in place (same origin; pads moved
  out, EP now 1.0×1.6).
- D4 — D_SMA → D_SMB. D9/D10/D11 — D_SMB (new).
- C4 — C_0603 → ECWFD_1uF_630V (TH radial, 15 mm pitch, big:
  25.3×8.4 mm body — placement must give it room at the AFE edge).
- R29 — R_1206 → R_0603; R47 — R_0603 (new).
- R31/R49/R50 — R_1210_3225Metric (was one R_1206).
- X1 — Crystal_SMD_3225-4Pin → Crystal_SMD_HC49-SD; pins 4→2.
- L1/L2 — L_0805_2012Metric → L_Murata_DFE201610P.
- T1 — XFMR_FLYBACK_6P → XFMR_EFD20_SMD10 (23.11×26.1 mm —
  much larger than the old 9×9 placeholder; HV island grows).
- SH1 — conversion pending (item 2 above); value text updated.
Firmware: untouched on this branch — no fix forced a change
(R24's refit makes the hardware match the 250 kHz design point
the firmware/sims already assumed).
