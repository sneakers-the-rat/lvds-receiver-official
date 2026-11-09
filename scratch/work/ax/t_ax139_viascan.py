import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
poly = None
for zz in b.Zones():
    if zz.GetNetname() == 'GND' and zz.GetLayer() == pcbnew.F_Cu:
        polys = zz.GetFilledPolysList(pcbnew.F_Cu)
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            bx = o.BBox()
            if abs(bx.GetLeft() / 1e6 - 72.68) < 0.3 \
                    and abs(bx.GetTop() / 1e6 - 8.93) < 0.3:
                poly = [(o.CPoint(j).x / 1e6, o.CPoint(j).y / 1e6)
                        for j in range(o.PointCount())]
print('P18 polygon points:', len(poly), flush=True)
def inside(x, y):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and \
                (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            c = not c
        j = i
    return c
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
def scan(label):
    best = []
    y = 8.95
    while y <= 10.72:
        x = 72.7
        while x <= 75.84:
            if inside(x, y):
                w = 9.9
                for l in range(3):
                    it = ('via', 'GND', (x, y, 0.25), 0.2)
                    for o in pool[l]:
                        if o[1] == 'GND':
                            continue
                        m = item_margin(l, it, [o])
                        if m < w:
                            w = m
                best.append((round(w, 3), round(x, 2), round(y, 2)))
            x += 0.05
        y += 0.05
    best.sort(reverse=True)
    print(label, 'top:', best[:6], flush=True)
scan('original pool')
bv = [it for it in pool[2] if it[1] == '+3V3A' and it[0] == 'seg'
      and abs(it[2][0] - 73.625) < 0.01 and abs(it[2][2] - 73.625) < 0.01]
rip_items(bv)
add_items({2: [('seg', '+3V3A', (73.625, 8.625, 73.625, 10.625, 0.10),
                0.25)], 0: [], 1: []})
scan('thinned pool')
