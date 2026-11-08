"""t_al7: add the GND stitch via at (75.9,-10.45) d0.5/drill0.3 to
exp224 (inside the fill pocket opened by the +3V3D dive re-lay),
refill, save exp225. Gates first in the exact item model."""
import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import load_items, pt_margin, in_box_pool, fmt_it

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = load_items(board)
pool = in_box_pool(items, (72.0, 80.0, -16.0, 6.0), pad=1.2)
ok = True
for li in range(3):
    m, w = pt_margin(li, 75.9, -10.45, 'GND', 0.25, pool[li])
    print(f'  gate via (75.9,-10.45) L{li}: {m:+.3f} worst {fmt_it(w)}')
    ok &= m >= 0
if not ok:
    print('GATES FAIL'); sys.exit(1)
code = None
for t in board.GetTracks():
    if t.GetNetname() == 'GND':
        code = t.GetNetCode(); break
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(75.9), pcbnew.FromMM(-10.45)))
v.SetWidth(pcbnew.FromMM(0.5)); v.SetDrill(pcbnew.FromMM(0.3))
v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNetCode(code)
board.Add(v)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print('saved', OUT)
