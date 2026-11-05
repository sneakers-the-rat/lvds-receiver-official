#!/usr/bin/env python3
"""Refill all zone pours on a board (save/reload cycle first —
ZONE_FILLER needs it on this KiCad build, per hw/import_ses.py).

Needed after hand-placed vias land inside a pour's stale fill: the
audit counts the via against the fill until the pour re-carves its
antipad. Pass 80's HV_SHDN landing via @(9.5,-18.9) is the case in
point (2 audit lines, HV_SHDN vs GND zone L1/L31).

Usage: python3 hw/refill.py <src> <out>
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT} (zones refilled)')
