import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import gridroute as G
items = G.load_items('hw/pdlvds_rx.exp267.kicad_pcb')
def show(net, box, layers=None):
    for it in items:
        if it.net != net or it.kind not in ('trk', 'via'):
            continue
        if layers and it.layer not in layers:
            continue
        p = it.a
        q = it.b if it.kind == 'trk' else it.a
        if box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3] or box[0] <= q[0] <= box[2] and box[1] <= q[1] <= box[3]:
            if it.kind == 'trk':
                print(net, 'TRK', it.layer, tuple(round(v,3) for v in it.a), '->', tuple(round(v,3) for v in it.b), 'w', round(it.hw*2,2))
            else:
                print(net, 'VIA', tuple(round(v,3) for v in it.a), 'd', round(it.hw*2,2))
show('XO', (74.4, 9.0, 76.4, 10.3), ('F',))
show('XI', (74.6, 9.4, 76.2, 13.2), ('B',))
show('PHY_1V8A', (73.0, 11.4, 75.6, 13.4), ('B',))
show('+3V3A', (73.8, 9.6, 75.8, 12.2), ('B', 'In2'))
