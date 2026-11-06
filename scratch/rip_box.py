#!/usr/bin/env python3
"""Rip tracks of one net intersecting a box (rip-and-relay prep).

Usage: python3 scratch/rip_box.py IN OUT NET X0 Y0 X1 Y1   (mm)
Removes PCB_TRACE_T items of NET whose segment bounding box
intersects the box. Vias are kept (layer bridges are separate
items). Prints the removal count.
"""
import sys
import pcbnew

MM = 1_000_000
src, dst, net = sys.argv[1], sys.argv[2], sys.argv[3]
x0, y0, x1, y1 = (float(v) * MM for v in sys.argv[4:8])
board = pcbnew.LoadBoard(src)
kill = []
for t in board.GetTracks():
    if t.Type() != pcbnew.PCB_TRACE_T or t.GetNetname() != net:
        continue
    a, e = t.GetStart(), t.GetEnd()
    if min(a.x, e.x) <= x1 and max(a.x, e.x) >= x0 and \
       min(a.y, e.y) <= y1 and max(a.y, e.y) >= y0:
        kill.append(t)
for t in kill:
    board.Remove(t)
print(f'ripped {len(kill)} {net} segments in box')
board.Save(dst)
print(f'saved {dst}')
