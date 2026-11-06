#!/usr/bin/env python3
"""Fence-rip surgery: remove the few foreign items that fence a
sealed pad's one open direction (victims are connected nets whose
pads keep their own escapes; the healing repair reconnects them).

Cases (all measured with stub_debug.py on fr11/fr12):
  CDR_VREF U4.3  west is open except CDR_NIN's hugging tracks
  XO       U7.27 north is open except XI's tracks
  +3V3D    U11.14 north is open except one GND track
  HV_GATE  U10.7 east is open except one HV_INTVCC via
Removes happen here (few, one process); stubs are placed by
hand_stub.py on the output board.
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from ripup import seg_dist

CASES = [  # (fence net, x, y, radius)
    ('CDR_NIN',    49.0, 51.25, 1.3),
    ('CDR_CLKP',   55.3, 51.25, 1.2),
    ('XI',         32.75, 58.4, 1.3),
    ('GND',        14.25, 61.3, 1.4),
    ('HV_INTVCC',  19.0, 10.5, 1.2),
]

def main():
    src, out = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard(src)
    all_tracks = list(board.GetTracks())
    doomed = []
    for net, x, y, r in CASES:
        for t in all_tracks:
            if t.GetNetname() != net:
                continue
            if seg_dist(x, y, t) < r:
                doomed.append(t)
    removed = []
    for t in doomed:
        removed.append(t.GetNetname())
        board.Remove(t)
    from collections import Counter
    print('surgery removed:', dict(Counter(removed)), flush=True)
    board.Save(out)
    print('saved', out, flush=True)

if __name__ == "__main__":
    main()
