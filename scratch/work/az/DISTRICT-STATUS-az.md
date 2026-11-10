# DISTRICT STATUS — az session, 2026-11-09 (handover)

## Frontier after this session
- **Pass 215 BANKED**: exp252, origin/main 6f487d9 (merge c96086a +
  metrics regen). Content: PHY_1V8A notch via relocated
  (75.7375,10.75) -> (75.27,10.33); F stub re-laid via (75.49,10.69);
  B head re-laid via (75.05,10.95) to joint (74.90,11.75).
- Audited delta vs exp251: KiCad DRC 5 = 5 (4 J1 copper_edge + 1
  track_dangling, the standing PHY tail at (71.375,17.625));
  check_pcb nets 3 {PHY_1V8, XI, USB_RST} unchanged; census 109 flat;
  courtyard 0; blind 21 SH1-only. Board census diff: PHY_1V8A only,
  152 -> 153 items (ripped via+F seg+B head+B leg1 = 4; added
  via+2F+2B = 5).
- Build gotcha recorded: ripping only the old head seg leaves the
  journey's first leg (75.30,11.35)->(74.90,11.75) as a DRC
  track_dangling spur (model fragments() counts it joined at the
  shared endpoint). Rip BOTH segs; the new head lands on (74.90,11.75).
- Notch v4 gates (faithful exp251 pool, t_az46): all >= +0.002
  (worst: F stub vs +3V3A pad U7.31). v2 (75.30,10.30) put the via
  0.22 from STP bottom-run tracks -> census 111; v3 (75.22,10.38)
  clipped ULPI_CK's In2 vertical (-0.03). v4 is the compromise point.
  NOTE: design gates for the notch must run on the FAITHFUL pool —
  on the STP-ripped pool the via's STP/CK margins are invisible.

## The remaining problem (3 nets) — what is proven
The U7 south-west braid {PHY_1V8 journey, PHY_1V8A journey+notch,
ULPI_CK web, ULPI_STP south chain, +3V3A S1 In2 web, EP/pad fences}
is saturated. Established by A* in both orders, floods, ablations,
leave-one-out, and ~10 hand designs (all in scratch/work/az/):

- **PHY_1V8 SOLVED at model level** on the notch-moved pool:
  t_az37 — STP chain rip + PHY loop x77.15 (split (77.15,13.0)) +
  PHY A* FOUND (via (71.9,17.8); B journey crosses the STP column
  in the y12.6-12.95 band; gates all >= +0.024) + tail rip ->
  PHY fragments 1. Journey saved: design_phy_astar4.json.
  RE-RUN on exp252 before building (notch moved 0.03-0.05).
