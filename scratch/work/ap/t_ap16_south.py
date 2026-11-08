"""t_ap16: J1 DP_CON via the SOUTH DIVE (exp233).
Insight after ap12: A6's via cannot share the F north field with
DM's via+stub (mutual exclusions close every stagger). Instead A6
escapes SOUTH on F into the band between the pad rows, dives at
~(30.15,72.28), and B6 joins it there on F directly. Only CC2's
B5 escape is re-planned (via moved east in the band to
~(30.85,72.3), web re-flooded to its north via). DM_CON, CC1 and
VBUS_RAW stay exactly as built.
DP: A6 stub (29.75,71.48)->(29.82,72.15)->via; B6 join
(30.0,73.18)->(29.9,72.7)->via; In2 main flood via->D3 via (w0.25);
D3 stub. All gates exact item model; winner -> dp-design.json."""
import sys, math, json, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, pt_margin, seg_margin, in_box_pool,
                      fmt_it, pair_clr)
from router import netclass, dist_to_item
from collections import deque

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp233.kicad_pcb')
items = load_items(b)
A6 = (29.750, 71.480)
B6 = (30.000, 73.180)
B5 = (30.500, 73.180)
D31 = (44.362, 47.300)
CC2_NORTH = (31.375, 69.375)
BIGBOX = (26.0, 48.0, 42.0, 76.0)
JBOX = (27.5, 33.0, 66.0, 75.5)

def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))
def via(net, x, y, d):
    return ('via', net, (x, y, d / 2), netclass(net)[1])

SEG_RIPS = [
    ('CC2', 30.500, 72.930, 30.375, 72.375),
    ('CC2', 30.500, 73.180, 30.500, 72.930),
    ('CC2', 30.375, 72.375, 30.375, 71.625),
    ('CC2', 30.375, 71.625, 30.375, 70.875),
    ('CC2', 30.375, 70.875, 30.625, 70.625),
    ('CC2', 30.625, 70.625, 30.625, 70.125),
    ('CC2', 30.625, 70.125, 30.875, 69.875),
    ('CC2', 30.875, 69.875, 31.125, 69.625),
    ('CC2', 31.125, 69.625, 31.375, 69.375)]
VIA_RIPS = [('CC2', 30.375, 72.375)]

def rip_exact(items, seg_rips, via_rips):
    st = {li: [] for li in range(3)}
    n = 0
    sr = set()
    for (net, ax, ay, bx, by) in seg_rips:
        sr.add((net, round(ax, 3), round(ay, 3), round(bx, 3),
                round(by, 3)))
        sr.add((net, round(bx, 3), round(by, 3), round(ax, 3),
                round(ay, 3)))
    vr = set((net, round(x, 3), round(y, 3)) for net, x, y in via_rips)
    for li in range(3):
        for it in items[li]:
            if it[0] == 'seg':
                d = it[2]
                key = (it[1], round(d[0], 3), round(d[1], 3),
                       round(d[2], 3), round(d[3], 3))
                if key in sr:
                    n += 1
                    continue
            elif it[0] == 'via':
                d = it[2]
                if (it[1], round(d[0], 3), round(d[1], 3)) in vr:
                    n += 1
                    continue
            st[li].append(it)
    return st, n

statics, nrip = rip_exact(items, SEG_RIPS, VIA_RIPS)
print(f'rips: {nrip} entries (expect 12)')

def prep(pool):
    out = []
    for it in pool:
        k, net, d, clr = it
        if k == 'pad':
            c = (d[0], d[1]); reach = math.hypot(d[2], d[3])
        elif k == 'via':
            c = (d[0], d[1]); reach = d[2]
        else:
            c = ((d[0] + d[2]) / 2, (d[1] + d[3]) / 2)
            reach = math.hypot(d[2] - d[0], d[3] - d[1]) / 2 + d[4]
        out.append((it, c, reach))
    return out

def ptm_fast(pp, x, y, net, rad):
    m = 9.9; worst = None
    for it, c, reach in pp:
        if it[1] == net:
            continue
        if math.hypot(x - c[0], y - c[1]) - reach - rad \
                - pair_clr(net, it[1]) >= m:
            continue
        d = dist_to_item(it, x, y) - rad - pair_clr(net, it[1])
        if d < m:
            m, worst = d, it
    return m, worst

