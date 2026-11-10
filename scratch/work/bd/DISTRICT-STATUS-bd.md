# DISTRICT STATUS — bd lane (checkpoint, 2026-11-10)

## Banked
- **Pass 219 (XI) on origin/main a1ad8ef5.** Board hw/pdlvds_rx.exp257.kicad_pcb.
  KiCad DRC 4 (standing J1 copper_edge_clearance only); check_pcb nets 1
  {USB_RST}, census 120 line-identical to pass 218, courtyard 0, blind 21.
  XI geography as built: NXT F stub (75.25,16.875)->via NV (74.94,17.36);
  In2 (74.94,17.36)->(74.10,17.70)->joint (74.5,19.25) into the kept tail
  (vestigial dive via ripped). DIR via DV (74.82,18.10); F stub
  (75.75,16.875)->(75.60,17.30)->(75.42,17.95)->DV; B journey
  DV->(73.3,18.42)->(71.375,19.125). XI ride on B: arc via (75.625,18.625)
  ->(75.42,18.15)->(75.48,17.74)->(75.60,16.95)->(75.60,16.30)
  ->(74.98,15.95)->(74.98,13.40)->(75.32,12.75)->PV (75.82,10.30).
- Tooling: hw/build_lib.py (Surgery: find-then-remove, add_track/via/
  polyline, finish = refill+save+reload census diff). Drivers:
  build_xi.py (v5 = banked shape), build_rst.py (v1, failed, below).
  Scan line (t_bd1..t_bd11) closed by user order; logs committed.
