#!/usr/bin/env python3
"""t_ah8_refill.py -- refill all zones and save (pre-referee step)."""
import sys
import wx
_app = wx.App(False)
import pcbnew

src, out = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(out)
print('refilled + saved', out)
