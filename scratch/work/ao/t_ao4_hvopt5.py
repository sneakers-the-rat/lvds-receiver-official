"""t_ao4: HV pocket joint optimizer v5 (exp231) -- ao session.
Derived from t_ao1 (flood journey machinery kept verbatim) with the
variant family replaced, per the t_ao2/t_ao3 wall findings:
 - dives exist (+0.014 best) ONLY under SW SHDN placements with a
   single-diagonal In2 web; those placements are themselves -0.178
   vs the +5V staircase joint area (31.15,-4.0) / +5V pad corner.
 - V5 therefore MOVES the +5V joint J east to 31.35/31.45/31.55,
   re-fans BOTH staircases from J, dives the +5V run to In2
   (30.55,-4.45)->(31.30,-4.45) so no F run crosses under the SHDN
   via, and gives SHDN a LAZY diagonal web to (cx,-2.875),
   cx in {32.4, 32.9}. SHDN scan box is the SW/central mouth
   x[30.50,31.10] y[-3.65,-3.30] at 0.025. Statics = V4 rip set
   (both run segs ripped).
Dive/rise boxes and the flood journey are t_ao1's. Complete designs
exact-re-gated; best -> scratch/work/ao/hv-design.json.
HV_INTVCC gated at its real class 0.20 (library pair_clr)."""
import sys, math, json, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, pt_margin, seg_margin, in_box_pool,
                      apply_rip, fmt_it, pair_clr)
from router import netclass, dist_to_item
from collections import deque

b = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1
                     else 'hw/pdlvds_rx.exp231.kicad_pcb')
items = load_items(b)
BOX = (29.0, 34.6, -6.4, 1.5)
A0 = (30.375, -3.0)
R0 = (30.775, -0.5)

def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))
def via(net, x, y, d):
    return ('via', net, (x, y, d / 2), netclass(net)[1])

RIP_SHDN = [('via', 'HV_SHDN', 30.875, -2.875),
            ('seg', 'HV_SHDN', 30.625, -3.375),
            ('seg', 'HV_SHDN', 30.875, -3.125),
            ('seg', 'HV_SHDN', 30.875, -2.875)]
RIP_NE = [('seg', '+5V', 30.400, -4.000), ('seg', '+5V', 31.125, -3.875),
          ('seg', '+5V', 31.375, -3.625), ('seg', '+5V', 31.625, -3.375)]
RIP_SE = [('seg', '+5V', 31.625, -4.375), ('seg', '+5V', 31.375, -4.750)]
RIP_RUN2 = [('seg', '+5V', 29.650, -4.000)]
RIP_RUN1 = [('seg', '+5V', 31.150, -4.000)]

statics_b, n_b = apply_rip(items, RIP_SHDN + RIP_NE + RIP_SE)
statics_v3, n_v3 = apply_rip(statics_b, RIP_RUN2)
statics_v4, n_v4 = apply_rip(statics_b, RIP_RUN2 + RIP_RUN1)
print(f'rips: base {n_b} entries, V3 extra {n_v3}, V4 extra {n_v4}')

def ne_refan():
    return [seg('+5V', 0, (31.150, -4.000), (31.550, -4.350), 0.6),
            seg('+5V', 0, (31.550, -4.350), (32.000, -3.900), 0.6),
            seg('+5V', 0, (32.000, -3.900), (31.950, -3.350), 0.6),
            seg('+5V', 0, (31.950, -3.350), (31.875, -3.125), 0.6)]

def se_refan(e1, e2):
    return [seg('+5V', 0, (31.150, -4.000), e1, 0.6),
            seg('+5V', 0, e1, e2, 0.6),
            seg('+5V', 0, e2, (31.375, -5.500), 0.6)]

def shdn_adds(sx, sy, sd, cx):
    """ao4: LAZY DIAGONAL web -- In2 diagonal (sx,sy)->(cx,-2.875),
    then the kept east horizontal. cx in {32.4, 32.9} (never None)."""
    return [via('HV_SHDN', sx, sy, sd),
            seg('HV_SHDN', 0, (30.375, -3.500), (sx, sy), 0.2),
            seg('HV_SHDN', 1, (sx, sy), (cx, -2.875), 0.25),
            seg('HV_SHDN', 1, (cx, -2.875), (43.375, -2.875), 0.25)]

