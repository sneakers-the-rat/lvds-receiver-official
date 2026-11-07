"""t_ag3: exact chains + neighbourhood census for the D5/XO design.
- Walk XO's In2 chain from its X1.2 via NW-ward, print vertices.
- Print every item (any net, any of F/In2/B) whose distance to the
  proposed new XO lane polyline or D5 journey polyline is < 1.0,
  with exact distances (obstacle census for hand design)."""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from router import netclass, dist_to_item
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp217.kicad_pcb')
LK = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
LN = ['F', 'In2', 'B']
items = {0: [], 1: [], 2: []}
for fp in b.GetFootprints():
    for pad in fp.Pads():
        net = pad.GetNetname()
        x, y = MM(pad.GetPosition())
        sx, sy = MM(pad.GetSize())
        data = (x, y, sx / 2, sy / 2, 0.0)
        for li, ln in enumerate(LK):
            if pad.IsOnLayer(ln):
                items[li].append(('pad', net, data,
                                  fp.GetReference() + '.' +
                                  pad.GetNumber()))
for t in b.GetTracks():
    net = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = MM(t.GetPosition())
        r = MM(t.GetWidth()) / 2
        for li in range(3):
            items[li].append(('via', net, (x, y, r), 'via'))
    else:
        if t.GetLayer() not in LK:
            continue
        li = LK.index(t.GetLayer())
        a, c = MM(t.GetStart()), MM(t.GetEnd())
        w = MM(t.GetWidth())
        items[li].append(('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                          'seg'))

# ---- walk XO In2 chain from via (86.125,10.375) ----
segs = [it[2] for it in items[1] if it[1] == 'XO' and it[0] == 'seg']
def key(p):
    return (round(p[0], 3), round(p[1], 3))
pool = {}
for s in segs:
    pool.setdefault(key((s[0], s[1])), []).append(s)
    pool.setdefault(key((s[2], s[3])), []).append(s)
start = (86.125, 10.375)
chain = [start]
cur = start
used = set()
for _ in range(200):
    nxt = None
    for s in pool.get(key(cur), []):
        if id(s) in used:
            continue
        a, bb = (s[0], s[1]), (s[2], s[3])
        if key(a) == key(cur):
            nxt = (s, bb)
            break
        if key(bb) == key(cur):
            nxt = (s, a)
            break
    if nxt is None:
        break
    used.add(id(nxt[0]))
    cur = nxt[1]
    chain.append(cur)
print('XO In2 chain from X1.2 via, NW-ward:')
for p in chain:
    print(f'  ({p[0]:.3f},{p[1]:.3f}) sum={p[0] + p[1]:.3f}')
print(f'  chain segs used: {len(used)} of {len(segs)} XO In2 segs')

# ---- obstacle census near proposed polylines ----
XO_NEW = [(80.625, 17.125), (81.2, 17.1), (87.9, 10.4)]
D5_NEW = [(80.25, 15.1875), (81.3, 15.35), (82.0, 15.3),
          (93.55, 3.75)]
def segdist(px, py, s):
    ax, ay, bx, by = s
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0,
                                ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
def item_dist_to_poly(it, poly):
    m = 9e9
    for a, bb in zip(poly, poly[1:]):
        if it[0] == 'seg':
            d = it[2]
            for t in [i / 16 for i in range(17)]:
                x = d[0] + (d[2] - d[0]) * t
                y = d[1] + (d[3] - d[1]) * t
                m = min(m, segdist(x, y, (a[0], a[1], bb[0], bb[1]))
                        - d[4])
            for p in ((d[0], d[1]), (d[2], d[3])):
                m = min(m, segdist(p[0], p[1],
                                   (a[0], a[1], bb[0], bb[1])) - d[4])
        elif it[0] == 'via':
            m = min(m, segdist(it[2][0], it[2][1],
                               (a[0], a[1], bb[0], bb[1])) - it[2][2])
        else:
            d = it[2]
            for cx in (d[0] - d[2], d[0], d[0] + d[2]):
                for cy in (d[1] - d[3], d[1], d[1] + d[3]):
                    m = min(m, segdist(cx, cy,
                                       (a[0], a[1], bb[0], bb[1])))
            m -= max(d[2], d[3]) * 0  # corner-sample approx only
    return m
for name, poly, own in (('XO_NEW', XO_NEW, 'XO'),
                        ('D5_NEW', D5_NEW, 'ULPI_D5')):
    print(f'--- items within 1.0 of {name} (centreline dist, '
          f'minus item half-size) ---')
    for li in range(3):
        for it in items[li]:
            if it[1] == own:
                continue
            d = item_dist_to_poly(it, poly)
            if d < 1.0:
                print(f'  {LN[li]} {it[0]} {it[1]} {it[3]} '
                      f'dist={d:+.3f} data={tuple(round(v,3) for v in it[2])}')
