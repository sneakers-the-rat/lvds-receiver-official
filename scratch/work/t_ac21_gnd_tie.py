"""t_ac21: GND F track tie for the U6.31 fill scrap severed by
ULPI_NXT's mouth diagonal. Path (hand-checked against the full
track dump + neck scans): starts on U6.31's pad, west at y0.28
(0.28/0.22 edge clearances to the +3V3D/+3V3A pads), then NW
around ULPI_NXT's mouth via (68,0.625) (perp 0.59 to NXT's seg,
0.69+ to the via), west into the mainland fill at y1.25
(fill reaches x67.80 there).

Usage: xvfb-run -a python3 scratch/work/t_ac21_gnd_tie.py IN OUT
(Refill in a fresh process with t_ac19 afterwards.)
"""
import sys
import wx
_app = wx.App(False)
import pcbnew

src, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
gnd = board.GetNetcodeFromNetname('GND')
pts = [(71.0, 0.28), (69.6, 0.28), (68.9, 0.95), (68.3, 1.25),
       (67.4, 1.25)]
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