- Merge state: split main tree is DIRTY (not bd's doing): MM
  metrics/commit_alignment.csv + token_per_message.svg, unstaged
  deletions under scratch/recovered/. bd pushes went through a
  detached worktree at HEAD (clean) both times. Do not clean the
  split tree without the parent's word.

## USB_RST — OPEN, one candidate built and refereed
exp258 candidate (build_rst.py v1) CONNECTED the net (DRC unconnected 0)
but cost 163 violations — ripped in effect (exp258 unbanked; exp257 is
the tip). Fence map from drc258.json + facts_region.py (region257.txt,
crossing-inclusive census x[70.5,77.6] y[3.0,20.5]):

- U6 pads are 0.3 x 1.475 (north row y[3.925,5.400]): U6.40 x[74.6,74.9].
  Any F arrival leg must run at y>=5.7 and drop at x74.75 into y5.400.
  ULPI_D0's F staircase (73.25,5.66)->(73.88,5.88)->(74.12,5.88)
  ->(74.38,6.12)->(74.62,6.38)->(74.88,6.62)... seals that channel:
  pad-row<->D0 gap is 0.667 at best (x73.55) — a w0.2 leg fits ONLY at
  y5.70 with both clearances at ~exactly 0.20-0.22, and its feed via
  has no legal cell west (D0 stub x73.25 + re-laid D0 steps) or east
  (ULPI_CK via (75.12,5.88) d0.6 + D0 tread y6.62 contradict at x75.125:
  via needs leg y>=6.475, tread needs y<=6.22).
- North pocket (B): DIR's B polyline DV(74.82,18.10)->(73.3,18.42)
  ->(71.375,19.125) + continuation seals the B pocket; south bow for
  DIR (drop x75.05, westward y19.6-19.95) hits CAP_DATA's B curve
  (via (72.6,19.3), densified journey SE through (72.95,19.65),
  (73.8,20.5), (74.3,21.0)) and its via (bow leg grazes 0.03-0.18).
  B stack y[18.1,19.7] x[72,74.5] must hold DIR + RST + DM_PHY via
  (73.625,19.125) d0.6 + CAP_DATA via — over capacity by ~0.3 mm.
- North pocket (F): DM_PHY loop east edge (vertical x74.125 w0.25,
  east edge 74.25) is flush with U7.9's stub head x74.25; NXT via NV
  (74.94,17.36) exclusion + DM vertical seal every F corridor
  (feasible interval empty at y17.5: [74.55, 74.42]).
- West dive (B, x72.2): PHY_1V8A B column + long +3V3A B legs
  (5.0/7.0 mm) + I2C_SDA B staircase + DP_PHY via (72.12,15.88) d0.6
  + XO via (72.12,9.88) — v1 dive shorted/crossed all of them.
- South hop (B->In2->F at y5.3): I2C_SCL B and I2C_SDA B staircases
  are parallel diagonals (SCL (72.875,4.625)->(76.125,7.875); SDA
  (71.12,4.12)->via (73.38,7.62)); BIST_DRV In2 is the opposite
  diagonal; SPI_MOSI In2 (71.9,7.25)-(73.4,5.2) caps the hop window.
  GND via move (73.434,17.685)->(72.8,18.2) is DEAD: RBIAS In2 mesh
  southern tail reaches (72.8,18.2) (shorts in drc258).

## Named question put to the parent (scan go-ahead requested)
Does ANY layer-sequence + corridor exist for USB_RST on the exp257
board if the search may jointly re-lay {DM_PHY F loop, ULPI_DIR
journey, GND via (73.434,17.685), ULPI_NXT escape}? Hand-building
has failed three compositions on referee-named items (v1: 163
violations, 6 nets); each partner's move re-fences the others, so
the constraint is joint (az's leave-one-out result said the same).
No scan written pending go-ahead.

## SCAN OUTCOME (go-ahead granted; run 2026-11-10. NO configuration;
## framing failed — stopped per term 1 of the go-ahead, no 2nd design)
Machinery: hw/gridroute.py (rasterizer with referee-class pair
inflation + 3-layer A*); driver scratch/work/bd/scan_rst.py; log
scan_rst.log; diagnostics scan_debug.py / scan_debug2.py /
scan_debug3.py. The one declared design: district x[70.0,77.6]
y[3.4,20.6], pitch 0.05, eps 0.02, partners' re-lay spans removed,
kept tails/pads as obstacles, 6 routing orders x GND-via legal
cells ranked from current (budget 48 attempts).
Result: NO CONFIGURATION in 48 attempts. Failure histogram:
ULPI_DIR "no path" x32 (every attempt that reached DIR); USB_RST
"terminal blocked" x16 (every attempt that reached RST first or
second); ULPI_NXT routed in all 48; DM_PHY never reached.
Two distinct bindings:
1. FRAMING (DIR leg): the raster cannot represent DIR's EXISTING
   referee-legal pass-219 journey. Dense samples of the built
   journey are free except 3 cells, all on F leg1 in the pad
   mouth, all stamped by FIXED ULPI_STP's F stub. Leg tests:
   F start->DV SEALED, B DV->goal PATH. The mouth map
   (scan_debug3) shows DIR's pad exit connects south only via a
   one-cell diagonal thread at y16.98-17.07, severed by the
   corner-cut rule — the built leg runs at exact clearances
   0.20-0.24 vs STP's stub (centreline 0.40-0.42), below the
   raster's representable resolution (~0.47). A scan that cannot
   reproduce the status quo cannot judge joint re-lays.
2. SUBSTANTIVE, EXACT (RST arrival): the "terminal blocked" is
   real geometry, not raster. Strengthens the F-arrival fence
   above: the CK via seals not just the feed via but the DROP
   LEG itself. Pad-legal entry into U6.40 is x in [74.75,74.80]
   on the north edge (pads 39/41 corner discs), but a drop leg
   there must join its horizontal at y <= 5.388 (x74.75) or
   y <= 5.371 (x74.80) to stay 0.6 from CK via centre
   (75.125,5.875) r0.3 — below the pad edge y5.400. Every
   approach to the pad crosses the via's 0.6 disc or a neighbour
   pad. ULPI_CK is NOT in the approved movable set, so the named
   question answers NO for a reason outside the joint re-lay set.
Next geometry change (posture law; needs a NEW go-ahead): widen
the re-lay set to ULPI_CK's U6-side escape (its via + first In2
leg). Candidate neighbourhood for the CK via ~(75.4,5.9) —
distances: 0.656 to the RST drop join (74.775,5.7), 0.552 to
its own pad41 rect, ~0.97 to D0's NE stairs (exact gating still
owed); its In2 leg then re-lays west to the existing x74.625
column (fences: DAC_SYNC In2 diagonal south of it, SPI_MOSI
In2 west). DIR's escape stays build-first exact geometry, as
pass 219 proved works. USB_RST remains OPEN; exp257 is the tip;
no pass 220.

## Carried opens (unchanged)
SH1 courtyard blind list (21); 2 gated D1 clearance lines; project
completion sequence is a later phase. Split-tree dirtiness (above).
