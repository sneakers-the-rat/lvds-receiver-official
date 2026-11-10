import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/work/bm')
import wx
_app = wx.App(False)
import gridroute as G
import bm_gate as BG

items = G.load_items('hw/pdlvds_rx.exp264.kicad_pcb')
for it in items:
    it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
def rk(p): return (round(p[0], 3), round(p[1], 3))
RIP_SEGS = {('ULPI_D0','F.Cu',(76.875,8.125),(77.125,8.375)), ('ULPI_D0','F.Cu',(77.125,8.375),(77.375,8.625)),
            ('ULPI_D0','F.Cu',(77.375,8.625),(77.625,8.875)), ('ULPI_D0','F.Cu',(77.625,8.875),(77.875,9.125)),
            ('ULPI_STP','B.Cu',(76.44,9.03),(76.42,9.5)), ('ULPI_STP','In2.Cu',(76.445,9.03),(77.2,5.9)),
            ('ULPI_CK','In2.Cu',(76.62,17.3),(76.62,13.5))}
pool = []
for it in items:
    if it.kind == 'via' and it.net == 'ULPI_STP' and abs(it.a[0]-76.445) < 0.01 and abs(it.a[1]-9.03) < 0.01:
        continue
    if it.kind == 'trk' and (it.net, it.layer, rk(it.a), rk(it.b)) in RIP_SEGS or \
       it.kind == 'trk' and (it.net, it.layer, rk(it.b), rk(it.a)) in RIP_SEGS:
        continue
    if it.kind == 'pad':
        cx = (it.rect[0]+it.rect[2])/2; cy = (it.rect[1]+it.rect[3])/2
        if it.layer != 'F.Cu' and 74.3 < cx < 79.2 and 11.4 < cy < 16.6:
            continue
    pool.append(it)

def scan(net, x0, x1, y0, y1, label):
    ok = []
    x = x0
    while x <= x1 + 1e-9:
        y = y0
        while y <= y1 + 1e-9:
            ms = BG.margin_via((round(x,2), round(y,2)), net, pool, r=0.25)
            if ms and ms[0][0] >= 0:
                ok.append((round(ms[0][0],3), round(x,2), round(y,2)))
            y += 0.05
        x += 0.05
    ok.sort(reverse=True)
    print(label, 'legal sites:', len(ok), 'best:', ok[:8])

scan('ULPI_STP', 76.2, 77.1, 8.6, 10.0, 'STP via')
scan('GND', 78.2, 79.8, 16.6, 19.8, 'GND stitch NE')
scan('GND', 75.4, 78.1, 12.7, 15.3, 'GND stitch EP')
