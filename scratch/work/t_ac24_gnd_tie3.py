"""t_ac24: GND F track tie v3 for the U6.31 fill scrap, designed
against the full track dump AFTER t_ac23 removed I2C_SDA's via
from (69.875,0.625):

(71.0,0.28) on U6.31's pad -> (69.15,0.22): west along the pad
row (edge 0.265+ to the +3V3D pad, 0.22 to +3V3A's).
(69.15,0.22) -> (68.4,1.05): NW, rounding ULPI_NXT's mouth via
(68,0.625) at perp 0.581 (via exclusion for a track is 0.55;
NXT's F diagonal capsule >=0.59 away at the via point).
(68.4,1.05) -> (67.6,1.05): west into island 17's northern fill
lobe (SCL's F staircase stays >=0.375 away).

Usage: xvfb-run -a python3 scratch/work/t_ac24_gnd_tie3.py IN OUT
(Refill afterwards in a fresh process with t_ac19.)
"""
import sys
import wx
_app = wx.App(False)
import pcbnew

src, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
gnd = board.GetNetcodeFromNetname('GND')
pts = [(71.0, 0.28), (69.15, 0.22), (68.4, 1.05), (67.6, 1.05)]
for a, b in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(board)
    t.SetNetCode(gnd)
    t.SetLayer(pcbnew.F_Cu)
    t.SetWidth(pcbnew.FromMM(0.2))
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
    board.Add(t)
    print('added GND F', a, '->', b)
board.Save(out)
print('saved', out)
