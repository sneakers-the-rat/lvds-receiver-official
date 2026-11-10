import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair6
import check_pcb
from hand_stub import build_items
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp82.kicad_pcb')
items = build_items(b)
cx, cy = 52.562, -17.25
for kind, net, layers, shape, desc in items:
    bb = shape.BBox()
    x0, y0 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop())
    x1, y1 = pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom())
    if x1 < cx-3 or x0 > cx+3 or y1 < cy-3 or y0 > cy+3:
        continue
    print(kind, net, sorted(layers), desc, 'bbox', round(x0,2), round(y0,2), round(x1,2), round(y1,2))
