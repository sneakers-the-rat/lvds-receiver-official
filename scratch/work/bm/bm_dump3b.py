import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import gridroute as G
items = G.load_items('hw/pdlvds_rx.exp267.kicad_pcb')
def show(net, box):
    for it in items:
        if it.net != net or it.kind not in ('trk', 'via'):
            continue
        p = it.a
        if box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]:
            if it.kind == 'trk':
                print(net, 'TRK', it.layer, tuple(round(v,3) for v in it.a), '->', tuple(round(v,3) for v in it.b), 'w', round(it.hw*2,2))
            elif it.kind == 'via':
                print(net, 'VIA', tuple(round(v,3) for v in it.a), 'd', round(it.hw*2,2))
for n in ('PHY_1V8A', '+3V3A'):
    show(n, (74.2, 9.8, 77.2, 12.3))
