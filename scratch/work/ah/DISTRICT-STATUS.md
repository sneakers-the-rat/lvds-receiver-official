# U7 south-west district — status after pass 189 (exp219)

## Banked in pass 189
- XO U7.27 leg CONNECTED (groute B corridor under the ripped SCL band).
- ULPI_CK, +3V3A (feed pair + staircase + main), I2C_SCL all rejoined after
  the district rip; both referees byte-identical violation tables vs exp218.
- Grout defect class documented: groute's passability skips same-net items,
  so it stacks/near-stacks vias on existing same-net vias and emits stubs
  relying on tangency (via (68.375,17.5) disc tangent to B vertical x68.625).
  After any groute chain: same-net via-pair scan (<0.75 mm) + DRC, budget a
  cleanup that re-anchors path segs onto the EXISTING vias.
- ORDER LESSON: referee after EACH groute job in a district. The +3V3A
  northern groute path sealed ULPI_CK's start (floods met on rip2:
  18,411/18,419 cells; disjoint after). CK must be rejoined BEFORE the
  +3V3A U7.16:C24.1 job, or hand-laid first as done here (t_ah7).

## Still open in the district (all three surveyed to fence precision)

### PHY_1V8A (U7.29 <-> C23.1) — pocket proven, route NOT built
- C23.1's pocket is fenced on every layer/face (full census t_ah5):
  W +3V3A B vertical x68.625 + SCL In2 vertical x69.25; E +3V3D B vertical
  x70.875 (vias d0.8 at y12.625/15.875) + XO In2 vertical x73.125;
  S face R20.2 pad rect (71.075,12.75) [+3V3D], +5V via (72.125,13.625) d0.8,
  SCL via (69.625,12.625); N PG_3V3 via (69.625,16.375) + its In2 staircase,
  DP_PHY B staircase, C23.2 GND pad, GND stitch via (72.0,14.65).
- KEY FACT: a w0.6 +5V In2 trunk at y13.625 spans x[54.125,72.125] (ends at
  the +5V via (72.125,13.625)); it seals all mid-field In2 crossings.
- F south mouth is a proven dead-end saddle (R20.2 rect vs +5V via disc
  exclusions overlap; the one threadable point leads into a strip of
  negative width). In2 entries all sealed; smallest seal = PG_3V3 via vs
  +3V3D via (70.875,15.875): centres 1.346 < 1.40 exclusion sum (0.054).
- Start side: via window V1 (75.875,10.6875) d0.5 gated F +0.004 / In2
  +0.132 / B +0.834 on rip2 — but pass 189's XO B seg (76.0,10.625)->
  (74.125,12.25) passes ~0.046 from V1's centre: V1 IS DEAD on exp219.
  Re-derive the start window against exp219 before any build.
- Unbuilt hypothesis (hand-derived on rip2, MUST be re-gated on exp219):
  move +3V3D's via (70.875,15.875) NE to ~(71.12,15.98) (gates: C23.2 rect
  +0.075, DP_PHY via +0.06) opening the In2 PG/+3V3D saddle by ~0.146;
  descent (70.1,17.1)->(70.28,16.72)->(70.35,16.35)->(70.2,15.5)->V2
  (70.05,14.45) [V2 gates F +0.525 / B +0.025 at y14.45]; +5V trunk crossed
  on F at x63.85 (D8.1 rect W edge 64.225, +0.025) via V3 ~(64.7,16.3);
  mid-field In2 west run must avoid BIST_DRV's southern In2 web
  ((70.375,9.625)->(70.625,9.375) area) and the kept +3V3A via
  (73.625,10.625). A ~20 mm In2 detour around the trunk's west end
  (x<54.125) is unexplored (territory x54-64 un-censused).

### +3V3A U7.25 — sealed; needs the PHY_1V8 south-fanout re-lay
- Start flood = 24 F cells (the pad), no via cell, on every field tried
  (rip2, g5, exp218). Pass 187's seal stands: PHY_1V8 fanout W/S
  (stub/via (77.875,10.375)/B-seg (77.875,12.875)), ULPI_D0 fanout E/S.
- The brief's east dive ~(78.35,11.3) is fenced by D0's staircase
  (-0.09..-0.44 for all candidates). Moving PHY's via SW to (77.5,9.9)
  opens the south fence but PHY's re-laid B run then fences U7.25's via
  candidates on B (-0.2). Solve as ONE computational design (optimizer
  over PHY via position + both nets' layer paths), not by hand.

### +3V3A U7.6 — west-face pocket, fence not yet named
- Start flood 33 F cells on rip2 and g5 alike (not a job-order problem).
  F closest pair (72.750,14.250)->(72.750,13.125), gap 1.125. First step
  next session: capture the probe midpoint blockers at (72.75,13.69)
  (t_ah3b prints them) to name the fence exactly; neighbours: SCL west
  web, +5V F fanout (73.562,13.75)->(72.812,13.75), GND stitch via
  (72.0,14.65), U7 west-row pads.
