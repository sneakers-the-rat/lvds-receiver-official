# DISTRICT-STATUS-6 — am session handover (exp231 / pass 201)

## Banked this session
- Passes 194/195: GND U6.38 island healed (see STATUS-5).
- Passes 196/197: SWCLK connected (see STATUS-5).
- Passes 198-201: SILK CAMPAIGN COMPLETE. KiCad DRC violations
  150 -> 4 (the 4 standing J1-intrinsic copper_edge items).
  silk_overlap 0, silk_over_copper 0, silk_edge 0. Unconnected
  unchanged 13; check_pcb nets 12, census 109, courtyard 0,
  blind SH1 21 -- identical throughout.
- Board state: exp231, DRC 13 unconnected / 4 violations.
  origin/main a29dbc4 at handover write time (verify on receipt).

## HV pocket (queue item 1) — NOT landed; two scan rounds done
Tools: scratch/work/am/t_am1_hvdump.py (full pocket dump,
hv-dump-exp231.txt), t_am2_scan.py (configs A/B/C), t_am3_scan2.py
(config B2 + rise scan). All scans on the exact item model
(t_ai_lib, fixed pool), HV_INTVCC gated at its real class 0.20.

- Config A (current board): 0 feasible INTVCC dives. Control --
  matches STATUS-5's seal proof.
- Config C (GATE needle + via ripped only): 0 dives. The needle
  alone is NOT the block; SHDN's via/web is.
- Config B (SHDN via -> (30.72,-3.55) d0.5, web + In2 re-laid;
  +5V NE staircase joints moved south): 3 feasible dives --
  (30.95,-2.75) min +0.005, (30.85,-2.80) +0.003, (31.00,-2.70)
  +0.000, all with straight F access from the pad's east edge.
  BUT two B additions fail their own gates vs the KEPT +5V SE
  staircase seg (31.625,-4.375)->(31.15,-4.000) w0.6.
- Config B2 (SHDN via -> (30.60,-3.62) d0.5; +5V joint moved east
  to (31.45,-4.000), both staircases re-fanned from it): the
  re-fanned staircases gate CLEAN (+0.131..+0.770), the same 3
  dives appear (+0.006/+0.003/+0.000) -- but the +5V pad run
  (29.65,-4)->(31.45,-4) w0.2 FAILS vs the SHDN via (-0.220) and
  the SHDN web seg fails vs the run (-0.070).

### The via/run/pad triangle (the current crux, exact)
SHDN's replacement via must satisfy ALL of:
- >=0.45 from INTVCC's pad rect (SE corner (30.375,-3.15));
- >=0.55 from the +5V pad-run line y=-4.0 (via r0.25 + run hw0.1
  + clr 0.2), i.e. centreline y >= -3.45;
- stay out of INTVCC's exit channel: INTVCC exiting east between
  the GATE pad (south edge -2.65, needs track centreline
  y <= -2.95) and its own pad needs >=0.55 from the via at the
  track's x -- a via at (30.80,-3.44) (which satisfies the first
  two at +0.064/+0.010) puts its exclusion disc (top at y-2.89)
  across that channel.
Candidate (31.0,-3.50): pad +0.266, run -0.050 -- the run line
kills every point with y<=-3.45 that is far enough east.
=> The +5V pad run itself must move or dive. Variants not yet
scanned: (i) +5V run dives to In2 east of its pad (via candidates
(30.75,-4.05) gates +0.098 vs SHDN's pad; In2 east is open) and
rises twice for the two staircases -- makes it a 6-net job;
(ii) +5V run re-lays SOUTH on F at y<=-4.55 from x30.4 (fences
south not yet censused: GATE/SENSE B chains are B-only, F south
of the pocket needs a fresh dump box y[-8,-3]);
(iii) SHDN via d0.5 -> the via goes NORTH-EAST instead and its
In2 join runs at y-2.875 east of x31.9 (web must cross INTVCC's
latitude on F east of the dive points -- the dives at
(30.85..31.0,-2.8..-2.7) sit exactly there; untested combo).

### New fact: C31.1's north side is WIDE OPEN
Rise scan (t_am3): 253 feasible rise points with straight F
access to C31.1's west edge; best cluster around (31.40,0.0..0.2)
at min +0.44..+0.50 on all layers. The journey's hard part is
only the In2/B crossing between the dive cluster
(30.85..31.0,-2.8..-2.7) and the rise cluster: FBX's In2 band
(y-2.125 horizontal x[30.625,32.375] + NE staircase) blocks In2
northward; GATE's B web + via (31.7,-1.5) block B. East In2
detour past the band's east end and north of GATE's via at
y~-1.15 was hand-checked to ~+0.075 worst (unverified by scan;
do it in the optimizer).

### Vehicle for the next session (unchanged in kind)
A proper joint optimizer: variables = SHDN via (x,y), INTVCC
dive (x,y), INTVCC rise (x,y), +5V run variant (i/ii/iii),
GATE needle kept, FBX band kept; gate every moved seg/via on
the exact model; flood/groute the In2 journey dive->rise on a
trial board; emit verbatim (margins will be knife-edge --
groute cannot thread +0.000..+0.006, as before).

## Remaining queue
1. HV pocket joint optimizer (above).
2. J1 pocket: DP_CON A6<->B6 + D3.1 leg (STATUS-5).
3. Long-haul singles: CAP_CLK, CAP_DATA, CDR_LOS, SPI_SCK,
   SPI_MOSI, +3V3D U11.14 (STATUS-5; all endpoint-sealed).
Parked (user decisions): STP/XI/USB_RST (C20), PHY_1V8A (C16).
Standing: 2 D1 clearance lines untouched; 4 copper_edge items
are J1-intrinsic -- do not chase.
