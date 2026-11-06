import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew, repair
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp182.kicad_pcb')
mm = lambda v: v/1e6

# filled polygons per layer for GND zones
fills = {}
for z in b.Zones():
    if z.GetNetname() != 'GND': continue
    for l in (pcbnew.F_Cu, pcbnew.B_Cu):
        if not z.IsOnLayer(l): continue
        polys = z.GetFilledPolysList(l)
        lst = []
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            lst.append([(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())])
        fills.setdefault(l, []).extend(lst)

def in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % n]
        if (y1 > y) != (y2 > y):
            xin = (x2-x1) * (y-y1) / (y2-y1) + x1
            if x < xin: inside = not inside
    return inside

def in_fill(x, y, l):
    return any(in_poly(x, y, p) for p in fills.get(l, []))

groups = repair.compute_groups(b)
gnd = groups.get('GND', [])
print(f'GND copper groups: {len(gnd)}')
stranded = []
for gi, g in enumerate(gnd):
    pads = [it for it in g if it.kind == 'pad']
    pts = []
    for it in g:
        bb = it.bbox
        pts.append((mm(bb.GetCenter().x), mm(bb.GetCenter().y)))
    touchF = any(in_fill(x, y, pcbnew.F_Cu) for x, y in pts)
    touchB = any(in_fill(x, y, pcbnew.B_Cu) for x, y in pts)
    tag = 'F' if touchF else ('B' if touchB else 'STRANDED')
    if tag == 'STRANDED':
        stranded.append((gi, pads, pts))
    print(f'group {gi}: {len(g)} items, pads={[p.desc for p in pads][:8]} touch={tag}')
print()
print('STRANDED groups:', len(stranded))
for gi, pads, pts in stranded:
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    print(f'  group {gi}: pads={[p.desc for p in pads]} bbox x[{min(xs):.1f},{max(xs):.1f}] y[{min(ys):.1f},{max(ys):.1f}]')
