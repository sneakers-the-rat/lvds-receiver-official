#!/usr/bin/env python3
"""All tracks/vias of NET on BOARD with endpoints, sorted."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

BOARD, NET = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(BOARD)
LN = {0: 'F', 1: 'In1', 2: 'In2', 31: 'B'}
rows = []
for t in board.GetTracks():
    if t.GetNetname() != NET:
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition())
        rows.append(f"VIA ({p[0]:.2f},{p[1]:.2f}) d={pcbnew.ToMM(t.GetWidth()):.2f}")
    else:
        a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
        rows.append(f"{LN.get(t.GetLayer(), t.GetLayer())} "
                    f"({a[0]:.2f},{a[1]:.2f})->({b[0]:.2f},{b[1]:.2f}) "
                    f"w={pcbnew.ToMM(t.GetWidth()):.2f}")
for r in sorted(rows):
    print(r)