def p5v_v3_adds(dx, in2y, rx):
    return [seg('+5V', 0, (29.650, -4.000), (dx, in2y), 0.2),
            via('+5V', dx, in2y, 0.6),
            seg('+5V', 1, (dx, in2y), (rx, in2y), 0.6),
            via('+5V', rx, in2y, 0.6),
            seg('+5V', 0, (rx, in2y), (31.150, -4.000), 0.2),
            seg('+5V', 0, (rx, in2y), (31.125, -3.875), 0.2)]

def p5v_v4_adds(ys, xt):
    return [seg('+5V', 0, (29.650, -4.000), (30.100, ys), 0.2),
            seg('+5V', 0, (30.100, ys), (xt, ys), 0.2),
            seg('+5V', 0, (xt, ys), (31.150, -4.000), 0.2)]

# ---- ao4 (v5) builders: +5V joint J moved east, run dives to In2 ----
def ne_refan5(J):
    return [seg('+5V', 0, J, (J[0] + 0.35, -3.550), 0.6),
            seg('+5V', 0, (J[0] + 0.35, -3.550), (31.875, -3.125), 0.6)]

def se_refan5(J):
    return [seg('+5V', 0, J, (32.000, -4.500), 0.6),
            seg('+5V', 0, (32.000, -4.500), (31.700, -5.100), 0.6),
            seg('+5V', 0, (31.700, -5.100), (31.375, -5.500), 0.6)]

def p5v_v5_adds(J):
    return [seg('+5V', 0, (29.650, -4.000), (30.550, -4.450), 0.2),
            via('+5V', 30.550, -4.450, 0.6),
            seg('+5V', 1, (30.550, -4.450), (31.300, -4.450), 0.6),
            via('+5V', 31.300, -4.450, 0.6),
            seg('+5V', 0, (31.300, -4.450), J, 0.2)]

# ---------- fast margins (t_an1b, verbatim) -------------------------
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

def build_pool(statics, adds):
    it2 = {li: list(statics[li]) for li in range(3)}
    for a in adds:
        if isinstance(a[0], int):
            it2[a[0]].append(a[1])
        else:
            for li in range(3):
                it2[li].append(a)
    return in_box_pool(it2, BOX, pad=1.2), it2

def gate_adds_exact(adds, pool):
    worst = []
    for a in adds:
        if isinstance(a[0], int):
            li, o = a
            if o[0] == 'seg':
                m, w = seg_margin(li, (o[2][0], o[2][1]),
                                  (o[2][2], o[2][3]), o[1], o[2][4],
                                  pool[li])
            else:
                m, w = pt_margin(li, o[2][0], o[2][1], o[1], o[2][2],
                                 pool[li])
            worst.append((m, f'L{li} {o[1]} {o[0]}', w))
        else:
            for li in range(3):
                m, w = pt_margin(li, a[2][0], a[2][1], a[1], a[2][2],
                                 pool[li])
                worst.append((m, f'L{li} {a[1]} via', w))
    worst.sort(key=lambda t: t[0])
    return worst

def gate_adds_fast(adds, pp):
    worst = 9.9
    for a in adds:
        if isinstance(a[0], int):
            li, o = a
            if o[0] == 'seg':
                m, _ = segm_fast(pp[li], (o[2][0], o[2][1]),
                                 (o[2][2], o[2][3]), o[1], o[2][4])
            else:
                m, _ = ptm_fast(pp[li], o[2][0], o[2][1], o[1], o[2][2])
            worst = min(worst, m)
        else:
            for li in range(3):
                m, _ = ptm_fast(pp[li], a[2][0], a[2][1], a[1], a[2][2])
                worst = min(worst, m)
    return worst

# ---------- variants --------------------------------------------------
VARIANTS = []
for J in ((31.35, -4.000), (31.45, -4.000), (31.55, -4.000)):
    VARIANTS.append((f'V5 J{J[0]}', statics_v4,
                     p5v_v5_adds(J) + ne_refan5(J) + se_refan5(J)))
VMAP = {v[0]: v for v in VARIANTS}

