"""t_ap4: J1 escape JOINT optimizer (exp233).
Finding (t_ap3): A6 has NO escape via while DM_CON's A7 via
(29.875,70.375) d0.6 stands -- its 0.75 exclusion disc blankets
A6's whole north; CC1's braid fences the NW, CC2 the NE.
Design: rip DM's A7 via + F stub + its two In2 junction segs;
jointly place (DM via, A6 via, B6 via) with stub gates; re-join
DM on In2; DP_CON joins A6via<->B6via on In2 (w0.2) and runs the
main staircase A6via->D3via on In2 (w0.25, mirroring DM) by flood;
D3.1 escape via from t_ap3's scan family. Exact re-gate of the
winning assembly; design -> scratch/work/ap/dp-design.json."""
import sys, math, json, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, pt_margin, seg_margin, in_box_pool,
                      apply_rip, fmt_it, pair_clr)
from router import netclass, dist_to_item
from collections import deque

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp233.kicad_pcb')
items = load_items(b)
A7 = (30.250, 71.480)
A6 = (29.750, 71.480)
B6 = (30.000, 73.180)
D31 = (44.362, 47.300)
BIGBOX = (26.0, 48.0, 42.0, 76.0)
JBOX = (27.5, 33.0, 66.0, 75.5)

def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))
def via(net, x, y, d):
    return ('via', net, (x, y, d / 2), netclass(net)[1])

RIP_DM = [('via', 'DM_CON', 29.875, 70.375),
          ('seg', 'DM_CON', 29.875, 70.375),
          ('seg', 'DM_CON', 30.250, 70.980),
          ('seg', 'DM_CON', 30.125, 70.125),
          ('seg', 'DM_CON', 29.625, 70.625)]
statics, nrip = apply_rip(items, RIP_DM)
print(f'DM rips: {nrip} entries')
# DM In2 re-join anchor points (ends of the ripped junction segs)
DM_B7PT = (29.625, 70.625)    # B7 chain end
DM_STPT = (30.125, 70.125)    # staircase entry end

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

def stub_best(pp, polys, net, hw=0.10):
    best = -9.9
    best_poly = None
    for poly in polys:
        m = 9.9
        for a, c in zip(poly, poly[1:]):
            mm, _ = segm_fast(pp[0], a, c, net, hw)
            m = min(m, mm)
        if m > best:
            best = m
            best_poly = poly
    return best, best_poly

pp0, _ = build_pp(statics, [])
# ---- stage 1: DM via scan (d0.6, as existing) -------------------------
dm_cands = []
for ix in range(33):
    x = 29.90 + ix * 0.025
    for iy in range(49):
        y = 69.50 + iy * 0.025
        mv = min(ptm_fast(pp0[li], x, y, 'DM_CON', 0.30)[0]
                 for li in range(3))
        if mv < -0.001:
            continue
        ms, poly = stub_best(pp0, [[A7, (x, y)],
                                   [A7, (30.250, 70.980), (x, y)],
                                   [A7, (x, A7[1]), (x, y)]], 'DM_CON')
        if ms < -0.001:
            continue
        # In2 re-join segs (w0.2) to both anchors
        mj = min(segm_fast(pp0[1], (x, y), DM_B7PT, 'DM_CON', 0.10)[0],
                 segm_fast(pp0[1], (x, y), DM_STPT, 'DM_CON', 0.10)[0])
        if mj < -0.001:
            continue
        dm_cands.append((min(mv, ms, mj), x, y, poly))
dm_cands.sort(reverse=True)
print(f'DM via candidates: {len(dm_cands)}; best {dm_cands[:5]}')

# ---- stage 2: A6 via scan per DM candidate ----------------------------
def a6_scan(pp):
    feas = []
    for ix in range(29):
        x = 29.30 + ix * 0.025
        for iy in range(37):
            y = 70.00 + iy * 0.025
            mv = min(ptm_fast(pp[li], x, y, 'DP_CON', 0.25)[0]
                     for li in range(3))
            if mv < -0.001:
                continue
            ms, _ = stub_best(pp, [[A6, (x, y)],
                                   [A6, (29.800, 70.900), (x, y)],
                                   [A6, (x, A6[1]), (x, y)],
                                   [A6, (A6[0], y), (x, y)]], 'DP_CON')
            if ms >= -0.001:
                feas.append((min(mv, ms), x, y))
    feas.sort(reverse=True)
    return feas

