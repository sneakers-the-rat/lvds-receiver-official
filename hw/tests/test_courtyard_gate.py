#!/usr/bin/env python3
"""Regression test: the courtyard hard gate in check_pcb.py.

Failure history (owner ruling 2026-11-05): the board reached pass
124 with 26 same-side courtyard collision pairs — real
body-on-body overlaps (U6xC49, U6xR15, U6xR16 at 4.32 mm^2 each)
— because no audit counted them. The owner ruled a layout with
overlapping parts INVALID, full stop, no exceptions: check_pcb's
verdict now FAILS on any courtyard pair, and footprints without
a drawn courtyard (SH1, D2, D1, C4, U9, T1) are measured with a
bbox fallback so the gate can see them.

This test pins courtyard_pairs() against the frozen pass-124
board (hw/pdlvds_rx.exp117.kicad_pcb, which never changes): the
26 polygon pairs must be exactly the recorded census, the blind
list exactly the six custom footprints, and every fallback pair
must involve a blind ref. If a future change to the gate makes
any of these move, the test fails.

Run: xvfb-run -a python3 hw/tests/test_courtyard_gate.py
"""
import os
import sys

HW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, HW)
import wx
_app = wx.App(False)
import pcbnew
import check_pcb

BOARD = os.path.join(HW, "pdlvds_rx.exp117.kicad_pcb")

EXPECTED_POLY = {
    frozenset(p) for p in [
        ("C1", "C5"), ("C16", "C17"), ("C41", "FB2"),
        ("C41", "R40"), ("D8", "U1"), ("F1", "C38"),
        ("F1", "D4"), ("J5", "R25"), ("MH2", "C19"),
        ("MH5", "C33"), ("R11", "J3"), ("R32", "R31"),
        ("R36", "C37"), ("R41", "R42"), ("R49", "R50"),
        ("U1", "R1"), ("U12", "R5"), ("U6", "C18"),
        ("U6", "C19"), ("U6", "C49"), ("U6", "MH2"),
        ("U6", "R15"), ("U6", "R16"), ("U6", "U5"),
        ("X1", "D6"), ("X1", "D7"),
    ]
}
EXPECTED_BLIND = ["C4", "D1", "D2", "SH1", "T1", "U9"]


def main():
    board = pcbnew.LoadBoard(BOARD)
    pairs, blind = check_pcb.courtyard_pairs(board)
    assert blind == EXPECTED_BLIND, f"blind list moved: {blind}"
    poly = {frozenset((a, b)) for a, b, _s, _area, fb in pairs
            if not fb}
    assert poly == EXPECTED_POLY, (
        f"polygon pair census moved:\n  missing: "
        f"{sorted(map(sorted, EXPECTED_POLY - poly))}\n  extra: "
        f"{sorted(map(sorted, poly - EXPECTED_POLY))}")
    for a, b, _s, _area, fb in pairs:
        if fb:
            assert a in EXPECTED_BLIND or b in EXPECTED_BLIND, \
                f"fallback pair without a blind ref: {a} x {b}"
    areas = {frozenset((a, b)): area for a, b, _s, area, _fb in pairs}
    assert abs(areas[frozenset(("U6", "C49"))] - 4.3216) < 0.01, \
        "U6xC49 area moved"
    print(f"PASS: {len(poly)} polygon pairs pinned, blind="
          f"{blind}, fallback pairs="
          f"{[(a, b) for a, b, _s, _ar, fb in pairs if fb]}")


if __name__ == "__main__":
    main()
