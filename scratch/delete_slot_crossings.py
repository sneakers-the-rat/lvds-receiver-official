#!/usr/bin/env python3
"""Delete segments of the named nets that enter the creepage slot
rectangle inflated by the 0.5 mm edge-clearance halo
(x 11.5..46.5, y 23.1..25.6). A segment 'enters' if any point of it
lies in the rectangle (endpoint inside, or clipped intersection).

Usage: python3 scratch/delete_slot_crossings.py IN OUT NET [NET...]
Prints per-net deletion counts. Referee afterwards: KiCad DRC +
a re-run of the crossing census (this test) expecting zero."""
import sys
import pcbnew

MM = 1_000_000
X0, Y0, X1, Y1 = 11.5, 23.1, 46.5, 25.6
src, dst, nets = sys.argv[1], sys.argv[2], set(sys.argv[3:])
board = pcbnew.LoadBoard(src)

def enters(ax, ay, ex, ey):
    if X0 <= ax <= X1 and Y0 <= ay <= Y1:
        return True
    if X0 <= ex <= X1 and Y0 <= ey <= Y1:
        return True
    # Liang-Barsky clip against the rect
    dx, dy = ex - ax, ey - ay
    u0, u1 = 0.0, 1.0
    for p_, q_ in ((-dx, ax - X0), (dx, X1 - ax),
                   (-dy, ay - Y0), (dy, Y1 - ay)):
        if p_ == 0:
            if q_ < 0:
                return False
            continue
        u = q_ / p_
        if p_ < 0:
            u0 = max(u0, u)
        else:
            u1 = min(u1, u)
        if u0 > u1:
            return False
    return True

from collections import Counter
killed = Counter()
kill = []
for t in board.GetTracks():
    if t.Type() != pcbnew.PCB_TRACE_T or t.GetNetname() not in nets:
        continue
    a, e = t.GetStart(), t.GetEnd()
    if enters(a.x / MM, a.y / MM, e.x / MM, e.y / MM):
        kill.append(t)
        killed[t.GetNetname()] += 1
for t in kill:
    board.Remove(t)
for n in sorted(killed):
    print(f'{n}: deleted {killed[n]} crossing segments')
board.Save(dst)
print(f'saved {dst}')
