# DISTRICT STATUS — av session (CAP landing, queue item 1)

Written 2026-11-08 (av, subagent 9e085623). Board UNCHANGED:
exp240 / pass 209, origin 5ac0276. KiCad DRC 7 unconnected /
4 violations (all J1-intrinsic); check_pcb 7 nets / census 109 /
courtyard 0 / blind SH1-only. **No pass banked by av.** Both CAP
joins remain open. Everything below is machine-verified in the
exact item model (au97 machinery) unless marked hand-derived.

## What av verified about the inherited record

- Frontier + both-referee baseline re-run after a mid-session VM
  replacement (KiCad restored via PPA network install, keyring
  fingerprint FDA854F6…A805 verified). Output:
  `check240_full.txt`.
- t_au97 re-run regenerates `build_au97.json` BYTE-IDENTICAL
  (`build_au97_ref.json`, log `t_av0_repro97_out.txt`). The au97
  trap's mechanism: phase2y's TAIL tuples carry hw 0.1 in the clr
  slot (pool items carry 0.2), so exact-tuple rip matching missed
  the 2 RBIAS In2 tail segs; `detour_RBIAS_tail` is a redundant
  parallel B path. RIP BY ROUNDED COORDINATES + victim counts.
- **au's "XO bridge emit-ready" claim is REFUTED.** XB10 (au's
  candidate bridge) crosses arr_data's In2 diagonal
  (70.500,21.000)->(72.300,19.200) at (71.56,19.94), margin −0.398,
  regardless of the RBIAS ride. It could never have emitted
  against the au93/au97 pool.
- au93 pool actually contains **19 RBIAS In2 segs total** (stub +
  vertical + diagonals + tails); every av script ripped all 19 by
  the (broken-in-the-same-way) predicate — states are consistent
  across av runs. The (73.875,11.625) via disc remains; rides
  connect to the disc.
