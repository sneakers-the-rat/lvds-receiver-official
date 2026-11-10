import sys, math
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/work/bm')
import wx
_app = wx.App(False)
import pcbnew
import gridroute as G
import bm_gate as BG

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp266.kicad_pcb')
frag = None
for z in b.Zones():
    if z.GetNetname() != 'GND' or z.GetLayer() != pcbnew.F_Cu:
        continue
    polys = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(polys.OutlineCount()):
        o = polys.Outline(i)
        xs = [o.GetPoint(j).x/1e6 for j in range(o.PointCount())]
        ys = [o.GetPoint(j).y/1e6 for j in range(o.PointCount())]
        if 75.0 < min(xs) < 75.2 and 6.9 < min(ys) < 7.1:
            frag = list(zip(xs, ys))
print('frag points:', len(frag))
def inside(px, py):
    c = False
    for (ax, ay), (bx, by) in zip(frag, frag[1:] + frag[:1]):
        if (ay > py) != (by > py) and px < (bx-ax) * (py-ay) / (by-ay) + ax:
            c = not c
    return c
def dist_poly(px, py):
    d = 1e9
    for (ax, ay), (bx, by) in zip(frag, frag[1:] + frag[:1]):
        vx, vy = bx-ax, by-ay
        t = max(0.0, min(1.0, ((px-ax)*vx + (py-ay)*vy) / (vx*vx + vy*vy + 1e-12)))
        d = min(d, math.hypot(px-(ax+t*vx), py-(ay+t*vy)))
    return d

items = G.load_items('hw/pdlvds_rx.exp266.kicad_pcb')
for it in items:
    it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
pool = []
for it in items:
    if it.kind == 'pad':
        cx = (it.rect[0]+it.rect[2])/2; cy = (it.rect[1]+it.rect[3])/2
        if it.layer != 'F.Cu' and 74.3 < cx < 79.2 and 11.4 < cy < 16.6:
            continue
    pool.append(it)
ok = []
gx = 75.2
while gx <= 78.45:
    gy = 7.1
    while gy <= 9.55:
        x, y = round(gx, 2), round(gy, 2)
        if inside(x, y) or dist_poly(x, y) <= 0.2:
            ms = BG.margin_via((x, y), 'GND', pool, r=0.25)
            if ms and ms[0][0] >= 0:
                ok.append((round(ms[0][0], 3), x, y, inside(x, y)))
        gy += 0.05
    gx += 0.05
ok.sort(reverse=True)
print('legal touch sites:', len(ok), ok[:10])
