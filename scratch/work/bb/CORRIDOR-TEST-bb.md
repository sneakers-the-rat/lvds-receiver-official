# Corridor test — user direction, tested on exp256 (bb, 2026-11-09)

User's read: the XI drop is fenced by a B-layer LOOP under U7 that curls
around a via at the chip's south-center; shift the corridor's B traces
EAST, then run XI straight on B from the arc via (75.625,18.625) north
to the U7.28 drop (pocket via PV (75.82,10.30), built pass 218).

## Identification (from the board, t_bb28 census of exp256)
Under-chip B corridor x[74.0,78.0] y[12.0,16.2] contains exactly:
- **ULPI_STP chain** (the pass-217 chain): (76.425,12.90)->(76.05,13.45)
  ->(76.35,13.90)->(76.35,15.60)->(76.05,16.70). **This IS the loop the
  user saw** — it bows east around the via below.
- **GND EP-stitch via (75.6,14.75) r0.3** — the ONLY via inside the U7
  exposed-pad rect; the chain wraps it.
- PHY_1V8 B chain x76.95 (the corridor's east wall).

## The eastward shift itself (t_bb29, exact model)
Chain re-laid at x76.48: gates +0.02 vs PHY_1V8 (buildable, knife-edge);
clears the stitch via (+0.28) and the straight XI line (+0.32). Cost if
built alone: 3 segs ripped/re-laid, STP terminals unchanged. It buys
the corridor — but the corridor was never the seal.

## The straight run, gated exactly (arc -> PV, single B seg hw0.125)
Variant 1 (chain east, stitch via in place) — fences (edge margin, mm):
- GND stitch via (75.6,14.75): **-0.509** (arc, stitch via and PV are
  nearly collinear at x 75.6-75.8; the line passes 0.116 from its centre)
- ULPI_DIR via (75.5,17.521): **-0.424**; DIR seg1: **-0.274**
- ULPI_STP dive via (76.065,17.96): **-0.151**; STP south column x76.05
  densified pieces: **-0.02..-0.045**; STP chain SW corner: -0.045
- ULPI_STP descent rejoin diagonal (76.425,12.9)->(76.05,13.45): **-0.121**

Variant 2 (chain east + stitch via relocated inside the EP to
(75.0,12.8); GND model frags 86->86): stitch fence gone, ALL others
remain (DIR via -0.424 etc.). Stitch via cannot move east instead:
sandwiched — needs 0.60 from the STP chain and 0.65 from the PHY_1V8
chain, which sit 0.47 apart after the shift.

## Verdict
The straight B run does not exist in this configuration. The seal is
not the under-chip loop: it is the corridor's SOUTH MOUTH (ULPI_DIR via
1.10 mm from the arc — any straight northbound line passes ~0.15 from
its centre vs 0.575 demanded — plus STP's dive via/column) and the
pocket DOORSTEP (STP descent diagonal), with the stitch via dead on
the line in between. NOT BUILT (does not gate). Pocket-via optimisation
line (pass 218 state) remains the live XI route.
