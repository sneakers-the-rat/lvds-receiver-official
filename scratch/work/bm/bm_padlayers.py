import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'hw')
import gridroute as G
items = G.load_items('hw/pdlvds_rx.exp262.kicad_pcb')
from collections import Counter
print('pad layers:', Counter(it.layer for it in items if it.kind == 'pad'))
print('trk layers:', Counter(it.layer for it in items if it.kind == 'trk'))
for it in items:
    if it.kind == 'pad' and it.net in ('GND', 'RBIAS', 'PHY_1V8', '+3V3A', 'PHY_1V8A'):
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if 74 < cx < 80 and 9 < cy < 18:
            print(it.net, 'layer=', it.layer, 'rect=', tuple(round(v, 3) for v in it.rect))
