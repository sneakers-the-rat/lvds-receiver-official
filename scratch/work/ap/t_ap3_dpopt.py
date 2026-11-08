"""t_ap3: DP_CON computational design (exp233), mirroring DM_CON.
DP_CON has three bare pads: J1.A6 (29.75,71.48), J1.B6 (30.0,73.18),
D3.1 (44.362,47.3). DM_CON's proven pattern: F stubs to vias, In2
join at J1, w0.25 In2 staircase to a D3 escape via.
Steps: (1) escape-via scans for A6/B6/D3.1 on the exact item model
(stub gates included; B6 gets L-shaped stub options S-then-W and
straight); (2) In2 floods: B6via->A6via (junction) and
junction->D3via (main journey, big box), w0.25; (3) exact re-gate
of the winning assembly; design -> scratch/work/ap/dp-design.json.
DP_CON gated at default class 0.20 (library pair_clr)."""
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
NET = 'DP_CON'
A6 = (29.750, 71.480)
B6 = (30.000, 73.180)
D31 = (44.362, 47.300)
BIGBOX = (26.0, 48.0, 42.0, 76.0)

def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))
def via(net, x, y, d):
    return ('via', net, (x, y, d / 2), netclass(net)[1])

pool_all = in_box_pool(items, BIGBOX, pad=1.2)

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

pp = {li: prep(pool_all[li]) for li in range(3)}

def via_scan(box, stub_polys, d=0.5):
    """stub_polys: fn(via_pt) -> list of F polylines (each a point
    list) of which at least one must gate >= -0.001 (w0.2)."""
    feas = []
    x0, x1, y0, y1 = box
    gx = int((x1 - x0) / 0.025)
    gy = int((y1 - y0) / 0.025)
    for ix in range(gx + 1):
        x = x0 + ix * 0.025
        for iy in range(gy + 1):
            y = y0 + iy * 0.025
            mv = min(ptm_fast(pp[li], x, y, NET, d / 2)[0]
                     for li in range(3))
            if mv < -0.001:
                continue
            best_stub = -9.9
            for poly in stub_polys((x, y)):
                m = 9.9
                for a, c in zip(poly, poly[1:]):
                    mm, _ = segm_fast(pp[0], a, c, NET, 0.10)
                    m = min(m, mm)
                best_stub = max(best_stub, m)
            if best_stub >= -0.001:
                feas.append((min(mv, best_stub), x, y))
    feas.sort(reverse=True)
    return feas

print('--- A6 escape scan ---')
a6 = via_scan((28.90, 30.30, 69.90, 71.30),
              lambda v: [[A6, v]])
print(f'A6 vias: {len(a6)}; best {a6[:5]}')
print('--- B6 escape scan (straight + S-then-W L stubs) ---')
def b6_polys(v):
    return [[B6, v],
            [B6, (B6[0], v[1]), v],
            [B6, (v[0], B6[1]), v]]
b6 = via_scan((28.60, 31.60, 71.90, 74.60), b6_polys)
print(f'B6 vias: {len(b6)}; best {b6[:5]}')
print('--- D3.1 escape scan ---')
d3 = via_scan((43.20, 45.20, 45.90, 47.60),
              lambda v: [[D31, v], [D31, (v[0], D31[1]), v],
                         [D31, (D31[0], v[1]), v]])
print(f'D3 vias: {len(d3)}; best {d3[:5]}')

# ---------- In2 flood ---------------------------------------------------
GS = 0.0625
def flood_grid(ppL, box, rad):
    x0, x1, y0, y1 = box
    nx = int((x1 - x0) / GS) + 1
    ny = int((y1 - y0) / GS) + 1
    marg = {}
    for iy in range(ny):
        y = y0 + iy * GS
        for ix in range(nx):
            x = x0 + ix * GS
            m, _ = ptm_fast(ppL, x, y, NET, rad)
            if m >= -0.001:
                marg[(ix, iy)] = m
    return marg

def flood(marg, ppL, box, D, R, rad):
    x0, x1, y0, y1 = box
    def cell(p):
        return (int(round((p[0] - x0) / GS)),
                int(round((p[1] - y0) / GS)))
    s, g = cell(D), cell(R)
    if s not in marg or g not in marg:
        return None, 'endpoint cell blocked'
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
            m, _ = segm_fast(ppL, path[i], path[j], NET, rad,
                             step=0.03125)
            if m >= -0.001:
                break
            j -= 1
        chain.append(path[j])
        i = j
    ms = [segm_fast(ppL, a, b, NET, rad, step=0.03125)[0]
          for a, b in zip(chain, chain[1:])]
    return (min(ms) if ms else 9.9), chain

RAD = 0.125  # w0.25 staircase, mirroring DM_CON
print('--- floods ---')
results = []
if a6 and b6 and d3:
    grid_big = flood_grid(pp[1], BIGBOX, RAD)
    print(f'big grid free cells: {len(grid_big)}')
    for (asc, ax, ay) in a6[:3]:
        for (bsc, bx, by) in b6[:3]:
            jm, ch = flood(grid_big, pp[1], BIGBOX, (bx, by), (ax, ay),
                           RAD)
            print(f'  junction B6({bx:.3f},{by:.3f})->A6({ax:.3f},{ay:.3f})'
                  f': {jm if jm is None else round(jm, 3)}')
            if jm is None:
                continue
            for (dsc, dx_, dy_) in d3[:3]:
                km, kh = flood(grid_big, pp[1], BIGBOX, (ax, ay),
                               (dx_, dy_), RAD)
                print(f'    main A6->D3({dx_:.3f},{dy_:.3f}): '
                      f'{km if km is None else round(km, 3)}')
                if km is not None:
                    results.append((min(jm, km), (ax, ay), (bx, by),
                                    (dx_, dy_), ch, kh))
results.sort(key=lambda t: -t[0])
print(f'complete assemblies: {len(results)}')
if results:
    r = results[0]
    print(f'BEST: score {r[0]:+.3f} A6via {r[1]} B6via {r[2]} '
          f'D3via {r[3]}')
    print(f'  junction chain: {r[4]}')
    print(f'  main chain: {r[5]}')
    design = {'score': r[0], 'a6_via': r[1], 'b6_via': r[2],
              'd3_via': r[3], 'junction': r[4], 'main': r[5]}
    with open('scratch/work/ap/dp-design.json', 'w') as f:
        json.dump(design, f, indent=1)
    print('saved scratch/work/ap/dp-design.json')
else:
    print('NO complete assembly')
