# DISTRICT-STATUS-3 — U7 south district / PHY_1V8A (aj session, 2026-11-07)

Frontier re-verified on exp221 (both referees, baselines in
scratch/work/aj/: drc-exp221-baseline.json, check-exp221-baseline.txt,
census-baseline.txt): KiCad 15 unconnected / 154 violations
(silk_overlap 66, silk_over_copper 78, copper_edge 7, silk_edge 2,
holes_co_located 1); check_pcb 13 nets, census 109 identical line
set, courtyard 0, blind SH1-only. KiCad had to be restored via the
PPA network install again — the toolchain kit FAILED with the same
mode (apt "Unable to fetch some archives" from cached debs, even
as root with env HOME=/home/hatch). Kit fix still owed.

## TOOLING BUG FOUND + FIXED (read this first)

`t_ai_lib.in_box_pool` dropped any pad/via whose CENTRE lay more
than `pad` (1.2) outside the scan box — even when the pad's copper
reached inside. U7's EP (GND, centre (76,14), half-size 1.55,
copper to y12.45) vanished from a viascan box ending at y12.5,
fabricating feasible XO via points at y12.5 with margin +0.015
(true margin −0.450, probe t_aj3). Fix: pads/vias are now included
iff their bounding circle comes within `pad` of the box
(over-inclusive = safe). Regression test t_aj1_pooltest.py (EP in
pool; (75.5,12.5) correctly −0.450; goal dive still +0.160).
Blast radius: only scans whose box edge passed within ~2.05 of a
large pad's centre while evaluating points near that edge. The ai
session's load-bearing scans (PHY start box y1=13.5, midfield
y1=13.2, goal boxes) all included the EP and are unaffected;
the XO re-dive scan box y[9.9,11.3] excluded the EP but its copper
ends at y12.45, >1.1 from every evaluated point — also clean.
All aj-session scans below use the fixed pool.

## PHY_1V8A — DESIGN SOLVED, BANKING BLOCKED BY XO (proof below)

### The solved design (gate-verified, t_aj7_phyproof.py, all gates ≥ 0)

Rips: XO tail only (F stub ×2, via (76.0,10.625), B chain ×2) —
plus SCL via (69.625,12.625) and +3V3D via (70.875,12.625), both
re-placed in the same design.
- PHY_1V8A F stub (75.75,11.562)→(75.72,11.0)→via Vp2
  (75.7375,10.75) d0.5/drill0.3 (worst gate +0.001, the exit pinch;
  the via itself +0.022 on F).
