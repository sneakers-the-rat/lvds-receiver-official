import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import gridroute as G
items = G.load_items('hw/pdlvds_rx.exp264.kicad_pcb')
def show(net, box, kinds=('trk','via')):
    for it in items:
        if it.net != net or it.kind not in kinds:
            continue
        p = it.a
        if box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]:
            if it.kind == 'trk':
                print(net, 'TRK', it.layer, tuple(round(v,3) for v in it.a), '->', tuple(round(v,3) for v in it.b), 'w', round(it.hw*2,2))
            else:
                print(net, 'VIA', tuple(round(v,3) for v in it.a), 'd', round(it.hw*2,2))
show('ULPI_D0', (76.2, 7.4, 78.8, 10.8))
show('GND', (75.6, 7.2, 78.6, 10.6))
show('ULPI_STP', (75.8, 8.2, 77.2, 13.2))
show('I2C_SCL', (75.6, 7.2, 77.4, 9.6))
