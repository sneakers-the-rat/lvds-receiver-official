#!/usr/bin/env python3
"""Regression test: rule areas are copper-pour keepouts ONLY.

Failure history (found 2026-11-05, pass 133): every rule area on the
board was created by hw/notch.py, hw/notch_strip.py, hw/fix_hvraw.py
or hw/fix_r47.py, each setting only SetIsRuleArea(True) +
SetDoNotAllowCopperPour(True) -- documented intent "copper-pour
keepout only, tracks/vias/pads unaffected". A fresh ZONE in the
KiCad 7-era pcbnew defaulted DoNotAllowTracks/Vias/Pads to True, the
tools never cleared them, and the stored board banned tracks in all
28 rule areas. KiCad 8 DRC reported 199 items_not_allowed (162 of
them APD_K/APD_A tracks crossing the front-end pour notch) against
routing the project's own tools had laid in good faith.

This test reads the newest exp board's stored zone data and asserts
the invariant directly: every keepout block allows tracks, vias and
pads, and disallows copper pour. It fails on exp157 (the last board
before the fix) and passes on exp158 (flags corrected by
scratch/fix_keepout_flags.py).

Run: python3 hw/tests/test_keepout_flags.py
"""
import glob
import os
import re
import sys

HW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def newest_board():
    boards = glob.glob(os.path.join(HW, 'pdlvds_rx.exp*.kicad_pcb'))
    def num(p):
        m = re.search(r'exp(\d+)\.', p)
        return int(m.group(1)) if m else -1
    return max(boards, key=num)


def main():
    path = newest_board()
    text = open(path).read()
    blocks = re.findall(
        r'\(keepout\s+\(tracks\s+(\w+)\)\s+\(vias\s+(\w+)\)\s+'
        r'\(pads\s+(\w+)\)\s+\(copperpour\s+(\w+)\)', text)
    assert blocks, f'no keepout blocks found in {path}'
    bad = [b for b in blocks
           if b != ('allowed', 'allowed', 'allowed', 'not_allowed')]
    assert not bad, (
        f'{len(bad)} of {len(blocks)} rule areas in '
        f'{os.path.basename(path)} ban tracks/vias/pads; rule areas '
        f'on this board are pour-only keepouts by design '
        f'(hw/notch.py). Offenders (tracks, vias, pads, copperpour): '
        f'{bad[:3]}')
    print(f'PASS: {len(blocks)} rule areas in '
          f'{os.path.basename(path)} are pour-only keepouts '
          f'(tracks/vias/pads allowed, copper pour not allowed)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