- B journey w0.2: Vp2→(75.3,11.35)→(74.9,11.75)→(74.2,12.25)→
  (73.5,12.55)→(73.3,12.2)→(73.22,11.94) [the RBIAS/XO via gate:
  RBIAS via (73.875,11.625) d0.6 excl 0.60, XO via (72.625,12.25)
  excl 0.55, gate point margins +0.10/+0.15] →(72.92,11.62)→
  (72.35,11.65)→(71.9,11.95)→(71.3,12.1)→(70.7,11.85)→
  (70.3,12.15)→(70.2,12.5)→(70.18,12.75) [door-1 gate: between
  SCL's moved via and +3V3D's shrunk via, margins +0.06/+0.08]→
  (70.1,13.3)→(70.0,14.3)→goal via (69.9375,15.375) d0.5
  (+0.160, disc overlaps C23.1's pad on F).
- I2C_SCL: via (69.625,12.625) d0.6 → (69.5,12.75) d0.6 (centre
  fully inside R20.1's pad rect x[69.025,69.825] y[12.275,13.225]);
  F stub (69.675,12.75)→(69.5,12.75); In2 (69.5,12.75)→(67.0,12.7)
  →(65.0,12.5). Worst gate +0.008 (B, vs +3V3A fence seg
  (68.875,12.375)→(68.375,17.5)); trunk margin +0.025.
- +3V3D: via (70.875,12.625) d0.8/drill0.4 → d0.5/drill0.3, same
  centre (precedent: pass 191's +3V3A Q via is d0.5 on a rail).
- NOT needed: the +3V3A feed re-lay (it served only XO's dead F
  route) and the far-west In2 trunk crossing (the In2 journey is
  dead at the start pocket: XO In2 vertical x73.125 + BIST fence +
  +3V3A In2 chains; the west band dead-ends at the NXT/SCL maze —
  floods in t_aj session, blockers named).
- A second B journey (southern loop: gate pocket south exit →
  (73.0,13.0) → around +5V via (72.2,13.1) at (72.4,13.85) → south
  around +3V3D fence-end via (70.875,15.875) → goal via from the
  SE) was hand-derived with margins +0.001..+0.08 but NOT
  gate-verified; door-1 above is the verified one.
- Groute (t_ab2) pad-to-pad returns NO PATH for PHY_1V8A even on
  the fully prepped trial (trial3): its 0.125 grid + EPS 0.004
  cannot thread the +0.001..+0.03 margins. Hand-lay + in-model
  gates is the only vehicle in this district.

### Why it cannot bank yet: the notch admits ONE via, and it is XO's

1. With XO's tail ripped, PHY_1V8A d0.5 viascan over the start box
   has exactly TWO feasible points: (75.7375,10.75) +0.022 and
   (75.9875,10.625) +0.008 — 0.28 apart. Two d0.5 vias need ≥0.70
   centre distance. The notch fits exactly one via. (The same
   holds a fortiori with the tail in place: ai session, zero.)
2. XO cannot dive anywhere else: viascan (tail ripped, PHY via at
   Vp2) over x[74.2,78.2] y[9.6,11.2] = ZERO. SE lobe is
   triple-sealed: F by PHY_1V8's stub corner (77.25,10.75) + P via
   (77.8688,10.0563) (best miss −0.04..0.0 tangent), In2 by
   +3V3A's S1 endpoint (76.625,10.25), B by PHY_1V8's B return
   first seg (77.35,10.0)→(76.8,10.9875) (best miss −0.028).
3. XO cannot rejoin on F westward: the band south of the row is
   C16, U7's +3V3D decap, centre (76.0,9.75): C16.1 [+3V3D]
   (75.225,9.75), C16.2 [GND] (76.775,9.75), pads 0.90×0.95,
   rects y[9.275,10.225], x[74.775,75.675]∪[76.325,77.225].
   XO's westward line must clear C16.1's SE corner (75.675,10.225)
   by 0.35 (track) and PHY's notch via by 0.55: corner-to-via
   distance is 0.529 < 0.90 — sealed. Same at C16.2's SW corner vs
   the via (0.788 < 0.85). XO's pad flood with tail ripped = 83
   cells, closest (76.312,10.562).
4. XO cannot rejoin on In2: its own vertical x73.125 is fenced
   from the start pocket by RBIAS's In2 vertical x73.875
   (y[11.625,16.375]) and, around RBIAS via's south end, by
   +3V3A's via (73.625,10.625) d0.8 (excl 0.75; the y9.8 underpass
   leads only to BIST's staircase fence). Flood: NO PATH,
   blockers RBIAS segs −0.081/+0.104.
5. C16 cannot shift on its row: west ≥0.5 needed to matter, but
   C21.2's GND pad (73.525,9.5, east edge x73.975) caps the shift
   at <0.5 (0.5 → pad gap 0.30, and the triple gate C16.1 corner /
   C16.2 south edge / PHY via still seals by exact arithmetic —
   session notes); north is blocked by +3V3A's via (75.625,8.625)
   d0.8 (lands inside C16.2's rect), south by the row pads
   (gap 0.247 < 0.35 at y10.2), east worsens the via gate.

### Resolution options (parent/user decision)

(d) SE-lobe re-solve (routing-only, hardest): joint re-lay of
    PHY_1V8's B return first seg + +3V3A's S1 joint (76.625,10.25)
    + P/Q micro-adjustments to open an XO dive around
    (76.5,10.4)–(76.7,10.6). Needs the via-position optimizer over
    all five variables; pass-191's geometry is the thing being
    spent. Not attempted this session.
(e) Relocate C16 off the row (placement): all row sites blocked
    (proof 5); a site in the west district along the +3V3D web
    (e.g. near R21 (73.75,7.75)) needs a placement study + C16's
    +3V3D/GND webs re-laid; U7's +3V3D decap moving ~30 mm is an
    electrical judgement call for the user.
(f) Leave PHY_1V8A or XO unconnected — user decision only.

Until one of (d)/(e)/(f) is chosen, PHY_1V8A stays open and XO's
tail stays EXACTLY as banked in exp221. The t_aj7 design is ready
to emit verbatim the moment XO has an answer that frees the
notch, OR to be re-gated against whatever (d) produces.

## Also recorded

- +3V3A feed re-lay coordinates (from the dead XO F design, kept
  for the record): new via must sit EAST of ULPI_CK's In2 vertical
  x74.625 — (74.7,10.75) fails In2 at −0.550 (on the vertical);
  (75.25,10.75) clears CK and RBIAS's pad. F seg from the
  (75.125,11.125) joint; B seg north to the w0.6 horizontal.
- SCL's pair clearance is 0.25 (power class in router.netclass —
  both referees agree; the door-1 arithmetic depends on it).
- Session tools: t_aj1 pool regression test, t_aj2 viascan with
  ADDVIA hypothetical-via support, t_aj3 margin probe, t_aj4 emit,
  t_aj5 groute-model probe, t_aj6 full joint build (gates caught
  everything above; nothing emitted), t_aj7 PHY design proof
  (all gates pass). Trial boards on disk: exp221_riptail, trial2,
  trial3 (trial4 was never written — groute aborted before save).
  exp222_PHYPROOF is NOT built (t_aj7 is gates-only by design;
  no board file was saved from it).
