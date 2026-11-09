"""t_aw23: which exp241 GND F islands are really disconnected (pad/via/
track-bridge graph), tie details, and the XO B-chain walk."""
import wx
_app = wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241.kicad_pcb')
F = pcbnew.F_Cu
zone = None
for z in b.Zones():
    if z.GetNetname() == 'GND' and z.IsOnLayer(F):
        zone = z
        break
fps = zone.GetFilledPolysList(F)
polys = []
for i in range(fps.OutlineCount()):
    out = fps.Outline(i)
    pts = [(pcbnew.ToMM(out.CPoint(k).x), pcbnew.ToMM(out.CPoint(k).y))
           for k in range(out.PointCount())]
    polys.append(pts)


def inside(pts, tx, ty):
    res = False
    m = len(pts)
    for k in range(m):
        x1, y1 = pts[k]
        x2, y2 = pts[(k + 1) % m]
        if (y1 > ty) != (y2 > ty):
            xin = (x2 - x1) * (ty - y1) / (y2 - y1) + x1
            if tx < xin:
                res = not res
    return res


def island_of(x, y):
    for i, pts in enumerate(polys):
        if inside(pts, x, y):
            return i
    return None


parent = list(range(len(polys)))


def union(a, c):
    if a is None or c is None:
        return
    ra, rc = a, c
    while parent[ra] != ra:
        ra = parent[ra]
    while parent[rc] != rc:
        rc = parent[rc]
    if ra != rc:
        parent[ra] = rc


def root(a):
    while parent[a] != a:
        a = parent[a]
    return a


pad_islands = set()
via_islands = set()
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == 'GND':
            pp = pcbnew.ToMM(p.GetPosition())
            ii = island_of(pp[0], pp[1])
            if ii is not None:
                pad_islands.add(ii)
for t in b.GetTracks():
    if t.GetNetname() != 'GND':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        pp = pcbnew.ToMM(t.GetPosition())
        ii = island_of(pp[0], pp[1])
        if ii is not None:
            via_islands.add(ii)
    else:
        a = pcbnew.ToMM(t.GetStart())
        c = pcbnew.ToMM(t.GetEnd())
        mx, my = (a[0] + c[0]) / 2, (a[1] + c[1]) / 2
        s = {island_of(a[0], a[1]), island_of(mx, my), island_of(c[0], c[1])}
        s.discard(None)
        s = list(s)
        for k in range(1, len(s)):
            union(s[0], s[k])

# main root = root of island 0 (largest, holds the board outline fill)
main = root(0)
print('pad islands:', sorted(pad_islands), flush=True)
print('via islands:', sorted(via_islands), flush=True)
for i, pts in enumerate(polys):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    conn = (root(i) == main) or (i in pad_islands) or (i in via_islands)
    print(f'island {i}: x[{min(xs):.2f},{max(xs):.2f}] '
          f'y[{min(ys):.2f},{max(ys):.2f}] root={root(i)} '
          f'pad={i in pad_islands} via={i in via_islands} '
          f'CONNECTED={conn}', flush=True)

print('--- XO B chain walk from (71.875,19.625) ---', flush=True)
segs = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != 'XO':
        continue
    if t.GetLayer() != pcbnew.B_Cu:
        continue
    a = pcbnew.ToMM(t.GetStart())
    c = pcbnew.ToMM(t.GetEnd())
    segs.append((tuple(round(v, 3) for v in a),
                 tuple(round(v, 3) for v in c)))
from collections import defaultdict
adj = defaultdict(list)
for (a, c) in segs:
    adj[a].append(c)
    adj[c].append(a)
cur = (71.875, 19.625)
prev = None
walk = [cur]
while True:
    nxts = [n for n in adj[cur] if n != prev]
    print(f'  joint {cur}: degree {len(adj[cur])}', flush=True)
    if not nxts:
        break
    if len(nxts) > 1:
        print(f'  BRANCH at {cur}: {nxts}', flush=True)
        break
    prev, cur = cur, nxts[0]
    walk.append(cur)
    if len(walk) > 40:
        break
print('  walk:', walk, flush=True)
print('  vias near walk end:', flush=True)
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == 'XO':
        p = pcbnew.ToMM(t.GetPosition())
        print(f'    XO via ({p[0]:.3f},{p[1]:.3f})', flush=True)
print('T_AW23 COMPLETE', flush=True)
