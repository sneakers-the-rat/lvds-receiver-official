"""t_ax65: GND stitch scan v3 - FULL exp242 pool (no local filter),
grid 0.05 over (66.9,72.3,-11.3,1.3); keep via points with worst
margin >= +0.02 that lie INSIDE exp244's GND F fill (point-in-polygon
on the real filled outlines)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp242.kicad_pcb')
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp244.kicad_pcb')
polys = []
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu):
        continue
    ps = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(ps.OutlineCount()):
        ol = ps.Outline(i)
        polys.append([(ol.GetPoint(j).x / 1e6, ol.GetPoint(j).y / 1e6)
                      for j in range(ol.PointCount())])


def inside(x, y):
    cnt = 0
    for pts in polys:
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if xi > x:
                    cnt += 1
    return cnt % 2 == 1


ok = []
y = -11.3
while y <= 1.3:
    x = 66.9
    while x <= 72.3:
        if inside(round(x, 3), round(y, 3)):
            via = ('via', 'GND', (round(x, 3), round(y, 3), 0.25), 0.2)
            m = min(min(item_margin(l, via, [o]) for o in pool[l]
                        if o[1] != 'GND') for l in range(3))
            if m >= 0.02:
                ok.append((round(m, 3), round(x, 3), round(y, 3)))
        x += 0.05
    y += 0.05
ok.sort(reverse=True)
print(f'{len(ok)} legal in-fill stitch points', flush=True)
for r in ok[:25]:
    print('  ', r, flush=True)
