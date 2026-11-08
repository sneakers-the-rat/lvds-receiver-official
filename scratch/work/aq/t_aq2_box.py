"""t_aq2: ALL-nets dump of box x[46,60], y[19,27] on exp234 + board bbox.
For the U11.14 +3V3D design: what lives south of the +5V trunk."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp234.kicad_pcb')
items = load_items(b)
bb = b.GetBoardEdgesBoundingBox()
print(f'board bbox: x[{pcbnew.ToMM(bb.GetX()):.2f},{pcbnew.ToMM(bb.GetRight()):.2f}] '
      f'y[{pcbnew.ToMM(bb.GetY()):.2f},{pcbnew.ToMM(bb.GetBottom()):.2f}]')


def centre(it):
    k, d = it[0], it[2]
    if k in ('pad', 'via'):
        return d[0], d[1]
    return (d[0] + d[2]) / 2, (d[1] + d[3]) / 2


for li in range(3):
    for it in items[li]:
        cx, cy = centre(it)
        if 46 <= cx <= 60 and 19 <= cy <= 27:
            print(f'L{li} {fmt_it(it)}')
print('--- drawings/edges in box ---')
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        c = d.GetBoundingBox()
        cx, cy = pcbnew.ToMM(c.GetCenter())
        if 44 <= cx <= 62 and 17 <= cy <= 29:
            print(f'EDGE {d.GetShape()} bbox x[{pcbnew.ToMM(c.GetX()):.2f},{pcbnew.ToMM(c.GetRight()):.2f}] y[{pcbnew.ToMM(c.GetY()):.2f},{pcbnew.ToMM(c.GetBottom()):.2f}]')
