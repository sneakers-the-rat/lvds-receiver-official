import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import gridroute as G
items = G.load_items('hw/pdlvds_rx.exp262.kicad_pcb')
for it in items:
    if it.net != '+3V3A':
        continue
    if it.kind == 'trk':
        a, b = it.a, it.b
        if 74.0 <= a[0] <= 79.5 and 8.0 <= a[1] <= 13.0:
            print('TRK', it.layer, tuple(round(v, 3) for v in a), '->', tuple(round(v, 3) for v in b), 'w', round(it.hw * 2, 2))
    elif it.kind == 'via':
        if 74.0 <= it.a[0] <= 79.5 and 8.0 <= it.a[1] <= 13.0:
            print('VIA', tuple(round(v, 3) for v in it.a), 'd', round(it.hw * 2, 2))