def segm_fast(pp, a, b, net, hw, step=0.05):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
    m = 9.9; worst = None
    for k in range(n + 1):
        mm_, w_ = ptm_fast(pp, a[0] + (b[0] - a[0]) * k / n,
                           a[1] + (b[1] - a[1]) * k / n, net, hw)
        if mm_ < m:
            m, worst = mm_, w_
    return m, worst

def build_pp(statics, adds, box=BIGBOX):
    it2 = {li: list(statics[li]) for li in range(3)}
    for a in adds:
        if isinstance(a[0], int):
            it2[a[0]].append(a[1])
        else:
            for li in range(3):
                it2[li].append(a)
    pool = in_box_pool(it2, box, pad=1.2)
    return {li: prep(pool[li]) for li in range(3)}, pool

def poly_margin(pp, li, poly, net, hw=0.10):
    m = 9.9
    for a, c in zip(poly, poly[1:]):
        if a == c:
            continue
        mm, _ = segm_fast(pp[li], a, c, net, hw)
        m = min(m, mm)
    return m

def stub_best(pp, polys, net, hw=0.10):
    best = -9.9
    best_poly = None
    for poly in polys:
        m = poly_margin(pp, 0, poly, net, hw)
        if m > best:
            best = m
            best_poly = poly
    return best, best_poly

def via_scan(pp, net, box, d, polys_fn):
    feas = []
    x0, x1, y0, y1 = box
    for ix in range(int((x1 - x0) / 0.025) + 1):
        x = x0 + ix * 0.025
        for iy in range(int((y1 - y0) / 0.025) + 1):
            y = y0 + iy * 0.025
            mv = min(ptm_fast(pp[li], x, y, net, d / 2)[0]
                     for li in range(3))
            if mv < -0.001:
                continue
            ms, poly = stub_best(pp, polys_fn((x, y)), net)
            if ms >= -0.001:
                feas.append((min(mv, ms), x, y, poly))
    feas.sort(key=lambda t: -t[0])
    return feas

GS = 0.0625
def flood_grid(ppL, box, rad, net):
    x0, x1, y0, y1 = box
    nx = int((x1 - x0) / GS) + 1
    ny = int((y1 - y0) / GS) + 1
    marg = {}
    for iy in range(ny):
        y = y0 + iy * GS
        for ix in range(nx):
            x = x0 + ix * GS
            m, _ = ptm_fast(ppL, x, y, net, rad)
            if m >= -0.001:
                marg[(ix, iy)] = m
    return marg

def flood(marg, ppL, box, D, R, rad, net):
    x0, x1, y0, y1 = box
    def cell(p):
        return (int(round((p[0] - x0) / GS)),
                int(round((p[1] - y0) / GS)))
    s, g = cell(D), cell(R)
    if s not in marg or g not in marg:
        return None, 'endpoint blocked'
    prev = {s: None}
    dq = deque([s])
    while dq:
        c = dq.popleft()
        if c == g:
            break
        cx, cy = c
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                n = (cx + dx, cy + dy)
                if n in prev or n not in marg:
                    continue
                if dx and dy and ((cx + dx, cy) not in marg
                                  or (cx, cy + dy) not in marg):
                    continue
                prev[n] = c
                dq.append(n)
    if g not in prev:
        return None, 'no path'
    path = []
    c = g
    while c is not None:
        path.append((x0 + c[0] * GS, y0 + c[1] * GS))
        c = prev[c]
    path.reverse()
    path[0] = D
    path[-1] = R
    chain = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1:
            m, _ = segm_fast(ppL, path[i], path[j], net, rad,
                             step=0.03125)
            if m >= -0.001:
                break
            j -= 1
        chain.append(path[j])
        i = j
    ms = [segm_fast(ppL, a, b, net, rad, step=0.03125)[0]
          for a, b in zip(chain, chain[1:])]
    return (min(ms) if ms else 9.9), chain

