# SH1 shield-can fix — proven geometry and plan (2026-11-10)

## The defect
SH1's solid Harwin can (no aperture) is centred (16,40) and D1, the
Excelitas C30737 APD, sits fully underneath it at (8,40). The APD
senses through its top face: as placed, the receiver is blind.
Found by the user 2026-11-10 17:38.

## Evidence in hand
- Harwin clip drawing S1001-46R ISS 6 / DRG-02154 (read via the
  Mouser datasheet link; PDF fetch from Mouser by curl times out):
  clip 4.50 long x 0.75/0.65 wide, height 0.90/0.75, for 0.15-0.20
  cans. RECOMMENDED PAD LAYOUT: 3 pads 1.50 / 1.10 / 1.50 wide,
  0.30 gaps, span 4.75/4.65, depth 0.90/0.75. No pad-to-wall
  locating dimension is printed; the clip's long axis runs along
  the wall and the wall centres on the pads.
- Harwin can drawing S02-XXXXXXX0 Rev 9 / DRG-02145 (PDF archived:
  results/partsfix/datasheets/harwin-s02-can.pdf): A/B are
  centre-of-material; wall 0.20; C = internal height. Stock cans
  have NO bottom-edge cut-outs (the clip drawing's cut-out is for
  custom cans). Note 4 recommends S1001-46R for these cans.
  Table 2 sizes include S02-25200300 (25x20x3.0) and
  S02-20150300 (20x15x3.0).

## Measured board geometry (canonical board, pad rects)
- D1 pads east edge x=9.50; body east 9.75.
- U1 (OPA657) pads west x[12.55,14.50], east x[17.50,19.45].
- U2 (THS4304, SOT-23-5) pads x[23.20,26.80].
- U3 (LMH7220) pads west x[34.20,35.52], east x[36.48,37.80].
- C33 (APD_K filter, 1206): pads y[27.60,29.40]; pad1 APD_K
  x[10.53,11.68], pad2 GND x[13.48,14.63], body between.
- South PSU row north pad edges: R38 47.02 (x 18.8-21.2),
  R39 47.52 (x 23.5-26.0), C39 48.52, C40 48.77, R6 49.52.
- R8 (POST_OUT->CMP_IN) pads x[29.02,31.48] y[37.27,38.23].
- C44 (+VA decpl) body x[31.68,32.33], pads x[30.77,33.23]
  y[39.52,40.48]. C2 (+VA decpl) pads x[31.02,33.48]
  y[41.52,42.48]. The U2-U3 gap's clear vertical channel is
  only ~0.2 mm wide (R8.2 pad west 30.68, C44 body east 32.33).

## Proven negatives (solver + hand checks, sh1_solve.py)
- 25x20 can over U1+U2 excluding D1 and U3: impossible — the
  U1-west-pad to U3-east-pad span (12.55..37.80 = 25.25) exceeds
  the 25.0 wall pitch; any east wall either crosses U3 pads or
  the west wall crosses U1 pads / D1.
- 20x20 can: pincer — C33 (north, y to 29.40) and the PSU row
  (south, y from 47.02) are 17.6 mm apart in the worst x bands;
  can is 20 tall. No centre passes (solver: 0).

## The plan (20x15 can + three small relocations)
1. Relocate the three U3-support passives parked in the U2-U3
   gap (electrically neutral-to-better — C44/C2 are U3's +VA
   decouplers, currently ~4 mm west of the +VA pin it serves).
   Targets from the 2026-11-10 relocation census:
   - R8 -> (30.25, 35.90), north within the gap: pads
     x[29.02,31.48] y[35.42,36.38]; east wall band [31.65,31.95]
     clears pad east edge 31.48 by 0.17. Webs: POST_OUT stub
     jogs north from (28.18,37.75); CMP_IN riser at x=31.07
     extends north from y 38.50 to 35.90.
   - C44 -> (38.6, 44.3), east of U3 (open strip x 38-40,
     y 43-46; C43 at (40.75,44) is clear of it).
   - C2 -> (38.3, 45.9), just south of C44's new home (clear of
     C43 pads y<=44.5 and C25 pads y>=46.5).
   +VA/GND webs re-lay at surgery time against DRC (the +VA In1
   run ends at (37.73,39.98); C10 at (38.25,36) is the nearby
   +VA/GND precedent).
2. Fit Harwin S02-20150300 (20x15, 3.0 internal height — same
   clearance over U1 1.75 max / U2 ~1.1) centred approx
   (21.8, 37.2): walls x 11.8 / 31.8, y 29.7 / 44.7. Windows:
   cy in [37.05, 37.35] from C33 (north wall >= 29.55) and R2
   (south wall <= 44.85); cx from D1/U1 west and the cleared
   gap east. Re-run sh1_solve.py with R8/C44/C2 excluded to
   confirm the final centre and clip windows before surgery.
3. Six S1001-46R clips (footprint HARWIN_S1001, written):
   two per long wall, one per short wall, positions from the
   solver's clip windows (west clip must dodge the APD_A track
   crossing x=11.3 at y[38.50,38.75] and APD_K at y~30/38.6 —
   final windows from the solver).
   SH1 footprint: SHIELD_CAN_S02_20150300 (WRITTEN 2026-11-10:
   outer 20.20x15.20, centreline 20x15, NO drawn courtyard —
   check_pcb fallback reports parts beneath). The
   SHIELD_CAN_S02_25200300 footprint written for the abandoned
   25x20 plan stays in the library unused, labelled with its
   provenance (same precedent as XFMR_EFD20_SMD10); likewise
   SHIELD_CAN_26x20 is orphaned by the swap. Neither is deleted
   (no-delete rule).
4. Design data: circuit.py SH1 value -> S02-20150300 + new
   footprint name; add CL1..CL6 "Harwin S1001-46R" (mech region,
   pins 1/2/3 = GND). Regen schematic, check_netlist, ERC.
   CONNECTIONS.md mech section updated.
5. Board surgery on the post-222 canonical copy (exp275):
   relocate R8/C44/C2 + re-lay webs; swap SH1 footprint and move
   to the solved centre; add CL1-6; refill; KiCad DRC +
   check_pcb (acceptance: unconnected 0, courtyard 0, and D1
   ABSENT from SH1's fallback pair list).
6. Heights under the can: U1 SO-8 1.75 max, U2 SOT-23-5 ~1.1,
   0603/1206 passives <= 1.35 (C33 is outside), RJ2 0603 — all
   < 3.0 internal. Verify each under-can part's height from its
   datasheet when the under-can list is final.
