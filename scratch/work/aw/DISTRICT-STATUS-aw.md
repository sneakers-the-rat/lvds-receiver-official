# DISTRICT STATUS — aw session (CAP district landing, pass 210)

Session: 2026-11-08 22:45 PST → 2026-11-09. Worker aw (ad8257c0).
Frontier in: exp240 / pass 209 (DRC 7 unconnected / 4 violations,
check_pcb 7 nets / census 109 / courtyard 0) — re-verified firsthand
before touching anything (identical numbers).

## RESULT — exp241 banked at pass 210

KiCad DRC: **unconnected 6, violations 5**.
check_pcb: **unconnected nets 6, census 109, courtyard 0**,
fallback SH1-only (21).

Unconnected 6 = the five untouched queue nets (CDR_LOS, PHY_1V8A,
ULPI_STP, USB_RST, XI) + **I2C_SCL** (bridge open — forensics below).
Violations 5 = the 4 standing J1 copper_edge items + 1 track_dangling
(the SCL W chain's severed end at (66.875,6.75) — the bridge's open
end; same item the SCL unconnected pair names).

**CAP_CLK and CAP_DATA are CONNECTED.** Delta vs exp240: unconnected
7→6, violations 4→5 (the +1 is the SCL dangling end, a named
consequence of the pocket re-fan, not collateral).

## How the landing was actually built (differs from the brief's H5)

- The brief's H5 piece (1) said X2 → ~(71.5,27.5). The corrected
  pad-aware site scan (t_aw3 v2 — see the item_margin finding below)
  found NO legal site in x69–75 × y23.75–30.75 in either rotation
  (the CDR F fanout threads the whole band). X2 went to the far site
  **(75.75,32.25) rot0** (model margin +0.431, courtyard OK).
  REFCLK re-laid from the surviving staircase via (71.875,23.375) to
  the new pad (76.8,31.425); both +3V3D pads re-linked via a shared
  via (71.7,24.2) to the old web terminus (70.45,22.425).