- CAP fragment singletons (U5.5 pad, U6.35 pad, U5.3 pad) are
  endpoint-census artifacts (copper overlap joins the census
  cannot see; t_av5 proved U6.35's link on esc). Not design holes.
- PHY_1V8A exists in the model as ONLY its 2 F pads. U9PADS = 7
  pads exactly as au recorded. Knot footprints censused (t_av7):
  C49 (70.0,19.5), R17 (70.0,21.0), C28 (73.5,20.5), C24
  (68.75,18.0), C22 (72.5,18.0), L1 (66.75,20.5), C38 (67.5,22.75),
  X2 (71.5,23.75).

## JOIN 1 (XO bridge) — refutation map

The bridge exists in exactly ONE form (t_av20/t_av21, fragments
verified == 1, sizes [300]):

- **S-route dip**: B run stub (71.875,19.625) -> via (73.9,21.425)
  (gate +0.000 vs C28 GND pad (74.275,20.5); +0.027 vs CAP_CLK via
  (73.25,21.75)) -> In2 run 354 pts SE/S/W: (75.3,19.43) ->
  (75.03,18.93) -> W along y18.1–18.45 -> NW (71.12,19.15) ->
  (70.12,19.57) -> (69.12,20.05) -> goal (68.875,20.375).
- **RBIAS ride exists solo** (In2 365–368 pts, dive
  (69.925,20.475) or (70.0,20.375), B hop to (69.625,20.625);
  gate +0.000 vs C49 +3V3A pad), fragments(RBIAS) == 1 solo.

**The pair is topologically locked.** The dip's In2 wall and the
ride cross once, in the waist x71.1–72.1, y18.4–19.3, where both
solo paths coincide (gap 0.0–0.23 vs 0.425 required). Entering
the channel N of the dip's run requires crossing the dip's line;
crossing on B is sealed by ULPI_DIR's diagonal
(75.5,17.521)->(71.375,19.125) + re-laid tail (path dumped
t_av26: N at x71.0–71.1 y19.5–22.5, then NW via (69.92,24.0) to
(68.875,29.0)) and PHY_1V8's B journey; crossing on F is sealed
by the knot pad rows. Iteration both directions (t_av23 wall the
dip -> dip has NO second path; t_av32 wall the ride -> dip NONE
at inflations 0.15/0.25/0.40) confirms: exactly one dip path,
exactly one ride corridor, mutually exclusive.

Every other bridge geometry — machine-refuted (A* NONE or exact
field arithmetic):
- Knot dip (single via in the corridor): viafit lens EMPTY.
  Binding fences: R17 GND pad (F), C49 GND pad (F), RBIAS
  terminus via (69.625,20.625) (In2/B), CAP_DATA diagonal (In2),
  DIR tail (B). Best cell (70.525,20.175): F +0.150 (need 0.25).
  Structural cause: 0603/0805 pad rows at 1.5 mm pitch with
  0.95 mm pads leave 0.55 mm channels; a track needs 0.60, a via
  0.90. The 0.55 seal recurs at y20.25 (R17/C49), y18.75
  (C24/C22 vs C49), x-wise at C28.
- C49 moves: 12 legal centres scan-wide (t_av11), top 10 tried
  with web re-lay emitted — dip NONE for all. Small shifts do
  not vacate the lens (the OTHER C49 pad becomes the fence).
- DIR re-lay as dip insurance: works solo (t_av17: succeeds
  without reservation; fails with r0.35 dummy + approach seg;
  succeeds with r0.30 via-only reservation) — but the dip via
  it insured is F-sealed anyway.
- Northern returns from the (73.9,21.45) viafit cells: all In2
  legs NONE — DM_PHY's In2 staircase (68.375,24.375)->via
  (73.625,19.125) + CAP_DATA's W run + ULPI_NXT diagonal seal
  the goal's N/W; the goal is approachable only from S/SW.
- E notch ride (87.5,10.75)->(76.0,10.625): NONE all layers
  (t_av19). E staircase ride ->(73.125,13.5..14.5): NONE ×5
  heights (t_av24).
- West dip via (68.3,20.6) + neighbours: In2 field −0.19..−0.38
  vs CAP_DATA's W-descent segs at (68.0–68.1, 20.575–20.8)
  (t_av29 probe table); B legs NONE (+3V3A fat B seg
  (67.625,20.125)->(67.875,19.875) hw0.300).
- F-via dip from (71.625,25.625): NONE (t_av28). F field map
  (t_av36): the via's pocket is walled by X2's pads (72.55,
  24.575)/(70.45,22.925), REFCLK via (71.875,23.375), clk9's F
  run y21.8–21.9, +3V3D via (71.125,24.375) r0.4. Only exit
  column x≈73.8 is itself interrupted at y21.9–23.1.
- Split rides: 14 dive candidates (t_av21): B legs NONE from
  y15.7–17.4 dives (DIR diagonal + PHY_1V8 B journey); the two
  composed dives (74.0,16.9)/(74.05,17.2) have F-illegal vias
  (−0.323 vs USB_RST pad (74.25,16.438), DM_PHY F fanout).
- C22+C24 shrink (0603->0402, model-level): opens the F track
  channel at y≈18.6 in principle, but the F leg from
  (71.625,25.625) still NONE (X2 pocket above), and the traced
  dive (70.15,18.6) is B-illegal vs DP_PHY's B staircase
  (70.125,18.875)->(70.375,18.625)->(70.375,17.625): −0.398
  (t_av34 — DP B copper not previously censused). The In2 hop
  (70.15,18.6)->goal EXISTS (74 pts).
- X1 re-place: 468 pad-legal sites (t_av27 scan, whole W half);
  XO hops from the 4 best sites to the tail/staircase: NONE at
  step 0.05 (t_av30, 8/8) and NONE at 0.025 for the two best
  (t_av31). The tail's pocket has no W entrance. X1 pads are
  4.5x2.0 at pitch 8.5, centre (85.75,14.0) rot 90; C20
  (76.5,18.5) / C21 (72.75,9.5) are remote by design (C21.1 is
  in frag-1 via the notch leg's F tail overlap at (72.375,10.0)).

## JOIN 2 (+3V3D stub) — independently tested (t_av37)

Phase A (F-only A* term (72.375,21.125) -> X2.4 (70.45,22.925)):
NONE at hw 0.15/0.125/0.10. Phase B (arr_clk tail extensions to
(71.2,21.8)/(71.3,21.75)/(71.15,21.9)/(71.25,21.7)): ALL NONE.
Join 2's fences are the same X2/REFCLK/clk9-tail cluster as the
F pocket. (In the au93 state; with clk9's tail re-planned E and
X2 moved, re-test.)

## The district as it stands (fences NOW)

The knot (x67–76, y17–26) is over-subscribed on all three
signal layers at once:
- F: pad rows tile every latitude (0.55 seals); X2's footprint
  pockets frag-0's F via.
- In2: DM_PHY staircase + CAP_DATA (diagonal + W run + W descent
  at x68.0) + CAP_CLK arrival + the dip/ride crossing.
- B: DIR diagonal + re-laid tail (x71.0 corridor), DP_PHY
  staircase (x70.375, y17.6–19.1) + its x68.875 vertical,
  PHY_1V8 journey, +3V3A fat seg (67.6–67.9, y19.9–20.1).

## NEXT GEOMETRIC CHANGES (named, in order)

**H5 — coordinated district re-fan (recommended; every piece
individually gate-able in the model before building):**
1. Move X2 N (e.g. centre (71.5,23.75) -> ~(71.5,27.5)); re-lay
   its REFCLK web (the (71.875,23.375) via moves with it) and
   +3V3D/GND webs. Frees the F pocket S of X2.
2. Re-plan clk9's tail so its F run crosses y21.8 at x>=74.5
   (phase-B machinery, wider candidate set) — frees the F
   S-run at x71.625. Also re-test join 2 in this state (its
   phase-A channel crosses the same fences).
3. Shrink C22 + C24 0603->0402 (paperwork with the build, as
   C20): F channel at y18.6 (proven track-legal points
   (71.2,18.6) +0.125, (70.3,18.6) +0.126, t_av35).
4. F dip: via (71.625,25.625) -> S x71.625 -> channel y18.6 ->
   dive (70.95,18.5) (B vs DP staircase +0.59 hand-derived —
   RE-GATE in model) -> In2 hop (proven 74 pts) -> goal.
   Ride then runs solo (proven). If the F S-run still fails,
   fallback H1.
**H1 — re-plan arr_data** (manifest journey, free): move its
diagonal/W run to widen the dip/ride waist by >=0.5, then the
sequential pair (dip S-route + ride) separates.
**H2 — re-lay DIR's diagonal** to F or In2, freeing B in the
waist for a ride B-crossing of the dip wall.
**H3 — re-place R17+C49 as a re-spaced pair** (district re-fan
of the knot rows themselves).

## Session notes

- VM replaced twice during av (KiCad restored both times via
  PPA network install; second restore needed keyring chmod 644
  for apt's sandbox user).
- t_av11's first run timed out (3000 s) in an unfiltered site
  scan; fixed with bbox-filtered local pools + coarse-to-fine.
- Scripts: t_av0–t_av37 in this directory (55 files incl.
  outputs). Key outputs: check240_full.txt, t_av1_out.txt
  (census), t_av21_out.txt (bridge closed solo + ride conflict),
  pair candidates in t_av20/t_av22 dumps.
- Queue items 2–4 untouched. Join 2's standalone failure means
  the CAP landing needs the re-fan for BOTH joins, not one.
