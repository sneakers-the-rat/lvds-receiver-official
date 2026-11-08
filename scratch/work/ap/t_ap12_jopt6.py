"""t_ap12: J1 escape district FULL re-plan v6 (exp233).
Changes vs ap9 (from the t_ap10 probe):
- EXACT pair-matched rips (no endpoint collateral): CC1's pad stub
  is KEPT (its -0.025 model margin vs the neighbour VBUS pad is a
  pre-existing board condition at the model's 0.25 power-class pair
  rule; KiCad's flat 0.2 rule is clean there). DM's staircase tail
  (30.375,69.625)->(30.125,69.875) KEPT (flood target is a real kept
  point); VBUS's (30.875,70.375)->(30.625,70.625) KEPT (rejoin
  target (30.625,70.625) is real).
- CC1 re-lay from the kept stub end (29.25,69.98), widths
  [0.25,0.25,0.2] (hw [0.125,0.125,0.10]).
Order: CC2 (top1) -> CC1 cfg (top3) -> DM via+joins -> VBUS rejoin
(NE jogs) -> DP (A6 tangent polys; junction In2 else B; main In2
w0.25). Winner -> scratch/work/ap/dp-design.json."""
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
A5S = (29.250, 69.980)
A7 = (30.250, 71.480)
A6 = (29.750, 71.480)
B6 = (30.000, 73.180)
B5 = (30.500, 73.180)
D31 = (44.362, 47.300)
CC1_ANCHOR = (30.925, 67.250)
CC2_NORTH = (31.375, 69.375)
DM_B7PT = (29.625, 72.125)
DM_STPT = (30.125, 69.875)
VB_A = (30.125, 71.125)
VB_B = (30.625, 70.625)
BIGBOX = (26.0, 48.0, 42.0, 76.0)
JBOX = (27.5, 33.0, 66.0, 75.5)

def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))
def via(net, x, y, d):
    return ('via', net, (x, y, d / 2), netclass(net)[1])

SEG_RIPS = [
    # DM_CON junction + stub (staircase tail kept)
    ('DM_CON', 29.875, 70.375, 30.250, 70.980),
    ('DM_CON', 30.250, 70.980, 30.250, 71.480),
    ('DM_CON', 29.625, 70.625, 29.875, 70.375),
    ('DM_CON', 30.125, 70.125, 29.875, 70.375),
    ('DM_CON', 30.125, 69.875, 30.125, 70.125),
    # CC2 web + stub (north via kept)
    ('CC2', 30.500, 72.930, 30.375, 72.375),
    ('CC2', 30.500, 73.180, 30.500, 72.930),
    ('CC2', 30.375, 72.375, 30.375, 71.625),
    ('CC2', 30.375, 71.625, 30.375, 70.875),
    ('CC2', 30.375, 70.875, 30.625, 70.625),
    ('CC2', 30.625, 70.625, 30.625, 70.125),
    ('CC2', 30.625, 70.125, 30.875, 69.875),
    ('CC2', 30.875, 69.875, 31.125, 69.625),
    ('CC2', 31.125, 69.625, 31.375, 69.375),
    # CC1 braid (pad stub kept)
    ('CC1', 29.875, 69.625, 29.250, 69.980),
    ('CC1', 30.125, 69.375, 29.875, 69.625),
    ('CC1', 30.125, 68.875, 30.125, 69.375),
    ('CC1', 30.375, 68.625, 30.125, 68.875),
    ('CC1', 30.625, 68.375, 30.375, 68.625),
    ('CC1', 30.875, 68.125, 30.625, 68.375),
    ('CC1', 30.875, 67.625, 30.875, 68.125),
    ('CC1', 30.925, 67.500, 30.875, 67.625),
    ('CC1', 30.925, 67.250, 30.925, 67.500),
    # VBUS_RAW staircase corner (continuation kept)
    ('VBUS_RAW', 30.375, 70.875, 30.125, 71.125),
    ('VBUS_RAW', 30.625, 70.625, 30.375, 70.875)]
VIA_RIPS = [('DM_CON', 29.875, 70.375), ('CC2', 30.375, 72.375)]

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
print(f'rips: {nrip} entries (expect 27)')

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

def poly_margin(pp, li, poly, net, hws):
    m = 9.9
    for i, (a, c) in enumerate(zip(poly, poly[1:])):
        if a == c:
            continue
        hw = hws[i] if isinstance(hws, (list, tuple)) else hws
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

# ---- CC2 (top-1) -----------------------------------------------------------
cc2s = via_scan(pp0, 'CC2', (29.90, 31.30, 71.90, 72.90), 0.5,
                lambda v: [[B5, v], [B5, (B5[0], v[1]), v],
                           [B5, (v[0], B5[1]), v]])
print(f'CC2 B5 vias: {len(cc2s)}; best '
      f'{[(round(c[0], 3), c[1], c[2]) for c in cc2s[:3]]}')
csc, cx, cy, cpoly = cc2s[0]
cm, cch = None, None
cc2_adds = [via('CC2', cx, cy, 0.5)]
for a, c in zip(cpoly, cpoly[1:]):
    cc2_adds.append(seg('CC2', 0, a, c, 0.2))
