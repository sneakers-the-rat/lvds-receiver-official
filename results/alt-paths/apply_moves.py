#!/usr/bin/env python3
"""Path A placement relief, round 2 — apply MOVES to a copy of the
pass-10 placement board (tracks/vias already stripped) and save the
candidate. Placement only: no copper is touched, rotations unchanged,
board outline / connectors / analog cluster (D1, U1, R1, C1) unmoved.

Every move is listed with its reason in MOVES below and in
../SUMMARY.md. One board per process (KiCad 7 SWIG).
Usage: apply_moves.py <in.kicad_pcb> <out.kicad_pcb>
"""
import sys
import pcbnew

# ref: (new_x_mm, new_y_mm, rationale)
MOVES = {
    # --- unseal boxed pads (sealer was a foreign neighbour) ---
    "C28": (58.5, 51.0,  "C28.2 GND pad physically overlapped U5.6 CDR_CLKP "
                         "(probe dist 0.000) sealing it; also U5xC28 courtyard "
                         "3.18 mm^2. Moved W to open space S of R13, still "
                         "adjacent to U5's +3V3D west column it decouples."),
    "C17": (62.5, 44.5,  "C17.2 GND sat 0.080 mm N of U5.16 +3V3D and C17.1 "
                         "0.08 mm from its W escape, sealing U5.16; also "
                         "U5xC17 courtyard 2.75 and C16xC17 0.44 mm^2. Moved "
                         "NW into the open area S of U6's south row."),
    "C14": (53.5, 57.0,  "C14.2 GND at 0.226 mm was the closest foreign item "
                         "to boxed U14.1 +5V; also U14xC14 courtyard "
                         "0.68 mm^2. Moved NW, closer to X2.3 REFCLK and "
                         "U4.11 REFCLKN, the net it decouples."),
    "R12": (44.0, 60.0,  "R12.2 GND pad overlapped U13.10 +VA (probe dist "
                         "0.025) sealing it, and R12.1 THRADJ was itself "
                         "boxed against U13's exposed pad (0.260 mm); also "
                         "R12xU13 courtyard 2.84 mm^2. Moved W into open "
                         "space S of C51; THRADJ still routes to U4.9."),
    "R40": (43.5, 62.0,  "R40.1 SET_P was boxed with C41.2 GND overlapping "
                         "its W edge (probe dist 0.225) and C51.1 in line N; "
                         "also C41xR40 courtyard 0.99 and R40xC51 0.62 mm^2. "
                         "Moved S toward C42.1, the other SET_P endpoint's "
                         "neighbourhood, into verified open space."),
    "C51": (43.5, 54.5,  "C41xC51 courtyard 0.41 mm^2 and C51xC13 0.22 mm^2; "
                         "moved N, nearer FB1/U4 which its +3V3D_CDR net "
                         "decouples; also clears R40's old north line."),
    # --- courtyard collisions, cheap wins in open space ---
    "C4":  (10.0, 31.5,  "C4's courtyard lay entirely inside C33's "
                         "(C4xC33 4.32 mm^2, MH5xC4 0.07). Both are APD_K "
                         "caps; moved S, staying in the APD bias area."),
    "C33": (13.5, 28.0,  "MH5xC33 courtyard 1.89 mm^2 (mounting hole MH5 is "
                         "fixed); moved E, still adjacent to the APD_K "
                         "network it bulk-decouples."),
    "C38": (25.0, 68.0,  "F1xC38 courtyard 3.16 mm^2; moved E into open "
                         "space between F1 and D3."),
    "D4":  (13.0, 72.0,  "F1xD4 courtyard 0.77 mm^2; moved 1 mm W, clear of "
                         "F1's courtyard, same +5V/GND neighbourhood."),
    "C5":  (22.5, 43.0,  "C1xC5 courtyard 0.27 mm^2; C1 is TIA-node analog "
                         "and stays; C5 moved 1 mm E, which also shortens "
                         "its POST_INP leg toward U2."),
    "C20": (17.5, 55.5,  "C20xL2 courtyard 0.14 mm^2; moved NW 1 mm; XI load "
                         "cap, still next to X1/U12 area."),
    "C21": (25.5, 55.0,  "X1xC21 courtyard 0.83 and C21xC6 0.13 mm^2; moved "
                         "SW into the gap between C6 and X1."),
    "C22": (38.5, 63.0,  "C40xC22 courtyard 0.48 mm^2; moved 1 mm E; "
                         "PHY_1V8 decoupling for U7, still adjacent."),
    "R24": (23.5, 15.0,  "R24xC30 0.21 and R24xR28 0.65 mm^2 courtyard "
                         "overlaps; moved SE into open space; HV_RT timing "
                         "resistor, position is not electrically sensitive."),
    "R17": (37.0, 55.5,  "R17xFB2 courtyard 1.58 mm^2; moved 1.5 mm N; "
                         "RBIAS still routes to U7.32."),
    "R27": (20.75, 11.5, "R27xU10 courtyard 0.15 mm^2 (0.1 mm strip); moved "
                         "SE, also taking R27.1 HV_GATE off U10.9's E graze."),
    "C37": (7.5, 60.0,   "R36xC37 courtyard 0.04 mm^2; moved 1 mm W toward "
                         "the board edge, clear of R36 and MH6."),
    "R42": (54.5, 60.0,  "R41xR42 courtyard 0.67 mm^2; moved S 1.5 mm into "
                         "the gap S of R41, clear of U14's courtyard."),
    "R5":  (15.5, 50.5,  "U12xR5 courtyard 0.15 mm^2 (0.11 mm strip); moved "
                         "1 mm W; +VA/VMID divider, not position-sensitive."),
    "R11": (42.0, 40.0,  "R11xJ3 courtyard 3.14 mm^2; J3 is the TEST_IN "
                         "connector and stays; R11 moved 2.5 mm W, still in "
                         "line between J3.1 and U3's CMP_IN."),
    "C49": (89.5, 28.0,  "U6xC49 courtyard 0.19 mm^2: the x=89 column sits "
                         "0.13 mm inside U6's courtyard E edge. Whole column "
                         "shifted 0.5 mm E (see R15/C19/R16)."),
    "C19": (89.5, 41.0,  "U6xC19 courtyard 0.19 mm^2; x=89 column shift E."),
    "R15": (89.5, 38.0,  "U6xR15 courtyard 0.19 mm^2; x=89 column shift E."),
    "R16": (89.5, 44.0,  "U6xR16 courtyard bbox-only overlap; x=89 column "
                         "shift E."),
}


def main():
    src, dst = sys.argv[1], sys.argv[2]
    b = pcbnew.LoadBoard(src)
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    missing = [r for r in MOVES if r not in fps]
    if missing:
        print("MISSING REFS:", missing)
        sys.exit(1)
    for ref, (x, y, _why) in MOVES.items():
        fp = fps[ref]
        old = fp.GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(int(x * 1e6), int(y * 1e6)))
        print("MOVE %s (%.2f,%.2f) -> (%.2f,%.2f)"
              % (ref, old.x / 1e6, old.y / 1e6, x, y))
    assert len(b.GetFootprints()) == 144
    b.Save(dst)
    print("saved", dst, "footprints:", len(b.GetFootprints()))


if __name__ == "__main__":
    main()
