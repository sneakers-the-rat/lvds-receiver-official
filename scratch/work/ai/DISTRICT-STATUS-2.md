# U7 SW district status after pass 191 (exp221, origin 2cfc87a)

Written 2026-11-07 by the ai session (passes 190+191). Board state:
KiCad DRC unconnected 15, violations 154 (silk_overlap 66,
silk_over_copper 78, copper_edge_clearance 7, silk_edge_clearance 2,
holes_co_located 1; clearance/shorting/dangling 0). check_pcb:
13 unconnected nets, census 109 (identical line set since exp219),
courtyard 0, blind list SH1-only (21).

## Done this session
- Pass 190: +3V3A U7.6 CONNECTED (see commit 87c0865 for the full
  method: fence named by probe blockers, +5V fanout re-lay, five GND
  fill-island stitch heals). +3V3A now has ONE open pad: none —
  +3V3A is fully connected after pass 191.
- Pass 191: +3V3A U7.25 CONNECTED via the joint PHY_1V8 re-lay
  (commit 6cad741). PHY_1V8's new south fanout: F stub
  (77.25,11.562)->(77.25,10.75)->via P (77.8688,10.0563) d0.5/0.3;
  B w0.6 return via (77.35,10.0), (76.8,10.9875), (76.8,14.9875) to
  the kept run corner (77.8,16.2). U7.25: F stub to via Q
  (77.8625,10.975) d0.5/0.3; In2 w0.6 Q->(76.6,12.15)->(77.375,13.125).
  Do not re-rip these casually: P/Q and the PHY stubs are the fences
  for everything else in the pocket now.

## PHY_1V8A (U7.29 <-> C23.1) — the district's last open net
Re-surveyed on exp221 (all numbers fresh):
- START SEALED on F: exact-model flood (t_ai13, w0.2) from U7.29 =
  204 cells, no west escape; probe-model flood = 24 cells (pad only).
  South fence NAMED: pass 189's XO F tail — via (76.0,10.625) d0.5
  (blocker margin -0.248 at the south midpoint (75.75,10.59)) and
  segs (76.75,11.125)->(76.5,10.75)->(76.0,10.625). The tail passes
  directly under U7.29/U7.28. West: the row pads themselves
  (0.25 gaps). East: pass 191's P/Q cluster. North: EP/D-row.
- ZERO feasible d0.5 vias for PHY_1V8A in the start box
  x[74,78.5] y[9,13.5], and zero in the mid-field box
  x[68.5,73.5] y[10.5,13.2] (t_ai2 on exp221).
- GOAL SIDE OPEN: C23.1 goal flood 627 cells (F 101 / In2 372 /
  B 154); dive cluster at the pad's north edge: best (69.9375,15.375)
  margin +0.16, cluster x[69.75,70.06] y[14.5,15.44] (the via disc
  overlaps C23.1's pad — same net, contact is the join).
- The F band y[13.1,13.875] x[69.25,73.56] (+5V fanout + pass 190's
  +3V3A y13.875 run) seals the pocket's F entry from the north;
  pass 190's +3V3A vertical (69.125,14.375)->(69.125,15.5) seals its
  F entry from the west. The pocket is reachable only by diving
  into the goal cluster (In2 flood reaches x66.12 at y[14.38,15.75];
  B flood reaches y13.12).
- XO cannot simply re-dive: XO viascan x[76.3,77.4] y[9.9,11.3] on
  exp221 = ZERO (pass 191's cluster closed the tail's neighbourhood).
- West dives for PHY_1V8A exist only at x[64,64.5] y[9.5,10.6]
  (best (64.0,9.5) +0.496) — unreachable until the start opens.
- The +5V In2 trunk (y13.625, x[54.125,72.125]) still seals In2
  north-south travel except at its west end (x<54.125, un-censused)
  or east end (XO In2 vertical x73.125 + RBIAS x73.875 fences).

### Remaining vehicles, in order of promise
1. JOINT 3-NET RE-FANOUT (XO tail + PHY_1V8 stub + U7.29 exit) over
   the exact item model, optimizer-style (t_ai11 pattern): move
   XO's tail dive and PHY's P/Q cluster as one system to open a
   y~10.8-11.1 F channel under the south row for U7.29, then the
   west channel + a dive west of x64.5 + far-west In2 trunk crossing
   (census x[50,64] In2 first) + east along y14.4-15.5 to the goal
   dive cluster (69.9375,15.375).
2. The ah session's +3V3D-via saddle move (open the F south mouth):
   the mouth's V1 window stays dead on exp221 (XO B seg
   (76.0,10.625)->(74.125,12.25) unchanged, 0.046 from V1's centre) —
   only viable combined with vehicle 1's XO tail move.
3. B-layer start: U7.29 has no B reachability either (start flood
   F-only in both models) — B helps only after an F exit exists.

## Rest of the queue (unchanged from the brief, all re-verified
## as still open by the exp221 check_pcb list)
SWCLK (U6.109<->J4.4); GND zone<->zone pair (pre-existing, still
exactly 1) + GND U6.38 (island20 in the ai island probe: U6.38's pad
alone on its F island at (73.75,4.662) — a stitch via in that island
is the obvious heal, gates permitting); HV_INTVCC; DP_CON x2
(3 groups); CAP_CLK, CAP_DATA, CDR_LOS, SPI_SCK, SPI_MOSI (all
endpoint-sealed singles); +3V3D U11.14. Parked, do not touch:
ULPI_STP / USB_RST / XI (C20 decision pending with the user).
