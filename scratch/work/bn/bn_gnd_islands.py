"""Find F.Cu GND zone-fill islands on a board and what copper each holds."""
import re, sys
import wx
_app = wx.App(False)
import pcbnew

path = sys.argv[1]
txt = open(path).read()
# locate the GND zone block(s): find '(zone' ... '(net_name "GND")' ... filled_polygon on F.Cu
polys = []
for zm in re.finditer(r'\(zone\b', txt):
    start = zm.start()
    # zone block ends heuristically at the next '\n\t(zone' or file end; take 400k chars
    block = txt[start:start + 600000]
    nm = re.search(r'\(net_name "([^"]*)"\)', block[:2000])
    if not nm or nm.group(1) != 'GND':
        continue
    for fm in re.finditer(r'\(filled_polygon\s*\(layer "F\.Cu"\)\s*\(pts(.*?)\)\s*\)', block, re.S):
        pts = [(float(x), float(y)) for x, y in
               re.findall(r'\(xy (-?[\d.]+) (-?[\d.]+)\)', fm.group(1))]
        if len(pts) >= 3:
            polys.append(pts)
print(f'GND F.Cu filled outlines: {len(polys)}')

# union-find over outlines: same island if any vertices within 0.02 or bboxes touch
n = len(polys)
parent = list(range(n))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
def union(i, j):
    ri, rj = find(i), find(j)
    if ri != rj: parent[ri] = rj
bb = [(min(x for x, y in p), max(x for x, y in p), min(y for x, y in p), max(y for x, y in p)) for p in polys]
for i in range(n):
    for j in range(i + 1, n):
        if bb[i][0] > bb[j][1] + 0.02 or bb[j][0] > bb[i][1] + 0.02 or bb[i][2] > bb[j][3] + 0.02 or bb[j][2] > bb[i][3] + 0.02:
            continue
        close = any(abs(x1 - x2) < 0.02 and abs(y1 - y2) < 0.02
                    for x1, y1 in polys[i] for x2, y2 in polys[j])
        if close: union(i, j)
comps = {}
for i in range(n):
    comps.setdefault(find(i), []).append(i)
print(f'islands: {len(comps)}')

def inside(pt, poly):
    x, y = pt; c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c

b = pcbnew.LoadBoard(path)
pads = []
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() == 'GND':
            p = pad.GetPosition()
            pads.append((f'{fp.GetReference()}.{pad.GetNumber()}', p.x / 1e6, p.y / 1e6,
                         'F' if pad.IsOnLayer(pcbnew.F_Cu) else '-'))
vias = []
for t in b.GetTracks():
    if t.GetNetname() == 'GND' and t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        vias.append((p.x / 1e6, p.y / 1e6))
for root, idxs in sorted(comps.items(), key=lambda kv: -len(kv[1])):
    xs = [x for i in idxs for x, y in polys[i]]; ys = [y for i in idxs for x, y in polys[i]]
    hp = [nm for nm, x, y, l in pads if l == 'F' and any(inside((x, y), polys[i]) for i in idxs)]
    hv = sum(1 for x, y in vias if any(inside((x, y), polys[i]) for i in idxs))
    print(f'island outlines={len(idxs)} bbox x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}] F-pads={len(hp)} vias={hv} {hp[:8]}')
