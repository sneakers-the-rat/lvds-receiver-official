# D1 terminal-pair exemption — evidence note and STOP verdict

Question put to the evidence: may the audit's 1.0 mm HV-class
clearance stop charging the pair D1.5 (APD_K) vs D1.4/D1.6 (APD_A),
0.5 mm apart inside D1's own footprint, on the grounds that it is
the manufacturer's own terminal geometry? The directed gate had
two evidence conditions; the exemption ships only if BOTH hold.

## (a) Land pattern — INCOMPLETE

Datasheet (Excelitas, "C30737PH and C30737LH Series",
C30737PH-LH-Rev.2011-09), Table 4 ordering guide: the LH package
is a "Leadless ceramic carrier (3 x 3 mm2 LCC)".

Board footprint (hw/pdlvds.pretty/C30737LH_LCC6.kicad_mod):
outline 3.0 x 3.0 mm — matches the datasheet package size.
Six pads 1.3 x 0.6 mm, columns at x = +/-0.85 mm, rows at
y = -1.1 / 0 / +1.1 mm, so the adjacent-pad edge gap is 0.5 mm.
hw/CONNECTIONS.md line 11: D1 pad 5 (centre row) = cathode ->
APD_K; pads 4 and 6 flank it on the APD_A side.

The LH package drawing is Figure 10 of the current datasheet
(Rev.2017-10, p.9; the project's own copy is
datasheets/C30737.pdf, provenance per datasheets/MANIFEST.md).
Its dimensions are raster graphics: the PDF text layer of that
page contains only the figure caption, in both the
Rev.2017-10 project copy and the Rev.2011-09 copy. A pad-for-pad
comparison against the manufacturer's recommended land pattern
could NOT be completed from text sources. Condition (a) is
therefore unverified, not established.

## (b) Rated voltage vs design maximum bias — FAILS THE GATE

Datasheet Table 1 (p.2), column C30737LH-500-90 (unfiltered,
900 nm peak): "Breakdown Voltage, VBR — Min 180, Max 260 V";
"Temperature Coefficient of VR, for Constant M — 1.3 V/°C"; all
characteristics specified "at TA = 22 °C; at operating
voltage-Vop"; operating temperature -20 to +60 °C. Values are
identical in the project's own datasheet copy
(datasheets/C30737.pdf, Rev.2017-10, Table 1: VBR 180-260 V;
datasheets/MANIFEST.md records "Vbr 180 typ / 260 max V" for
the C30737LH-500-90) and in Rev.2011-09 Table 1. The part is characterised for operation at Vop
at/near its breakdown; nothing in the datasheet rates its
terminals for more than the VBR envelope (max 260 V at 22 °C,
plus the 1.3 V/°C constant-M drift).

Design maximum bias (docs/03-power.md, "HV set-point network"):
V_HV ≈ 247.8 + 107.4 x (1.6 − V_DAC) volts; the DAC powers up at
zero-scale, "which corresponds to HV ≈ 420 V demand … the loop
regulates to ≈420 V, the design maximum." The 150-420 V supply
range exists for the alternate Hamamatsu S8664-20K population
(docs/02-architecture.md: "Its bias requirement is why the HV
supply is designed to 420 V"). For the C30737 population the
firmware maps set-points near the part's Vop and holds the
converter disabled until configured — but no hardware bound
limits the voltage the rail can present at D1's terminals to
the C30737's envelope. The pair D1.5/D1.4/D1.6 stands across
essentially the full bias (anode at the TIA virtual ground,
≈ +1.0 V; docs/02-architecture.md).

420 V (design maximum) > 260 V (datasheet VBR max). The voltage
exceeds the rating.

## Verdict: STOP — no exemption ships

Per the directed gate, the audit is NOT rescoped and no
exceptions-registry entry for D1 is created. The two audit lines
(APD_K (D1.5) vs APD_A tracks at (8.3, 38.62) and (9.15, 41.4),
"need 1.0 mm") remain violations of the check exactly as
written. This also means "zero means zero" cannot be reached by
relabelling this pair: the pair is manufacturer geometry, but
the manufacturer's geometry is specified for a ≤260 V-class
part, and this design's rail can exceed that envelope.

What would change the answer (owner decisions, not audit
decisions):
- a hardware bound on the HV rail for the C30737 population
  that keeps D1's terminal voltage inside its datasheet
  envelope under every condition the design can produce
  (including DAC power-on zero-scale), or
- a detector population whose rating covers the 420 V rail.

Sources: datasheets/C30737.pdf (Excelitas Rev.2017-10) Table 1
p.2, Figure 10 p.9, Table 4 p.10, via datasheets/C30737.txt and
datasheets/MANIFEST.md; Excelitas datasheet
C30737PH-LH-Rev.2011-09 Table 1 p.2 and Table 4 p.8 (fetched
2026-11-05, same values); docs/02-architecture.md;
docs/03-power.md; hw/CONNECTIONS.md;
hw/pdlvds.pretty/C30737LH_LCC6.kicad_mod.

## Amendment — post-clamp gate state (HV clamp merged; parts-fix)

The design changed after the verdict above: the HV set-point
network was re-ratioed and merged (R31 7.68 MΩ / R32 75.0 kΩ /
R33 140 kΩ, all 0.1%; SHDN divider R25 143 kΩ / R26 33 kΩ; J5
interlock in the PC7 path). The gate's two conditions re-run
against the merged design:

**(b) Rated voltage vs design maximum bias — NOW PASSES.**
The fitted C30737 transfer is V_HV = 253.21 − 54.857·V_DAC, so
the maximum demand over ALL DAC states — including the DAC8562's
zero-scale power-up state, which is the top of the transfer — is
253.21 V nominal, and 259.40 V with every tolerance corner
stacked against the bound (0.1% resistor stack, FBX reference at
its 1.631 V datasheet max, FBX pin sinking its 100 nA max):
inside the 260 V VBR maximum. Derivation:
results/hvfix/derivation.py (re-run on the parts-fix branch,
output byte-identical to the merged record). ngspice of the
actual network agrees: 253.17 V nominal zero-scale, 259.36 V at
the worst corner, verdict PASS (results/hvfix/hv-clamp-sim-run.txt;
sim/run_hv_clamp.py). D1's terminals stand across essentially the
full bias (anode ≈ +1.0 V), so the maximum at the terminal pair
itself is ≈252 V nominal / ≈258 V worst-case (docs/03) against
the 260 V rating. The 420 V figure that failed this gate no
longer exists in the C30737 population's hardware: that range
survives only in the mutually exclusive S8664 stuffing variant,
whose detector is 500 V-class. The parts-fix R31 series string
(2.94 MΩ + 2× 2.37 MΩ) was proven to preserve this bound exactly
(results/partsfix/r31_string_check.py: all-corner total band
identical to the single-part model; worst-high reproduces
259.40 V).

**(a) Land pattern — STILL UNVERIFIED.** Nothing in the clamp or
parts-fix work touched D1's footprint or produced a readable
copy of the manufacturer's Figure 10 land pattern; the condition
stands exactly as recorded above.

**Gate state: the exemption still does NOT ship.** Condition (b)
now passes and condition (a) remains unverified, and the gate
requires BOTH. The two audit lines for the D1.5/D1.4/D1.6 pair
remain in force as written; they come off only when (a) closes
with a pad-for-pad comparison against Excelitas's recommended
land pattern.
