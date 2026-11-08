# DISTRICT-STATUS-5 — al session handover (exp227 / pass 197)

## Banked this session
- Pass 194 (exp224): +3V3D U6.39 dive re-lay — zero delta, opens the
  under-U6 fill pocket. Pass 195 (exp225): GND U6.38 island healed
  (stitch via 75.9,-10.45); DRC unconnected 15->14.
- Pass 196 (exp226): SWCLK connected via DAC_SYNC west-dive re-lay
  (dive 87.3,-18.15; SWCLK via 90.55,-18.05, B south approach to
  J4.4); side effect: severed a GND fill pocket south of U6.
  Pass 197 (exp227): pocket healed (stitch via 82.0,-18.075);
  DRC unconnected 14->13, check_pcb nets 13->12.
- Board state: exp227, DRC 13 unconnected / 150 violations
  (silk 144, copper_edge 4 J1-intrinsic, silk_edge 2);
  check_pcb 12 nets, census 109, courtyard 0, blind SH1 (21).

## HV pocket (queue item 3) — NOT landed; seal proven deeper
INTVCC (U10.8 29.65,-3.0 <-> C31.1 31.225,-0.5) is the only open net
in the pocket; GATE/SHDN/FBX are connected and their copper is the
fence. This session's fence arithmetic (exp227, exact coordinates):
- INTVCC's pad is boxed on F: GATE pad 0.2 N, SHDN pad 0.2 S,
  SHDN via (30.875,-2.875) d0.6 track-exclusion disc (r0.60) covers
  the pad's east edge (pad edge point is 0.515 from via centre),
  EP + GND via (28.25,-3.0) W. Via-in/on-pad dead by arithmetic:
  the N-S gap between GATE/SHDN pad edges is 0.70 total; a centred
  via needs r<=0.15. Board min hole 0.3 kills d0.4.
- Every dive via in the ring x[30.4,31.8] y[-3.5,-1.2] is killed by
  a named fence: SHDN via halo (E), GATE needle halo (N), FBX In2
  band y-2.125 + staircase (In2), +5V w0.6 staircase + y-4.0 stub
  (SE, 0.85 via-halo), C31.2/SENSE via (N). Best dead points:
  (31.5,-2.35) F +0.046 / B ok / In2 -0.35 vs FBX; (30.95,-1.35)
  F +0.065/+0.032 but unreachable on F.
- SHDN via relocation: all candidates in x[30.4,31.2] die vs the
  +5V stub seg (30.4,-4.0)-(31.125,-3.875) or INTVCC's pad rect;
  southernmost feasible y is -3.5, and INTVCC's F exit cone needs
  the via at y<=-3.5 with centreline window exactly 0.00 wide
  (GATE pad bound -2.95 = SHDN via bound via_y+0.55). West escape
  dead (EP), via-in-SHDN-pad dead (INTVCC rect 0.35-0.45).
- The needle/SHDN channel at x30.875 is 0.012 too narrow for a
  w0.2 track (centreline window [-2.475,-2.487]); a +0.08 N needle
  shift opens it to 0.068 — but INTVCC's climb to that latitude is
  fenced by GATE's pad SE corner and the via disc's SW quadrant.
- West exit (rip GND EP via + seg (27.5,-3.0)-(28.25,-3.0), both
  proven redundant by ak) dies at the x28.125 GND vertical, then
  at C30.2's pad + SENSE via (29.375,-1.625) in the NW corridor.
Vehicle (unchanged from ak SS4, now 5 nets): joint optimizer over
INTVCC dive/exit x SHDN web x GATE needle x FBX In2 band x +5V
staircase joints, GND EP rip in scope. HV_INTVCC is default-class
0.20 (not in the 1.0 mm HV_NETS list) — gate at 0.20.

## Remaining queue after this session
1. HV pocket joint optimizer (above).
2. J1 pocket: DP_CON A6<->B6 + D3.1 (groute NO PATH standing;
   CC1/DM_CON ~40-seg In2 staircase re-fanout as computational
   design).
3. Long-haul singles: CAP_CLK, CAP_DATA (U6 west face 71.338,1.75/
   2.25 -> U5 west face x76.525), CDR_LOS (U6.75 92.662,1.75 ->
   U4.22 68.688,36.5), SPI_SCK (U8.7 70.7,6.75 -> U6.111
   89.75,-16.663), SPI_MOSI (U8.8 -> U6.113 88.75,-16.663),
   +3V3D U11.14 (56.75,24.812) vs its track end (66.55,22.75).
   All endpoint-sealed; note the north-mouth braid is UNCHANGED
   (the GND heal used the south pocket, not the braid) and the
   SWCLK/DAC district south of U6 now has new copper.
4. Silk campaign: 144 of 150 violations.
Parked (user decisions): STP/XI/USB_RST (C20), PHY_1V8A (C16).