# ---- stage 3: B6 via scan (near-pad regions) ---------------------------
def b6_scan(pp):
    feas = []
    for (x0, x1, y0, y1) in ((28.70, 30.30, 73.60, 74.50),
                            (31.20, 31.80, 73.80, 74.80)):
        for ix in range(int((x1 - x0) / 0.025) + 1):
            x = x0 + ix * 0.025
            for iy in range(int((y1 - y0) / 0.025) + 1):
                y = y0 + iy * 0.025
                mv = min(ptm_fast(pp[li], x, y, 'DP_CON', 0.25)[0]
                         for li in range(3))
                if mv < -0.001:
                    continue
                ms, _ = stub_best(pp, [[B6, (x, y)],
                                       [B6, (B6[0], y), (x, y)],
                                       [B6, (x, B6[1]), (x, y)]], 'DP_CON')
                if ms >= -0.001:
                    feas.append((min(mv, ms), x, y))
    feas.sort(reverse=True)
    return feas

# ---- D3.1 via shortlist (from t_ap3 family + north spots) --------------
def d3_scan(pp):
    feas = []
    for ix in range(81):
        x = 43.20 + ix * 0.025
        for iy in range(69):
            y = 45.90 + iy * 0.025
            mv = min(ptm_fast(pp[li], x, y, 'DP_CON', 0.25)[0]
                     for li in range(3))
            if mv < -0.001:
                continue
            ms, _ = stub_best(pp, [[D31, (x, y)],
                                   [D31, (x, D31[1]), (x, y)],
                                   [D31, (D31[0], y), (x, y)]], 'DP_CON')
            if ms >= -0.001:
                feas.append((min(mv, ms), x, y))
    feas.sort(reverse=True)
    return feas

# ---- floods --------------------------------------------------------------
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

results = []
for (dmsc, dmx, dmy, dpoly) in dm_cands[:4]:
    dm_adds = [via('DM_CON', dmx, dmy, 0.6),
               seg('DM_CON', 1, (dmx, dmy), DM_B7PT, 0.2),
               seg('DM_CON', 1, (dmx, dmy), DM_STPT, 0.2)]
    for a, c in zip(dpoly, dpoly[1:]):
        dm_adds.append(seg('DM_CON', 0, a, c, 0.2))
    ppA, _ = build_pp(statics, dm_adds)
    a6s = a6_scan(ppA)
    print(f'DM via ({dmx:.3f},{dmy:.3f}) sc {dmsc:+.3f}: A6 vias '
          f'{len(a6s)} best {a6s[:3]}')
    if not a6s:
        continue
    b6s = b6_scan(ppA)
    d3s = d3_scan(ppA)
    print(f'   B6 vias {len(b6s)} best {b6s[:3]}; D3 vias {len(d3s)} '
          f'best {d3s[:3]}')
    if not b6s or not d3s:
        continue
    gridJ = flood_grid(ppA[1], JBOX, 0.10, 'DP_CON')
    gridB = flood_grid(ppA[1], BIGBOX, 0.125, 'DP_CON')
    for (asc, ax, ay) in a6s[:3]:
        for (bsc, bx, by) in b6s[:4]:
            jm, jch = flood(gridJ, ppA[1], JBOX, (bx, by), (ax, ay),
                            0.10, 'DP_CON')
            if jm is None:
                continue
            for (esc, ex, ey) in d3s[:3]:
                km, kch = flood(gridB, ppA[1], BIGBOX, (ax, ay),
                                (ex, ey), 0.125, 'DP_CON')
                if km is None:
                    continue
                results.append((min(jm, km), (dmx, dmy), (ax, ay),
                                (bx, by), (ex, ey), jch, kch, dpoly))
                print(f'   ASSEMBLY: DM({dmx:.2f},{dmy:.2f}) '
                      f'A6({ax:.2f},{ay:.2f}) B6({bx:.2f},{by:.2f}) '
                      f'D3({ex:.2f},{ey:.2f}) j {jm:+.3f} main '
                      f'{km:+.3f}')
    if results:
        break
results.sort(key=lambda t: -t[0])
print(f'\ncomplete assemblies: {len(results)}')
if results:
    r = results[0]
    design = {'score': r[0], 'dm_via': r[1], 'a6_via': r[2],
              'b6_via': r[3], 'd3_via': r[4], 'junction': r[5],
              'main': r[6], 'dm_stub': r[7]}
    with open('scratch/work/ap/dp-design.json', 'w') as f:
        json.dump(design, f, indent=1)
    print('BEST:', json.dumps(design, indent=1))
else:
    print('NO complete assembly')