- **STP re-lay is the open half.** With PHY's journey placed, STP
  A* = NONE; STP-first A* takes the gap thread (x76.45-76.55,
  y10.8-11.2, gates >= +0.18) and then PHY = NONE. The two nets'
  B crossings are mutually exclusive in every configuration tried:
  - STP west descent: crosses PHY's staircase diagonal AND 1V8A's
    B journey band (y12.2-14.05 snake, x72.9-75.3). NONE even with
    blockers forcing it west and no PHY journey placed (t_az37).
  - STP In2 hop over PHY's east run: via sites killed by the EP
    rect (x74.45-77.55, y12.45-15.55 — no via inside, and the
    channel between EP north edge 15.55 and the pad row 15.998 is
    0.448 < via+clearances), +3V3A S1's In2 seg/node (76.6,12.15),
    and STP's own staircase points (76.05,11.85).
  - STP east re-lay: PHY loop vertical x77.15 (y13.0-15.1) + the
    run's east corner seal it; PHY's run sags to y12.75 at
    x76.6-76.8, fencing a parallel STP run.
  - CK B-hop (to free an In2 crossing): CK via E has no legal site
    (PHY_1V8A pad U7.29 rect, XI pad U7.28 rect, XO F diagonal,
    +3V3A S1 long In2 diagonal (76.625,10.25)->(77.125,13.125));
    CK via W squeezed by +3V3A via (73.625,10.625) r0.4 (needs
    0.90 centre distance), its F chain, RBIAS pad, 1V8A head.
  - PHY In2 hop (to free STP's B column): hop vias fenced by U7
    west F pads (.5 rect y13.812-14.688 needs 0.45), the EP, PHY's
    own vertical x73.65, and 1V8A's (73.35,13.55) point.
  - PHY southern crossing (t_az43): dies on 1V8A's densified snake
    (x72.9-73.5, y12.2-14.05) and RBIAS via (73.875,11.625).
  - 1V8A journey B->In2 (t_az41): dies on ULPI_CK's In2 vertical
    (continuous y6.375-13.5 — no crossing south of 13.5 except
    below 6.375), XO's In2 journey (72.4,10.1), +5V In2 rail
    (y13.625 + via (72.2,13.1) r0.4) at the C23 approach.
- **XI**: binder set = {PHY_1V8A notch (now moved — retest),
  ULPI_CK In2 y13.5 horizontal, XO F diagonal} (LOO, t_az13).
  Exactly ONE legal d0.5 via exists in box x[70.5,77] y[8.5,13.5]
  on the faithful exp251 pool: (75.2,10.2), margin 0.000
  (t_az24 exact scan) — re-scan on exp252, the notch move changes
  its B binder (+0.019 was vs the OLD notch via). Proven pieces:
  CK In2 jog x74.55 (t_az28, clean, worst +0.125), XO jog x76.62
  (t_az19, clean >= +0.025). XI's F feed via->U7.28 failed against
  XO's rejoin diagonal in both jog variants — search feed x XO
  rejoin as one coupled pair, or A* the whole XI problem on the
  exp252 pool with CK jog + XO jog pre-applied.
- **USB_RST**: untouched this session beyond ay/az diagnostics:
  binding is JOINT/distributed (LOO: restoring any single one of
  24 nets leaves it routable; south box or north box mega-rip
  alone insufficient, both together FOUND: dive (74.125,16.375),
  ride x74.125, via (74.125,6.0), arrive U6.40). Next: bisect by
  district/group restores; DM_PHY F loop coupled re-lay named.

## Untried levers for the successor
1. **t_ab2_groute on a prep board** (DRC-rule engine, 0.125 grid):
   rip STP's south chain + PHY's loop on a prep copy of exp252 and
   groute ULPI_STP U7.13->U6.26 and PHY_1V8 C22.1->U7.15 in
   sequence (either order). Its via/pad geometry is DRC-exact,
   slightly looser than the strict item model in via-vs-pad cases.
2. **C23 relocation**: kills 1V8A's west journey, freeing the west
   B band for STP's descent. The (79.5,11.5) site is DEAD (ULPI_D1
   F web occupies it — pad-subject scans return the 9.9 sentinel;
   gate sites with seg/via subjects or rect arithmetic). The east
   district is dense (D0-D7 webs, NRST, +3V3D column x81.0);
   survey rot90 sites south of U5 / east of x80 with exact rect
   checks, and re-plan D1's F web if a site needs it.
3. X1 relocation (XI), U5 relocation — still untouched.
4. On exp252, re-run the t_az24 via scan in the pocket box: the
   notch move may have opened a second legal via site.

## Corrections to earlier records (board-verified this session)
- "STP via (75.8,10.15)" in pass-214 records was an A* journey
  waypoint, not a board via. Board STP vias: (70.25,-2.2),
  (73.45,-3.3), (73.55,-1.25), (77.0,9.6), (77.35,7.75),
  (76.065,17.96), all d0.5.
- The +3V3A S1/S2 web south of U7 is on In2, not B.
- PHY_1V8's south loop chain (77.25,10.75)->(77.55,10.35) is on F;
  the B loop is via (77.9,10.08) -> (77.45,10.10) -> (76.95,11.05)
  -> x76.95 vertical -> (77.8,16.2).
- fragments() in the au71-derived harness returns a LIST of dicts
  with 'items'/'terms' keys (not a dict); journeys that end inside
  a pad rect count as separate model fragments while check_pcb
  counts them joined — gates, not fragment counts, are the truth.
- load_board_pool verified faithful: pool via set == board via set
  (328 vias).
