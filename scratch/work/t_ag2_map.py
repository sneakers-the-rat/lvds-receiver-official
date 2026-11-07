"""t_ag2: ASCII geography of the district + XO/XI group analysis.
Raster 0.25 mm over box, per layer F/In2/B: each cell shows the
net whose copper covers the cell centre (track capsule approx via
segment distance, pads as rects, vias as discs). Also union-find
groups for XO and XI (items + pads, same-layer touch + vias)."""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp217.kicad_pcb')
LK = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
LN = ['F', 'In2', 'B']

# ---- item model (same construction as t_af scripts) ----
items = {0: [], 1: [], 2: []}
pads = []
for fp in b.GetFootprints():
    for pad in fp.Pads():
        net = pad.GetNetname()
        x, y = MM(pad.GetPosition())
        sx, sy = MM(pad.GetSize())
        pads.append((fp.GetReference(), pad.GetNumber(), net, x, y,
                     sx / 2, sy / 2))
        for li, ln in enumerate(LK):
            if pad.IsOnLayer(ln):
                items[li].append(('pad', net,
                                   (x, y, sx / 2, sy / 2, 0.0),
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

def segdist(px, py, s):
    ax, ay, bx, by = s[0], s[1], s[2], s[3]
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0,
                                ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

SHORT = {'ULPI_D4': '4', 'ULPI_D5': '5', 'ULPI_D6': '6',
         'ULPI_D7': '7', 'ULPI_D3': '3', 'ULPI_D2': '2',
         'ULPI_D1': '1', 'ULPI_D0': '0', 'XO': 'X', 'XI': 'i',
         'I2C_SCL': 'L', 'I2C_SDA': 'A', '+3V3D': 'P', 'NRST': 'N',
         'GND': 'g', 'PHY_1V8': 'V', '+3V3A': 'a', 'ULPI_CK': 'K',
         'CDR_SQUELCH': 'Q', 'VCAP2': 'c', '': '.'}

def raster(li, x0, x1, y0, y1, step=0.25):
    print(f'--- layer {LN[li]} x[{x0},{x1}] y[{y0},{y1}] step {step}')
    print('     ' + ''.join(str(int(x * 10) % 10) if abs(x * 4 -
          round(x * 4)) < 1e-9 and int(round(x * 4)) % 4 == 0 else ' '
          for x in [x0 + i * step for i in
                    range(int((x1 - x0) / step) + 1)]))
    ny = int((y1 - y0) / step) + 1
    for j in range(ny):
        y = y0 + j * step
        row = []
        nx = int((x1 - x0) / step) + 1
        for i in range(nx):
            x = x0 + i * step
            ch = '.'
            for kind, net, d, tag in items[li]:
                if kind == 'seg':
                    if segdist(x, y, d) <= d[4] + 1e-9:
                        ch = SHORT.get(net, '?')
                        break
                elif kind == 'via':
                    if math.hypot(x - d[0], y - d[1]) <= d[2] + 1e-9:
                        ch = SHORT.get(net, '?')
                        break
                elif kind == 'pad':
                    if abs(x - d[0]) <= d[2] + 1e-9 and \
                       abs(y - d[1]) <= d[3] + 1e-9:
                        ch = SHORT.get(net, '?')
                        break
            row.append(ch)
        print(f'{y:5.2f}' + ''.join(row))

raster(1, 78.0, 95.0, 0.0, 18.0)
raster(2, 78.0, 95.0, 0.0, 18.0)
raster(0, 78.0, 95.0, 8.0, 18.0)
raster(1, 70.0, 79.0, 8.0, 18.0)
raster(0, 70.0, 79.0, 8.0, 18.0)

# ---- union-find for XO / XI over all layers ----
def items_touch(a, b):
    ka, da = a[0], a[2]
    kb, db = b[0], b[2]
    def pt_item(px, py, it):
        if it[0] == 'seg':
            return segdist(px, py, it[2]) - it[2][4]
        if it[0] == 'via':
            return math.hypot(px - it[2][0], py - it[2][1]) - it[2][2]
        return max(abs(px - it[2][0]) - it[2][2],
                   abs(py - it[2][1]) - it[2][3])
    def seg_seg(s1, s2):
        # sample-based
        m = 9e9
        for t in [i / 20 for i in range(21)]:
            x = s1[0] + (s1[2] - s1[0]) * t
            y = s1[1] + (s1[3] - s1[1]) * t
            m = min(m, segdist(x, y, s2) - s2[4])
        return m
    if ka == 'seg' and kb == 'seg':
        return seg_seg(da, db) <= 0.02 or seg_seg(db, da) <= 0.02
    if ka == 'seg':
        return pt_item(da[0], da[1], b) <= 0.02 or \
            pt_item(da[2], da[3], b) <= 0.02
    if kb == 'seg':
        return pt_item(db[0], db[1], a) <= 0.02 or \
            pt_item(db[2], db[3], a) <= 0.02
    if ka == 'via' and kb == 'via':
        return math.hypot(da[0] - db[0], da[1] - db[1]) <= \
            da[2] + db[2] + 0.02
    if ka == 'via' and kb == 'pad':
        return max(abs(da[0] - db[0]) - db[2],
                   abs(da[1] - db[1]) - db[3]) <= da[2] + 0.02
    if ka == 'pad' and kb == 'via':
        return items_touch(b, a)
    # pad-pad same footprint handled by net anyway; use rect gap
    gx = max(abs(da[0] - db[0]) - da[2] - db[2], 0)
    gy = max(abs(da[1] - db[1]) - da[3] - db[3], 0)
    return math.hypot(gx, gy) <= 0.02

import itertools
for NET in ('XO', 'XI'):
    nodes = []
    for li in range(3):
        for it in items[li]:
            if it[1] == NET:
                nodes.append((li, it))
    parent = list(range(len(nodes)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj
    # via nodes appear on all 3 layers with same (x,y): they link layers
    for i, j in itertools.combinations(range(len(nodes)), 2):
        li, a = nodes[i]
        lj, bb = nodes[j]
        if a[0] == 'via' and bb[0] == 'via' and \
           abs(a[2][0] - bb[2][0]) < 0.01 and \
           abs(a[2][1] - bb[2][1]) < 0.01:
            union(i, j)
            continue
        if li != lj:
            continue
        if items_touch(a, bb):
            union(i, j)
    groups = {}
    for i in range(len(nodes)):
        groups.setdefault(find(i), []).append(nodes[i])
    print(f'=== {NET}: {len(groups)} groups ===')
    for g in groups.values():
        xs, ys, pp = [], [], set()
        for li, it in g:
            d = it[2]
            if it[0] == 'seg':
                xs += [d[0], d[2]]
                ys += [d[1], d[3]]
            else:
                xs.append(d[0])
                ys.append(d[1])
            if it[0] == 'pad':
                pp.add(it[3])
        print(f'  n={len(g)} bbox x[{min(xs):.2f},{max(xs):.2f}] '
              f'y[{min(ys):.2f},{max(ys):.2f}] pads={sorted(pp)}')