- The waist lock (av's dip-vs-ride) broke by **composing the RBIAS
  ride FIRST, then the XO dip** (t_aw9): dip vias (71.75,20.55),
  (70.95,18.5); worst gates +0.000/+0.013/+0.016/+0.025. The ride was
  later REPLACED in the repair round by a direct In2 leg (below), so
  the shipped board has neither the dive via nor the B hop.
- DM_PHY's severed In2 span re-laid at **hw 0.10** (t_aw10) in the
  wider box — note the pair asymmetry vs DP_PHY's 0.125 for the
  final report.
- Join 2 (+3V3D stub at C28) resisted five campaigns (t_aw13 A/B/C,
  t_aw15 DM-rip joint, t_aw16 ULPI_NXT re-lay, t_aw17 C28 W/SW scan —
  zero legal 0603 sites). Closed by **shrinking C28 0603→0402 AND
  moving it (73.5,20.5)→(73.25,20.75)** (t_aw18): stub journey worst
  gate +0.001. C22 and C24 also shrunk 0603→0402 (centres unchanged)
  per the brief. Paperwork moved in the same commit series:
  hw/circuit.py (new C0402 constant; C22/C24/C28), docs/08-parts-lock.md
  rows C22/C24/C28. CONNECTIONS.md carries no footprint data for
  these parts (checked — value prose only, unchanged).
- Build: t_aw19 (v1) from build_aw1.json (t_aw18 manifest) onto
  exp241esc; repair round via t_aw28_modfix.py (manifest v2) +
  t_aw29_build2.py (builder v2) + t_aw39 (clk_via removal).

## Findings (mechanisms, all evidence in scratch/work/aw/)

1. **item_margin pad-subject blindness** (t_aw3b): the au71 helper
   returns the 9.9 sentinel for any non-seg/via SUBJECT — pads as
   subjects are silently "clear". All au/av journey gates used
   seg/via subjects (their results stand); the first X2 site scan
   (863 "legal" sites) was VOID. Correct pad test: perimeter+centre
   sampling vs dist_to_item − pair_clr, plus key-point-in-rect.
2. **fragments() tolerance joins** (au97 execs with "< 0.04"): the
   model unions endpoints within 0.04 mm INCLUDING across layers
   with no via, and does NOT join a track ending inside a pad rect
   away from its centre. Three exp241 v1 defects traced to this
   (heal2's B-run start 0.035 from an F stub; the (68.375,17.5)
   F/B coincidence; U9 SCL pad). KiCad DRC is the arbiter; any
   model join whose endpoints are not exactly coincident on a
   shared layer or via must be re-examined before building.
3. **SWIG proxy identity** (t_aw19): board.Remove() must be called
   on the SAME proxy objects matched during the scan — comparing
   id() across two GetTracks() iterations removed ZERO items in the
   first build (reload census diff exposed it: exactly the rip
   counts). Collect victims, Remove them directly, keep the dead
   proxies alive in a _DEAD list.
4. **au97 namespace trap** (t_aw13): t_au97 creates its own inner
   exec dict; helper __globals__ point THERE, not at the caller's
   dict. Model-state replacement must patch every namespace (the
   working replay preamble is t_aw18 lines 1–~50 — copy verbatim).
   fragments()['items'] elements are (layer, item) PAIRS.
5. **Same-net via proximity is invisible to the model** (viafit and
   clearance fields skip same-net items) but KiCad enforces hole
   spacing (≥0.2495) regardless of net. Builder v2 implements
   via-snapping (≤0.45 mm → snap to the existing same-net via
   centre, in the vias list AND every run's pts). exp241 v2 build
   snapped 9 vias, incl. scl_ffan's (69.3,1.25)→(69.35,1.4) merger
   with the FIXED via.
6. **GND orphan islands** (t_aw22/23/26/27/30): exp241 v1 had 4 new
   GND zone↔zone pairs. Mechanism: a fill island whose only ties
   are a lone decap pad + tracks to via-less islands is its own
   group — connection to main requires a via to the In1 plane.
   The 4 orphans: islands holding {C46.2,C38.2}, {C28.2} (orphaned
   BY the C28 move), {C22.2} (orphaned BY the C22 shrink),
   {U6.38}. Healed by 4 measured stitch vias: (68.17,23.51) d0.6
   gap +0.080; (73.518,21.05) d0.5 +0.038; (73.434,17.685) d0.5
   +0.040; (73.725,2.816) d0.5 +0.058 (gaps beyond the 0.2 default;
   note the C28 stitch sits inside the 0.25 POWER-class census band
   — a census adjacency, not a DRC violation; DRC clearance is 0).
7. **TMP_ALERT fixed route vs shifted U9** (modfix M0): au's FIXED
   TMP vertical at x65.7 was gated against the UNSHIFTED U9; with
   U9 at −1.25 its pad1 (SCL) rect reaches x65.8 → dead short with
   SCL (exp241 v1: 2 shorts + mask bridge + 1 clearance). Vertical
   moved to **x65.45** (margins +0.050/+0.025/+1.130).
8. **CAP_CLK via (70.2,1.8) is a pure F junction** (t_aw38/39):
   clk_exit_frun (F) and the U6 patch seg meet there; clk9's B run
   starts at (69.55,2.7) via the manifest's extra B seg. The via
   connected on one layer only → via_dangling. REMOVED (t_aw39);
   builder v2 no longer emits it.
9. **XO B spur chain** (t_aw23): the 8-seg B chain from the ripped
   via (71.875,19.625) to the kept start via (71.625,25.625) is a
   pure spur (degree-2 joints, no branches) paralleled by the dip.
   Ripped in manifest v2.
10. **SDA via (69.05,2.05) has NO legal alternative site** (t_aw31
    disc packing + directed probes): N fails vs the CAP_CLK exit
    via at −0.349 exactly; E/S/W fail vs clk_exit seg / SCL fixed
    via disc / PG staircase diagonal. Shrinking it was rejected
    (fab spec). Instead **PG_3V3's staircase tail was re-laid**
    (modfix M1, journey pg_fix): rip the tail seg + the 6.25 mm
    south vertical (68.625,1.875)→(68.625,−4.375), A* B-locked
    re-lay (68.375,2.125)→(68.625,−4.375). The SDA via never moved.
11. **RBIAS direct In2 leg** (modfix M2): with the pocket in its
    final state, RBIAS runs (73.875,11.625)→(69.625,20.625) on In2
    alone — no dive via (69.925,20.475), no B hop. This designed
    out the last hole_near_hole pair of the composed ride.
12. **Two VM replacements hit this session** (t_aw11 killed ~311 s
    in; t_aw27 killed mid-search). KiCad restored both times via
    the PPA network install (recipe in the session record; the
    toolchain kit remains flaky — still owed).

## exp241 referee trail

- v1 (t_aw19 build): DRC 15 unconnected / 42 violations (11
  hole_near_hole, 7 track_dangling, 6 silk_overlap, 5
  silk_over_copper, 4 J1, 3 clearance, 2 holes_co_located,
  2 shorting, 1 mask bridge, 1 via_dangling); check_pcb 9 nets /
  census 114 / courtyard 0. Every class diagnosed to a mechanism
  (above) — no gate was loosened anywhere.
- v2 (t_aw29 build, manifest v2): DRC 6 / 6 (4 J1 + via_dangling
  clk_via + SCL track_dangling).
- v3 (t_aw39 removes clk_via): **DRC 6 / 5; check_pcb 6 / census
  109 / courtyard 0.** Silk zero (builder v2 copies the old
  footprints' refdes/value positions onto swaps + 3 named refdes
  moves: R13→(80.75,32.2), FB1→(71.8,28.3), C26→(64.2,4.9)).

## I2C_SCL BRIDGE — OPEN (the one CAP-district residual)

Board state: SCL = {U4.20, U6.136, U9.1 pocket+E web} vs {R20.1 +
W chain + N In2 seg to via (69.625,12.625)}. The split was created
by the au71 pocket re-fan (the original In2 diag staircase was
ripped for the CAP funnel). A bridge from the W chain's severed
end **(66.875,6.75)** (In2) to the pocket (goal: FIXED via
(69.35,1.4)) was searched exhaustively:

- ML A* (all layers, hw 0.10, 0.025 grid) from BOTH fragment-0
  anchors ((66.875,6.75) and the N via (69.625,12.625)) to the
  goal on ALL THREE layers, box (62,72,−2,14): **NONE ×6**.
  In2-locked and small-box variants: NONE. A* is complete on its
  grid — no hw0.10 path exists in the current fence configuration.
- Field forensics (t_aw34/35/36/37): the corridor is fenced by a
  STACK — GND In2 staircase (66.6–67.4, 4.1–5.9) + GND via
  (66.2,6.5) r0.3 collar; U14's F pads at x66.3 (THR_DAC/HV_DAC/
  GND, y5.25–6.25); CDR_LOL's B band path (vertical x67.875,
  y4.625–6.375); data_entry's In2 diagonal (69.9,3.175)→(63.85,6.3)
  and clk9's B diagonal ((69.55,2.7)→(64.75,16.95)) near-parallel
  ~0.62 mm apart — **viafit is ZERO in (64–70, 3–6)** (a via needs
  ~0.9 mm; the pair leaves 0.62). The B south corridor (row y−0.5,
  column x69.35) is track-open but unreachable: every layer-change
  column into it is fenced (x65 patchy + B-side LOL/GND minefield;
  x67/68 viafit only at y<−0.4, themselves unreachable).
