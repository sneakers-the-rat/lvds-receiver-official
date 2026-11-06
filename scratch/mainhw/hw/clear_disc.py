#!/usr/bin/env python3
"""Remove up to N foreign items inside a disc, then SAVE and exit.

One short process per batch: KiCad 7.0.11's SWIG proxies corrupt
after a few dozen board.Remove() calls in one process, so clearing
a whole thicket is done as several invocations of this script
(state persists in the board file). It prints how many disc items
remain; invoke until 0. No zone refill here (fresh-process work).

Run: xvfb-run -a python3 hw/clear_disc.py IN OUT CX CY R N \
    KEEP_NET[,KEEP_NET...]
"""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from ripup import seg_dist

def main():
    src, out = sys.argv[1], sys.argv[2]
    cx, cy, radius = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
    maxn = int(sys.argv[6])
    keep = set(sys.argv[7].split(',')) if len(sys.argv) > 7 else set()
    board = pcbnew.LoadBoard(src)
    inside = []
    for t in board.GetTracks():
        if t.GetNetname() in keep:
            continue
        if seg_dist(cx, cy, t) < radius:
            inside.append(t)
    todo = inside[:maxn]
    for t in todo:
        board.Remove(t)
    board.Save(out)
    print(f"clear_disc: removed {len(todo)}, remaining in disc: "
          f"{len(inside) - len(todo)}")

if __name__ == "__main__":
    main()
