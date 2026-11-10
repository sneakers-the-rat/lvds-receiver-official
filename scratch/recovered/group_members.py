#!/usr/bin/env python3
"""Print every item of every group of NET on BOARD (audit model)."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair

BOARD, NET = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(BOARD)
groups = repair.compute_groups(board)[NET]
print(f"{NET}: {len(groups)} groups")
for gi, g in enumerate(groups):
    print(f"-- group {gi}: {len(g)} items")
    for it in sorted(g, key=lambda t: t.desc):
        print("   ", it.kind, it.desc, sorted(it.layers))