- Fences that were TESTED as movable and are NOT: data_entry
  (re-lay S with virtual obstacles: NONE In2-locked AND NONE ML —
  HV_SHDN's In2 seg at (63.375,6.125)→(63.625,5.875) pins its W
  end; t_aw28 M3-pre), ULPI_NXT's diagonal (t_aw16), DM_PHY (ripped
  entirely in t_aw15 — bridge still NONE).
- NEXT GEOMETRIC CHANGES TO TRY (posture-law handover, in order):
  (a) **Joint fence move for a viafit window at ~(67.6,5.1)**: the
      window needs ≥0.575 plan distance from BOTH the GND In2
      vertical (67.375,5.125)→(67.375,4.125) and CDR_LOL's B
      vertical (67.875,6.375)→(67.875,4.625). At the best candidate
      (67.5,5.0): F +0.285 ✓, In2 −0.200 (GND seg), B +0.050 (LOL
      seg) — both binding fences must move ~0.3–0.5 (GND web W via
      In2 A* re-lay between (66.125,6.375) and its via (67.375,4.125);
      LOL band path E via B A* re-lay between (67.075,6.875) and
      (69.3,3.58) — its E detour fences: clk9's B E-end + exit-via
      area (69.075,2.8)/(69.55,2.7)). Then bridge: dive at the
      window, F south run at x≈67 to the fanout join (66.5,1.63)
      (F column x66.3–67 probed open y5→1.63 except U9's W pads).
  (b) **Move the GND via (67.375,4.125)** S/E and re-lay its F segs
      (67.375,4.125)→(67.625,3.875)→(68.25,3.5): opens the In2
      y3.4 passage S of the staircase (currently +0.03/+0.13
      sub-legal at the via's r0.6 track-exclusion). F re-lay fences:
      U9's E pad column (rects to x67.275, y≤3.875) — the first F
      seg must thread E of x67.275 at y3.8+; quantified tight.
  (c) **Re-place U14** (the x66.3 pad column is the corridor's W
      wall on F): biggest blast radius (THR_DAC/HV_DAC/GND/+3V3A
      webs), frees the whole F W column.
  (d) Re-lay clk9's B run N of its line (fences: LOL's B web) or
      data_entry onto F (fences: heal1 at (68.85,~3.9), THR_DAC's
      F web) — both probed hostile, not proven impossible.
- data_entry was restored VERBATIM in manifest v2 (worst pair
  +0.035 vs HV_SHDN is the original journey's own margin) — the
  open item carries zero gratuitous change.

## Queue handovers (post-landing board state)

2. **CDR_LOS**: endpoints U4.22 (68.69,36.5) ↔ U6.75 (92.66,1.75)
   unchanged. District changed since the exp234 survey: U9 at
   (67.0,2.75), CDR_LOL's B vertical at x67.075 (pass 207) with its
   band path through (67.875,6.375)→(67.875,4.625)→…→(69.3,3.58);
   re-survey before designing.
3. **PHY_1V8A**: t_aj7 design stands but RE-GATE every coordinate —
   the district mouth changed: C22 is now 0402 (pads (72.02,18)/
   (72.98,18)); REFCLK now arrives from X2's far site (75.75,32.25)
   via a relay crossing N of the knot; XO's dip tail occupies
   (70.95,18.5)→(68.875,20.375) on In2. Door-1's SCL via is at
   (69.625,12.625) on the board, unchanged — it belongs to SCL's
   OPEN fragment 0; moving it per t_aj7 is still fine (it stays
   SCL's anchor either way) but note the SCL bridge (above) may
   want the same neighbourhood — coordinate the two jobs.
4. **STP/XI/USB_RST**: unchanged brief (C20 shrink authorized).
   Note X2's REFCLK relay and C28's move altered the y20–24 field
   E of the knot; re-gate the quadrant arithmetic on exp241.

## Session mechanics

- Evidence: scratch/work/aw/t_aw1..t_aw39 + outputs, build_aw1.json
  (v1 backup build_aw1_v1.json), state_aw.pkl / state_aw2.pkl,
  x2_sites.json, this file. The stitch experiment board was moved
  to scratch/work/aw/exp241stitch-test.kicad_pcb (evidence, not a
  deliverable).
- Two VM replacements survived via checkpointing (state cache
  t_aw12 is why the H5 model survived the first).