# ---------- stage A: SHDN via candidates ------------------------------
stageA = []
for (vname, statics, vadds) in VARIANTS:
    pool, _ = build_pool(statics, vadds)
    wv = gate_adds_exact(vadds, pool)
    if wv[0][0] < -0.001:
        print(f'{vname}: variant adds fail {wv[0][0]:+.3f} '
              f'({wv[0][1]} vs {fmt_it(wv[0][2])})')
        continue
    pp = {li: prep(pool[li]) for li in range(3)}
    cnt = 0
    grids = [(30.50 + gx * 0.025, -3.65 + gy * 0.025)
             for gx in range(25) for gy in range(15)]
    for sd in (0.5, 0.6):
        for (sx, sy) in grids:
            ms = [ptm_fast(pp[li], sx, sy, 'HV_SHDN', sd / 2)[0]
                  for li in range(3)]
            if min(ms) < -0.001:
                continue
            mw, _ = segm_fast(pp[0], (30.375, -3.500), (sx, sy),
                              'HV_SHDN', 0.10)
            if mw < -0.001:
                continue
            stageA.append((min(min(ms), mw), vname, sx, sy, sd))
            cnt += 1
    print(f'{vname}: {cnt} SHDN candidates')
print(f'stage A total: {len(stageA)}')

# ---------- scans ------------------------------------------------------
def dive_scan(pp):
    feas = []
    for gx in range(41):
        x = 30.45 + gx * 0.025
        for gy in range(39):
            y = -3.25 + gy * 0.025
            ms = [ptm_fast(pp[li], x, y, 'HV_INTVCC', 0.25)[0]
                  for li in range(3)]
            if min(ms) < -0.001:
                continue
            ma, _ = segm_fast(pp[0], A0, (x, y), 'HV_INTVCC', 0.10)
            if ma < -0.001:
                continue
            feas.append((min(min(ms), ma), x, y))
    feas.sort(reverse=True)
    return feas

def rise_scan(pp):
    feas = []
    for gx in range(25):
        x = 30.90 + gx * 0.05
        for gy in range(21):
            y = -0.40 + gy * 0.05
            ms = [ptm_fast(pp[li], x, y, 'HV_INTVCC', 0.25)[0]
                  for li in range(3)]
            if min(ms) < -0.001:
                continue
            ma, _ = segm_fast(pp[0], (x, y), R0, 'HV_INTVCC', 0.10)
            if ma < -0.001:
                continue
            feas.append((min(min(ms), ma), x, y))
    feas.sort(reverse=True)
    return feas

# ---------- flood journey ----------------------------------------------
FBOX = (21.5, 38.5, -5.0, 2.8)
GS = 0.0625

def flood_grid(ppL):
    """Free-cell margin grid for a w0.2 HV_INTVCC track centre on one
    layer. Independent of (D,R): the dive/rise vias are same-net and
    never gate the journey, so build once per config+layer."""
    x0, x1, y0, y1 = FBOX
    nx = int((x1 - x0) / GS) + 1
    ny = int((y1 - y0) / GS) + 1
    marg = {}
    for iy in range(ny):
        y = y0 + iy * GS
        for ix in range(nx):
            x = x0 + ix * GS
            m, _ = ptm_fast(ppL, x, y, 'HV_INTVCC', 0.10)
            if m >= -0.001:
                marg[(ix, iy)] = m
    return marg

def flood(marg, ppL, D, R):
    """BFS on a prebuilt flood_grid. Returns (min sampled margin along
    the simplified chain, chain) or (None, reason)."""
    x0, x1, y0, y1 = FBOX
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
    # greedy line-of-sight simplification with sampled seg gates
    chain = [path[0]]
    i = 0
    while i < len(path) - 1:
        j = len(path) - 1
        while j > i + 1:
            m, _ = segm_fast(ppL, path[i], path[j], 'HV_INTVCC', 0.10,
                             step=0.03125)
            if m >= -0.001:
                break
            j -= 1
        chain.append(path[j])
        i = j
    ms = [segm_fast(ppL, a, b, 'HV_INTVCC', 0.10, step=0.03125)[0]
          for a, b in zip(chain, chain[1:])]
    return (min(ms) if ms else 9.9), chain

