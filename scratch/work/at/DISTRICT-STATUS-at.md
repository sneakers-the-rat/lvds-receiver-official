# CAP district — at-session status (2026-11-08, in progress)

## Baseline (re-verified this session, both referees)
exp240 / pass 209, origin 58165c2. KiCad DRC: 7 unconnected, 4 violations
(all J1-intrinsic copper_edge). check_pcb: 7 nets, census 109,
courtyard 0, blind SH1-only (21). Remaining: CAP_CLK, CAP_DATA,
CDR_LOS, PHY_1V8A, ULPI_STP, XI, USB_RST.

## What the as-session handover got wrong (found this session)
- The "keystone gap" (SDA via ↔ HV band east end, 0.866) is NOT the
  binding cut. The binding cut is the SLOT between the HV band and
  SCL's In2 diagonal END (68.875,1.625) / SCL via (69.375,1.375) r0.3:
  edge-to-edge gap 0.459–0.482 vs 0.600 needed for one w0.2 track at
  0.2 clearance both sides. Short ≈ 0.118–0.141. This is exactly the
  flood's 0.100/0.071 bottleneck.
- The handover's HV B-hop topology is DEAD (t_at2c_gate): E-via
  survivors 0/36 (ULPI_NXT F diagonal + PG B vertical + SCL via tile
  the window); hop bottom seg vs PG_3V3 B seg −0.450. PG_3V3's B
  chain is a serpentine wall (band line x+y=70.5 → vertical x68.625 →
  y−4.375 → SE steps → vertical x69.375 → y−6.875 → SW → vertical
  x68.375 → y−9.125). No B crossing north of y−9.125.
- SCL has a redundant F diagonal seg (67.875,1.625)→(69.375,1.375)
  w0.20 IN ADDITION to the F staircase — missed by earlier prose.

## Model iterations (all in scratch/work/at/)
- v2 (t_at6): band jog from V2 + webs out. A* both fail. S=(70.12,0.82)
  ILLEGAL −0.020 vs U6.32 +3V3A pad; S=(70.05,0.82) legal (+0.05).
- v3 (t_at9): NXT via (68.0,0.625)→(68.05,0.30) + full band jog.
  Pre-gate −0.168: NXT via vs DIR **F** seg (67.5,0.125)→(70.625,−1.25).
  The DIR/NXT fanout comb is rigid: NXT via cannot move S (DIR F seg),
  W/NW (DIR via, 0.707 knife already), SE (band + DIR F seg), NE (pads).
  CONFIRMED IMMOVABLE by t_at11b scan + t_at15 pre-gate (−0.244).
  → band jog from V1/V2 is impossible; V2 corner (68.625,0.875) is the
  SCL via's closest band point (0.90) and cannot move SW.
- v4 (t_at10/t_at13): chord (68.625,2.5)→(69.1,1.6)→SCL via + band jog
  from V3 + SDA via (69.6,2.3). Pre-gate −0.165 (SDA via vs U9.5
  +3V3A pad (69.225,2.75)). Widest −0.071 (binds partly artefactual:
  t_at13 left V2V3 seg un-ripped alongside its transition seg).
- v6 (t_at16/t_at17/t_at18): band jog v4+ (rip V2V3 + 5, chain via
  (68.75,0.5)) + SCL via →(69.5,1.35) r0.25 + In2 tail (68.875,1.625)
  →(69.5,1.35) + CLK via →(70.15,1.72). Pre-gate PASSES +0.020.
  A* still fails; widest −0.071; probe (t_at18) at (68.7,1.3):
  band +0.029 | SCL tail +0.069 | SCL diagonal +0.069. The diagonal
  END (68.875,1.625) is the NE fence — moving the via did not move it.
  Slot arithmetic: band line (x+y=69.5) ↔ diagonal-end point (sum
  70.5): 0.707 centreline − 0.125 (band hw) − 0.100 (diag hw) = 0.482
  edge gap < 0.600. THE DIAGONAL ITSELF MUST BEND (chord), and every
  chord descent is fenced by the SDA fanout via (69.32,2.14) — the
  single keystone fence:
  - chord descents die vs SDA via by 0.02–0.35 on In2, B, and F;
  - SDA via's own feasible set is one cluster (69.2–69.35, 1.9–2.1),
    trapped by U9 pads (N +3V3A (69.225,2.75), W GND EP (68.25,2.75)
    1.0×1.6, E CLK via, S SCL F diagonal + In2 diagonal);
  - SCL via pit (69.5,1.35): descents die vs U9.6 pad rect (E),
    SDA via (W), CLK via (SE, thread SDA↔CLK = 0.85 < 1.1 needed).
- U9 NORTH move: blocked — EP (north ≥0.4) hits +3V3A via (69.125,
  4.375) r0.4, which itself has NO legal home (LOL B braid + SPI_SCK
  In2 saddle + EP triple-lock the whole (68.9–69.7, 3.8–5.0) region).
  U9 north 0.25 is the max and doesn't open the pit.
- U9 EAST: SDA pad hits CLK via. U9 SOUTH: into the pocket. NO.

## VM REPLACEMENT mid-session (21:53) — toolchain restored
KiCad wiped; restored 8.0.9 from toolchain kit cache (keyring+sources
per restore.sh, install --no-download from kit debs — 14 s; the
snapshot hook's apt-get update held the system lists lock, crawling;
kit route bypasses it entirely). Baseline re-verified after restore:
exp240 DRC 4 J1 copper_edge + 7 unconnected ✓.

