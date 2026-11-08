"""t_al14: GND stitch via (82.0,-18.075) d0.5 into the fill pocket
severed by pass 196's DAC west run (pocket outline x[78.08,86.95]
y[-18.5,-15.83], 0 vias; scan t_al13: F +0.225 In2 +2.408 B +2.515).
Usage: t_al14_build227.py in out"""
import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import load_items, pt_margin, in_box_pool, fmt_it
SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = load_items(board)
pool = in_box_pool(items, (78.0, 87.0, -19.0, -15.0), pad=1.2)
ok = True
for li in range(3):
    m, w = pt_margin(li, 82.0, -18.075, 'GND', 0.25, pool[li])
    print(f'  gate via (82.0,-18.075) L{li}: {m:+.3f} worst {fmt_it(w)}')
    ok &= m >= 0
if not ok:
    print('GATES FAIL'); sys.exit(1)
code = None
for t in board.GetTracks():
    if t.GetNetname() == 'GND':
        code = t.GetNetCode(); break
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(82.0), pcbnew.FromMM(-18.075)))
v.SetWidth(pcbnew.FromMM(0.5)); v.SetDrill(pcbnew.FromMM(0.3))
v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNetCode(code)
board.Add(v)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print('saved', OUT)
