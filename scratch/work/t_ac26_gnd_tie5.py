"""t_ac26: GND F track tie v5 for the U6.31 fill scrap, with the
diagonal distance computed by the correct cross product
(s = (P-A) x u, u = ULPI_NXT diagonal's unit vector; v3's sign
error put its west end 0.199 from the diagonal -- a short).

Path: (71.0,0.27) on U6.31's pad -> (69.6,0.25) [s = -0.442 to
NXT's diagonal; edge 0.27 to +3V3D's pad, 0.56 to SDA's moved
via] -> (68.9,0.85) [rounds NXT's mouth via: end dist 0.928,
|s| >= 0.442 throughout] -> (68.2,1.15) [perp 0.561 to NXT's
via] -> (67.85,1.22) [SCL edge 0.205] -> (67.5,0.95) [perp
0.563 to NXT's via; lands in island 17's northern fill lobe --
the v3 tie's DRC heal proved fill contact in this pocket].

Usage: xvfb-run -a python3 scratch/work/t_ac26_gnd_tie5.py IN OUT
(Refill afterwards in a fresh process with t_ac19.)
"""
import sys
import wx
_app = wx.App(False)
import pcbnew

src, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
gnd = board.GetNetcodeFromNetname('GND')
pts = [(71.0, 0.27), (69.6, 0.25), (68.9, 0.85), (68.2, 1.15),
       (67.85, 1.22), (67.5, 0.95)]
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
