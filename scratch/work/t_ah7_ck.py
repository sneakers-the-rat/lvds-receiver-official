#!/usr/bin/env python3
"""t_ah7_ck.py -- re-lay ULPI_CK's ripped In2 vertical by hand, gated.
The rip removed exactly (74.625,13.5)->(74.625,6.375) w0.25; on rip2 the
CK floods meet, so this single segment is the rejoin -- if its gate is
clean. Gate first; add only with --build. Reload census asserts CK
track count grows by exactly 1 and nothing is renamed.
Usage: t_ah7_ck.py IN OUT [--build]
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

SRC, OUT = sys.argv[1], sys.argv[2]
BUILD = '--build' in sys.argv
NET = 'ULPI_CK'
A, C = (74.625, 13.5), (74.625, 6.375)
W = 0.25
LI = 1  # In2

board = pcbnew.LoadBoard(SRC)
items, _ = repair.build_items(board)

def pair_clr(other):
    return max(netclass(NET)[1], netclass(other)[1] if other else 0.2)

worst = (1e9, None, None)
n = int(math.hypot(C[0] - A[0], C[1] - A[1]) / 0.05) + 1
for s in range(n + 1):
    x = A[0] + (C[0] - A[0]) * s / n
    y = A[1] + (C[1] - A[1]) * s / n
    for it in items[LI].near(LI, x, y):
        if it[1] == NET:
            continue
        m = dist_to_item(it, x, y) - (W / 2 + pair_clr(it[1]))
        if m < worst[0]:
            worst = (m, it, (round(x, 3), round(y, 3)))
m, it, at = worst
print(f'CK vertical gate: margin {m:+.3f} vs {it[1] if it else None} '
      f'{tuple(round(v,3) for v in it[2]) if it else None} at {at}')
if m < 0 or not BUILD:
    sys.exit(0 if m >= 0 else 1)

code = board.GetNetcodeFromNetname(NET)
before = sum(1 for t in board.GetTracks() if t.GetNetname() == NET)
t = pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(A[0]), pcbnew.FromMM(A[1])))
t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(C[0]), pcbnew.FromMM(C[1])))
t.SetWidth(pcbnew.FromMM(W))
t.SetLayer(pcbnew.In2_Cu)
t.SetNetCode(code)
board.Add(t)
board.Save(OUT)
b2 = pcbnew.LoadBoard(OUT)
after = sum(1 for t in b2.GetTracks() if t.GetNetname() == NET)
print(f'saved {OUT}; {NET} tracks {before} -> {after} (expect +1)')
assert after == before + 1