# ---------- stage B ------------------------------------------------------
results = []
nfail = {'adds': 0, 'dives': 0, 'rises': 0, 'journey': 0}
FLOODS = [0]
GRIDS = [0]
STOP_B = [False]
seen = set()
for (ascore, vname, sx, sy, sd) in stageA:
    if STOP_B[0]:
        break
    key = (vname, round(sx, 2), round(sy, 2), sd)
    if key in seen:
        continue
    seen.add(key)
    _, statics, vadds = VMAP[vname]
    for cx in (32.40, 32.90):
        adds = vadds + shdn_adds(sx, sy, sd, cx)
        pool, it2 = build_pool(statics, adds)
        pp = {li: prep(pool[li]) for li in range(3)}
        if gate_adds_fast(adds, pp) < -0.001:
            nfail['adds'] += 1
            continue
        dives = dive_scan(pp)
        if not dives:
            nfail['dives'] += 1
            continue
        rises = rise_scan(pp)
        if not rises:
            nfail['rises'] += 1
            continue
        grids = {}
        GRIDS[0] += 1
        got = False
        for (dsc, dx_, dy_) in dives[:3]:
            D = (dx_, dy_)
            for (rsc, rx_, ry_) in rises[:2]:
                R = (rx_, ry_)
                for L in (1, 2):
                    if L not in grids:
                        grids[L] = flood_grid(pp[L])
                    FLOODS[0] += 1
                    jm, ch = flood(grids[L], pp[L], D, R)
                    if jm is None:
                        continue
                    results.append((jm, vname, (sx, sy, sd, cx), D, R,
                                    L, ch))
                    got = True
        if not got:
            nfail['journey'] += 1
        else:
            if len(results) >= 10 or GRIDS[0] >= 40:
                print(f'stopping stage B: designs {len(results)}, '
                      f'grid configs {GRIDS[0]}, floods {FLOODS[0]}')
                STOP_B[0] = True
                break
            print(f'  B {vname} SHDN({sx:.2f},{sy:.2f}) d{sd} cx{cx}: '
                  f'dives {len(dives)} best {dives[0][0]:+.3f} '
                  f'@({dives[0][1]:.3f},{dives[0][2]:.3f}), '
                  f'rises {len(rises)}, designs so far {len(results)}')
        if GRIDS[0] >= 40:
            print(f'stopping stage B: grid budget exhausted '
                  f'({GRIDS[0]} configs), designs {len(results)}')
            STOP_B[0] = True
            break
print(f'stage B fail counts: {nfail}')
results.sort(key=lambda t: -t[0])
print(f'\ncomplete fast designs: {len(results)}')
for r in results[:10]:
    print(f'   flood {r[0]:+.3f} {r[1]} SHDN{r[2]} dive{r[3]} rise{r[4]}'
          f' L{r[5]} chain {len(r[6])} pts')

# ---------- exact re-gate -------------------------------------------------
def exact_design_score(vname, shdn, D, R, L, ch):
    _, statics, vadds = VMAP[vname]
    sx, sy, sd, cx = shdn
    adds = vadds + shdn_adds(sx, sy, sd, cx)
    adds.append(via('HV_INTVCC', D[0], D[1], 0.5))
    adds.append(seg('HV_INTVCC', 0, A0, D, 0.2))
    for a_, b_ in zip(ch, ch[1:]):
        if a_ == b_:
            continue
        adds.append(seg('HV_INTVCC', L, a_, b_, 0.2))
    adds.append(via('HV_INTVCC', R[0], R[1], 0.5))
    adds.append(seg('HV_INTVCC', 0, R, R0, 0.2))
    pool, it2 = build_pool(statics, adds)
    return gate_adds_exact(adds, pool), adds

print('\n=== exact re-gate of top designs ===')
final = []
for r in results[:6]:
    wg, adds = exact_design_score(r[1], r[2], r[3], r[4], r[5], r[6])
    print(f'flood {r[0]:+.3f} -> exact min {wg[0][0]:+.3f} '
          f'({wg[0][1]} vs {fmt_it(wg[0][2])})')
    for m, name, w in wg[:4]:
        print(f'     {m:+.3f} {name} vs {fmt_it(w)}')
    final.append((wg[0][0], r, wg))
final.sort(key=lambda t: -t[0])
if final and final[0][0] >= -0.001:
    r = final[0][1]
    design = {'score_exact': final[0][0], 'variant': r[1],
              'shdn': {'x': r[2][0], 'y': r[2][1], 'd': r[2][2],
                       'cx': r[2][3]},
              'dive': r[3], 'rise': r[4], 'journey_layer': r[5],
              'journey': r[6]}
    with open('scratch/work/ao/hv-design.json', 'w') as f:
        json.dump(design, f, indent=1)
    print('\nBEST DESIGN saved to scratch/work/ao/hv-design.json:')
    print(json.dumps(design, indent=1))
else:
    print('\nNO complete design found')
