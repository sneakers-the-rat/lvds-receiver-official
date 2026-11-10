# DISTRICT STATUS — bk (USB_RST, full-set build)

Date: 2026-11-10. Frontier: exp257 (pass 219). Candidate built: **hw/pdlvds_rx.exp258.kicad_pcb** (NOT banked — does not meet the pass-220 bar).

## Verdict

**U7 re-place (or an equivalent geometry change) is required.** This is the
built candidate's referee output, not pricing alone: with every item in the
widened movable set moved simultaneously, the board connects USB_RST
(nets 0) but only by shorting it to +3V3A at the one via that cannot move.

## Candidate referee output (exp258, this build)

- KiCad DRC: **41 violations, 0 unconnected items**
  - 4 copper_edge_clearance — the standing J1 items, unchanged
  - **1 shorting_items: nets +3V3A and USB_RST** (journey track vs the
    +3V3A via (73.625,10.625) d0.8)
  - 34 clearance — worst actual 0.020 mm; pairs: ULPI_DIR/ULPI_STP ×10,
    ULPI_DIR/ULPI_NXT ×4, +3V3A/USB_RST ×3, RBIAS/XO ×3, DM_PHY/ULPI_DIR ×3,
    PHY_1V8A/RBIAS ×2, CDR_SQUELCH/ULPI_DIR ×2, BIST_DRV/SPI_MOSI ×2,
    BIST_DRV/USB_RST ×2, ULPI_CK/USB_RST ×2, ULPI_D0/USB_RST ×1,
    ULPI_NXT/USB_RST ×1
  - 1 via_diameter + 1 drill_out_of_range — bh's arrival surface via
    (74.82,5.84) is d0.40/drill 0.20, below the board setup minimums
    (via 0.50, drill 0.30); at d0.50 it does not fit (bh's fences stand)
- check_pcb: **unconnected nets 0**, census 165 (exp257: 120), courtyard 0,
  blind list 21 (SH1) unchanged
- Save net-rename census diff: only the five expected net deltas
  (BIST_DRV +1, ULPI_CK +2, ULPI_DIR +4, USB_RST +14 trk/+2 via, rest 0);
  all 14 USB_RST segments verified present post-save (bk_verify.py)

## What the candidate moves (all at once)

- DM_PHY F loop re-laid west (v3, one extra west nudge vs GND via
  (73.434,17.685)): prices +0.012 — clean.
- USB_RST dive via (74.45,18.25) + F stub from U7.9 (bi's dive, with DM
  re-laid): clean except −0.031 vs the NXT rejoin (fanout packing).
- CK jog re-laid shallower: west point (74.38,10.28) instead of (74.32,10.2)
  (the jog exists to dodge the PHY_1V8A notch via's In2 disc).
- RBIAS column shifted −0.30 (load-bearing: RBIAS has an x74.0 section at
  y≈15.25; unshifted, the journey's north leg has no channel at all).
- bh arrival: CK via → (75.48,5.92) d0.5, RST surface via (74.82,5.84),
  BIST/MOSI/SCL nudges per bh/bj. Arrival knives stand at −0.002..−0.046
  (CK-F vs HV_SHDN pad) except the sub-minimum surface via above.

## The three locks (each priced in bk_price/bk_facts*, all in bk_lib v6)

1. **The +3V3A via (73.625,10.625) d0.8 cannot move and cannot be fed
   otherwise.** Every re-place is sealed: north pocket = XO F journey
   (y8.55–9.1 and y9.6 bands) + GND pad (73.075,9.025)–(73.975,9.975);
   west along its own web = XO F journey + GND pad (71.325,10.525)–
   (72.225,11.475); south = XO/RBIAS In2 columns + the journey itself;
   east/south-east F feed = XO band at y9.6 + PHY notch via disc + PV via
   (75.82,10.30); In2 feed is not possible (U7 pads are F-only; every other
   U7 net dives by via for this reason). Shrinking it in place to d0.5/d0.4
   still seals the thread (jog capsule flank at y10.625 is x74.049; a d0.4
   via demands journey centre ≥74.175). Deleting it strand-feeds U7.25.
   In the built candidate the journey passes its disc at centre distance
   0.467 vs 0.75 required — DRC reports the short.
2. **The RBIAS via has no legal re-place either** (its shift is mandatory
   for the north leg). West pocket = the +3V3A via disc itself (bj's
   composite overlapped them at −0.693; bk at (73.52,10.88) −0.624);
   south = XO column (73.125) and the thread; the candidate uses
   (73.52,11.55), which clears everything except XO column/diag endpoint
   (−0.180/−0.055, no overlap).
3. **DIR/NXT fanout is a genuine 3-body packing failure** with the dive
   via present (bi/bj concur): best joint found = DIR via (75.0,19.2)
   (binds: CDR_SQUELCH −0.009, NXT continuation −0.048) + NXT via
   (74.90,17.40) with east-mid rejoin, mutual pair −0.167 (rejoin seg vs
   DIR via, actual 0.408 vs 0.575). DIR's F stub also grazes ULPI_STP's
   escape column (10 DRC pairs, worst actual 0.020 mm).

## What would unblock it

Moving U7 (the brief's last resort) — or any change of the same magnitude:
relocating the +3V3A feed via out of the pocket (e.g. U7 rotated/shifted so
the via lands south of the jog band), or re-placing U6. Short of that, the
pocket y9.4–11.6 between the CK column and the RBIAS/XO columns has no
legal In2 path for USB_RST at referee clearances.

## Files

- scratch/work/bk/bk_lib.py (composite definition, v6), bk_price.py /
  bk_price_out.txt (joint pricing), bk_facts*.py (district facts),
  bk_fanout.py / bk_nxt.py (fanout searches), bk_build.py (build),
  bk_verify.py (post-save segment verification), drc_exp258.json /
  drc_exp258.log, check_exp258.txt (referee outputs)
- hw/pdlvds_rx.exp258.kicad_pcb — the candidate (unbanked)
- hw/pdlvds_rx.exp258.debris-be.kicad_pcb — the pre-existing unbanked
  exp258 found in the tree, preserved under a new name before building

Pass 220 is NOT banked: the bank bar (nets 0 / DRC 4 J1 only) is not met.
Frontier remains exp257 (pass 219).