def chain_adds(net, li, chain, w):
    return [seg(net, li, a, c, w) for a, c in zip(chain, chain[1:])
            if a != c]

pp0, _ = build_pp(statics, [])
results = []

# ---- CC2 band via + join flood ----------------------------------------------
cc2s = via_scan(pp0, 'CC2', (30.50, 31.30, 71.90, 72.90), 0.5,
                lambda v: [[B5, v], [B5, (B5[0], v[1]), v],
                           [B5, (v[0], B5[1]), v],
                           [B5, (30.90, 72.90), v]])
print(f'CC2 band vias: {len(cc2s)}; best '
      f'{[(round(c[0], 3), c[1], c[2]) for c in cc2s[:5]]}')
grid_cc2 = flood_grid(pp0[1], JBOX, 0.10, 'CC2')
for (csc, cx, cy, cpoly) in cc2s[:4]:
    cm, cch = flood(grid_cc2, pp0[1], JBOX, (cx, cy), CC2_NORTH,
                    0.10, 'CC2')
    print(f'  CC2 via ({cx:.3f},{cy:.3f}): join flood {cm}')
    if cm is None:
        continue
    cc2_adds = [via('CC2', cx, cy, 0.5)]
    for a, c in zip(cpoly, cpoly[1:]):
        cc2_adds.append(seg('CC2', 0, a, c, 0.2))
    cc2_adds += chain_adds('CC2', 1, cch, 0.2)
    ppA, _ = build_pp(statics, cc2_adds)
    # ---- DP: A6 SOUTH DIVE (stub crosses B6's pad, joining it) ----
    def a6_polys(v):
        return [[A6, (29.850, 72.600), v],
                [A6, (29.800, 72.200), v],
                [A6, (29.900, 72.900), v],
                [A6, v]]
    a6s = via_scan(ppA, 'DP_CON', (29.60, 30.20, 73.60, 74.30), 0.5,
                   a6_polys)
    print(f'  DP A6 south vias: {len(a6s)}; best '
          f'{[(round(c[0], 3), c[1], c[2]) for c in a6s[:4]]}')
    for (asc, ax, ay, apoly) in a6s[:3]:
        bm = asc  # B6 joins via the stub's pad crossing (same net)
        bpoly = []
        dp_adds = [via('DP_CON', ax, ay, 0.5)]
        for a, c in zip(apoly, apoly[1:]):
            dp_adds.append(seg('DP_CON', 0, a, c, 0.2))
        ppB, _ = build_pp(statics, cc2_adds + dp_adds)
        d3s = via_scan(ppB, 'DP_CON', (43.20, 45.20, 45.90, 47.60),
                       0.5,
                       lambda v: [[D31, v], [D31, (v[0], D31[1]), v],
                                  [D31, (D31[0], v[1]), v]])
        print(f'    D3 vias: {len(d3s)}')
        gridBig = flood_grid(ppB[1], BIGBOX, 0.125, 'DP_CON')
        for (esc, ex, ey, epoly) in d3s[:3]:
            km, kch = flood(gridBig, ppB[1], BIGBOX, (ax, ay),
                            (ex, ey), 0.125, 'DP_CON')
            if km is None:
                continue
            results.append({
                'score': min(csc, cm, asc, bm, esc, km),
                'cc2_via': (cx, cy), 'cc2_stub': cpoly,
                'cc2_join': cch,
                'a6_via': (ax, ay), 'a6_stub': apoly,
                'b6_join': bpoly,
                'd3_via': (ex, ey), 'd3_stub': epoly,
                'main': kch})
            print(f'    ASSEMBLY main {km:+.3f} A6({ax:.2f},{ay:.2f}) '
                  f'CC2({cx:.2f},{cy:.2f}) D3({ex:.2f},{ey:.2f})')
            break
        if results:
            break
    if results:
        break
print(f'\ncomplete assemblies: {len(results)}')
if results:
    r = results[0]
    with open('scratch/work/ap/dp-design.json', 'w') as f:
        json.dump(r, f, indent=1)
    print('BEST saved; score', r['score'])
else:
    print('NO complete assembly')