ppA, _ = build_pp(statics, cc2_adds)

# ---- CC1 configs ------------------------------------------------------------
cc1_cfgs = []
for ty in (69.60, 69.35, 69.10, 68.85):
    for ex in (30.30, 30.55, 30.80):
        poly = [A5S, (29.250, ty), (ex, ty), CC1_ANCHOR]
        m = poly_margin(ppA, 0, poly, 'CC1', [0.125, 0.125, 0.10])
        if m >= -0.001:
            cc1_cfgs.append((m, poly))
cc1_cfgs.sort(key=lambda t: -t[0])
print(f'CC1 configs feasible: {len(cc1_cfgs)}; '
      f'{[(round(c[0], 3), c[1][1], c[1][2]) for c in cc1_cfgs[:4]]}')

for (c1m, c1poly) in cc1_cfgs[:3]:
    cc1_adds = [seg('CC1', 0, a, c, w)
                for a, c, w in zip(c1poly, c1poly[1:],
                                   [0.25, 0.25, 0.2])]
    ppB, _ = build_pp(statics, cc2_adds + cc1_adds)
    # ---- DM ---------------------------------------------------------------
    dms = via_scan(ppB, 'DM_CON', (29.85, 30.60, 69.90, 70.90), 0.5,
                   lambda v: [[A7, v], [A7, (30.250, 70.980), v],
                              [A7, (v[0], A7[1]), v],
                              [A7, (30.550, 70.900), v]])
    print(f'  CC1 ty={c1poly[1][1]} ex={c1poly[2][0]}: DM vias '
          f'{len(dms)}; best '
          f'{[(round(c[0], 3), c[1], c[2]) for c in dms[:4]]}')
    for (dsc, dx, dy, dpoly) in dms[:3]:
        dm_adds = [via('DM_CON', dx, dy, 0.5)]
        for a, c in zip(dpoly, dpoly[1:]):
            dm_adds.append(seg('DM_CON', 0, a, c, 0.2))
        ppC, _ = build_pp(statics, cc2_adds + cc1_adds + dm_adds)
        # ---- VBUS rejoin (gated before the In2 join floods) --------
        vb_best = None
        for mx in (30.30, 30.45, 30.60, 30.75):
            for my in (70.55, 70.75, 70.95):
                m = poly_margin(ppC, 1, [VB_A, (mx, my), VB_B],
                                'VBUS_RAW', 0.10)
                if vb_best is None or m > vb_best[0]:
                    vb_best = (m, (mx, my))
        print(f'    VBUS rejoin (pre-flood): {vb_best}')
        if vb_best is None or vb_best[0] < -0.001:
            continue
        vb_adds = chain_adds('VBUS_RAW', 1, [VB_A, vb_best[1], VB_B],
                             0.2)
        ppC, _ = build_pp(statics, cc2_adds + cc1_adds + dm_adds
                          + vb_adds)
        # ---- CC2 join flood (after VBUS) -----------------------------
        grid_cc2 = flood_grid(ppC[1], JBOX, 0.10, 'CC2')
        cm, cch = flood(grid_cc2, ppC[1], JBOX, (cx, cy), CC2_NORTH,
                        0.10, 'CC2')
        print(f'    CC2 join flood (post-VBUS): {cm}')
        if cm is None:
            continue
        cc2_full = cc2_adds + chain_adds('CC2', 1, cch, 0.2)
        ppC, _ = build_pp(statics, cc2_full + cc1_adds + dm_adds
                          + vb_adds)
        grid_dm = flood_grid(ppC[1], JBOX, 0.10, 'DM_CON')
        m1, ch1 = flood(grid_dm, ppC[1], JBOX, (dx, dy), DM_STPT,
                        0.10, 'DM_CON')
        if m1 is None:
            continue
        dm_adds += chain_adds('DM_CON', 1, ch1, 0.2)
        ppC, _ = build_pp(statics, cc2_adds + cc1_adds + dm_adds)
        # ---- VBUS rejoin (gated before the In2 join floods) --------
        vb_best = None
        for mx in (30.30, 30.45, 30.60, 30.75):
            for my in (70.55, 70.75, 70.95):
                m = poly_margin(ppC, 1, [VB_A, (mx, my), VB_B],
                                'VBUS_RAW', 0.10)
                if vb_best is None or m > vb_best[0]:
                    vb_best = (m, (mx, my))
        print(f'    VBUS rejoin (pre-flood): {vb_best}')
        if vb_best is None or vb_best[0] < -0.001:
            continue
        vb_adds = chain_adds('VBUS_RAW', 1, [VB_A, vb_best[1], VB_B],
                             0.2)
        ppC, _ = build_pp(statics, cc2_adds + cc1_adds + dm_adds
                          + vb_adds)
        # ---- CC2 join flood (after VBUS) -----------------------------
        grid_cc2 = flood_grid(ppC[1], JBOX, 0.10, 'CC2')
        cm, cch = flood(grid_cc2, ppC[1], JBOX, (cx, cy), CC2_NORTH,
                        0.10, 'CC2')
        print(f'    CC2 join flood (post-VBUS): {cm}')
        if cm is None:
            continue
        cc2_full = cc2_adds + chain_adds('CC2', 1, cch, 0.2)
        ppC, _ = build_pp(statics, cc2_full + cc1_adds + dm_adds
                          + vb_adds)
        grid_dm = flood_grid(ppC[1], JBOX, 0.10, 'DM_CON')
        m2, ch2 = flood(grid_dm, ppC[1], JBOX, (dx, dy), DM_B7PT,
                        0.10, 'DM_CON')
        if m2 is None:
            continue
        dm_adds += chain_adds('DM_CON', 1, ch2, 0.2)
        print(f'    DM ({dx:.2f},{dy:.2f}): joins {m1:+.3f}/{m2:+.3f}')
        ppD, _ = build_pp(statics, cc2_adds + cc1_adds + dm_adds)
        # ---- VBUS rejoin ---------------------------------------------------
        vb_best = None
        for mx in (30.45, 30.60, 30.75, 30.90):
            for my in (70.55, 70.75, 70.95, 71.05):
                m = poly_margin(ppD, 1, [VB_A, (mx, my), VB_B],
                                'VBUS_RAW', 0.10)
                if vb_best is None or m > vb_best[0]:
                    vb_best = (m, (mx, my))
        print(f'    VBUS rejoin: {vb_best}')
        if vb_best is None or vb_best[0] < -0.001:
            continue
        vb_adds = chain_adds('VBUS_RAW', 1, [VB_A, vb_best[1], VB_B],
                             0.2)
        ppE, _ = build_pp(statics, cc2_adds + cc1_adds + dm_adds
                          + vb_adds)
        # ---- DP -------------------------------------------------------------
        a6s = via_scan(ppE, 'DP_CON', (29.30, 30.00, 69.50, 71.00),
                       0.5,
                       lambda v: [[A6, v],
                                  [A6, (29.650, 70.500), v],
                                  [A6, (29.650, 70.350), v],
                                  [A6, (29.800, 70.900), v],
                                  [A6, (v[0], A6[1]), v],
                                  [A6, (A6[0], v[1]), v]])
        b6s = via_scan(ppE, 'DP_CON', (28.70, 30.30, 73.60, 74.50),
                       0.5,
                       lambda v: [[B6, v], [B6, (B6[0], v[1]), v],
                                  [B6, (v[0], B6[1]), v]])
        d3s = via_scan(ppE, 'DP_CON', (43.20, 45.20, 45.90, 47.60),
                       0.5,
                       lambda v: [[D31, v], [D31, (v[0], D31[1]), v],
                                  [D31, (D31[0], v[1]), v]])
        print(f'    DP: A6 {len(a6s)} '
              f'{[(round(c[0],3), c[1], c[2]) for c in a6s[:3]]}; '
              f'B6 {len(b6s)}; D3 {len(d3s)}')
        if not a6s or not b6s or not d3s:
            continue
        gridJ1 = flood_grid(ppE[1], JBOX, 0.10, 'DP_CON')
        gridJ2 = flood_grid(ppE[2], JBOX, 0.10, 'DP_CON')
        gridBig = flood_grid(ppE[1], BIGBOX, 0.125, 'DP_CON')
        done = False
        for (asc, ax, ay, apoly) in a6s[:3]:
            for (bsc, bx, by, bpoly) in b6s[:3]:
                jm, jch = flood(gridJ1, ppE[1], JBOX, (bx, by),
                                (ax, ay), 0.10, 'DP_CON')
                jl = 1
                if jm is None:
                    jm, jch = flood(gridJ2, ppE[2], JBOX, (bx, by),
                                    (ax, ay), 0.10, 'DP_CON')
                    jl = 2
                if jm is None:
                    continue
                for (esc, ex, ey, epoly) in d3s[:3]:
                    km, kch = flood(gridBig, ppE[1], BIGBOX,
                                    (ax, ay), (ex, ey), 0.125,
                                    'DP_CON')
                    if km is None:
                        continue
                    results.append({
                        'score': min(csc, c1m, dsc, asc, bsc, esc, cm,
                                     m1, m2, vb_best[0], jm, km),
                        'vb_jog': vb_best[1], 'cc1_poly': c1poly,
                        'cc2_via': (cx, cy), 'cc2_stub': cpoly,
                        'cc2_join': cch,
                        'dm_via': (dx, dy), 'dm_stub': dpoly,
                        'dm_join_st': ch1, 'dm_join_b7': ch2,
                        'a6_via': (ax, ay), 'a6_stub': apoly,
                        'b6_via': (bx, by), 'b6_stub': bpoly,
                        'd3_via': (ex, ey), 'd3_stub': epoly,
                        'junction': jch, 'junction_layer': jl,
                        'main': kch})
                    print(f'    ASSEMBLY j {jm:+.3f} (L{jl}) main '
                          f'{km:+.3f} A6({ax:.2f},{ay:.2f}) '
                          f'B6({bx:.2f},{by:.2f}) D3({ex:.2f},{ey:.2f})')
                    done = True
                    break
                if done:
                    break
            if done:
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