## CAP SYNTHESIS (t_at22–t_at29) — the pair is the problem, not the slot
- v7 (U9 west + chord winner) A* FAILS both nets; widest −0.050 with
  binds scattered at ~−0.045 over the whole map. In v7 the pocket is
  SEALED by my own winner copper (CLK via boxed by SCL via W, S via
  S, DATA+SDA vias N — DATA↔SDA via discs touch exactly, 1.10 apart).
- t_as36 REPRODUCES exactly: CLK-first completes, DATA-second fails;
  DATA-first completes, CLK-second fails. Each single journey is
  LEGAL in the exact model in its ablated fence set (t_at27: CLK-CD
  min margin +0.030 vs SDA via (69.9,0.82); vias +0.000..+0.05 — the
  as A* is NOT buggy; pt_margin ≥ 0 ⟺ field ≥ 0.10).
- CLK's journey NEVER crosses the band: it exits SE under U6's pads
  and rides the triangle at sum 69.65–70.25 (NE of band line 69.5).
  It violates only vs the band's east-end KNOB (69.375,0.125) at
  0.177 — the band east end needs a small SW jog (v4+-style, sum
  69.25) OR equivalent re-lay. The t_as36 ablation removed ALL band
  x<70.2/y<7 — its journeys assume the band re-lays in that space.
- DATA's DC journey ALSO exits east: rides x70.65 south on In2 under
  the pads, 0.15–0.39 from CLK's entry segs (need 0.40). Overlay
  (t_at29): 6,793 conflict cell-pairs, concentrated: (1) entries
  x70.25–70.65 y1.0–1.8; (2) hop vias IDENTICAL (63.75,12.15) and
  (64.95,15.45) — distance 0.000; (3) west ride x64.0 shared line.
- Pair widest (t_at28, CLK fixed): DATA bottleneck −0.046 — with
  CLK's journey fixed, DATA is 0.046 short on every route. The fix
  must move CLK's journey locally (it has +0.13..+0.25 slack almost
  everywhere) or re-lay a fence.
- NEXT (queued): t_at30 sequential A* in the v8 model (band ablated
  x<70.2/y<7, XO web out, +3V3D web out) with CLK routed under a
  STRONG clearance-max penalty, then DATA with CLK fenced. Then the
  band re-lay as its own A* in the leftover space. Fallback named:
  DATA B-layer south ride (In2 dive (70.62,2.18) → B x70.65 →
  (69.9,−1.9) In2) — B corridor fence-checked partially clean.

## U9 WEST 1.0 — JOINT SEARCH LANDED (t_at21_joint3.py)
138,032 joint-feasible {SCL via, chord bend, SDA via} configurations.
WINNER (chosen for build-side heal room):
- SCL via (69.35,1.40) r0.25 (own gate +0.150 — the min, comfortable)
- chord bend (68.8,1.9); chord gates +0.424/+0.312; SLOT SLACK +0.320
- SDA via (69.4,2.2) r0.25 (F stub ~straight E from new pad
  (68.225,2.1); In2 heal NE (69.4,2.2)->(70.2,2.5)->(71.125,1.875)
  clears CLK via (70.15,1.72) by 0.68 and DATA via by 0.72)
- SCL B heal (69.35,1.4)->(69.9,1.75)->(70.875,2.625) clears SDA
  via by 0.65.
NEXT: t_at22 full v7 A* (both orders) for the CAP journeys, then
BUILD exp241 (see sequence in the section below).

## Current attempt: U9 WEST 1.0 (posture-law geometry change)
U9 = temp sensor (pads: SCL/GND/TMP_ALERT west col x67.275;
GND/+3V3A/SDA east col x69.225; EP (68.25,2.75)). West 1.0 →
centre (67.25,2.75); east col x68.225 — clears U8 (pads y≥5.1) by
>2 mm; the whole (68.4–69.9, 1.3–2.6) region becomes pad-free.
Joint search t_at20_joint2.py over {SCL via, chord bend, SDA via}
in that configuration (pool = v6 edits + U9 pads shifted + U9 F
stubs ripped). IN FLIGHT at time of writing.
If it lands: BUILD exp241 = esc + U9 west + SCL/SDA re-fans +
chord + band jog + S via + journeys + heals (SDA In2 staircase,
SCL B staircase, +3V3A 3 groups, GND tree/EP, TMP_ALERT stub,
+3V3D web at U5, XO In2 web) — all in one pass, both referees.

## District ground truth (raw dumps t_at12/t_at19 — trust these)
- U6 west pads x71.338 (rect x[70.598,72.078], 1.48×0.30): y −1.75
  blank, DIR −1.25, NXT −0.75, +3V3D −0.25, GND 0.25, +3V3A 0.75,
  +3V3A 1.25, CAP_CLK 1.75, CAP_DATA 2.25, CDR_LOL 2.75.
- SCL via (69.375,1.375) r0.30 (d0.6). SDA via (69.32,2.14) r0.25.
  DATA via (69.9,3.18) r0.25. CLK via esc (70.02,1.83) r0.25.
  LOL via (70.625,3.375) r0.30. +3V3A via (69.125,4.375) r0.40.
- netclass: CAP/HV_SHDN/SCL/SDA/THR/PG/NXT/DIR/XO/GND clr 0.2;
  +3V3D/+3V3A clr 0.25 (power). Track passable = field ≥ 0.10
  (w0.2), via fit = field ≥ 0.25 (d0.5) in the A* model.
- DIR via (67.5,0.125) r0.25; DIR In2 seg (59.875,7.875)→(67.5,0.125);
  DIR F seg (67.5,0.125)→(70.625,−1.25). NXT via (68.0,0.625) r0.25;
  NXT In2 (60.25,8.25)→(68.0,0.625); NXT F (68.0,0.625)→(70.5,−0.75)
  + stub →(70.625,−0.75).
