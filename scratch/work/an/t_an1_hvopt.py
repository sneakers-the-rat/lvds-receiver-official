"""t_an1: HV pocket JOINT optimizer (exp231 frontier).

Variables: SHDN via (x,y,d) + web shape (In2 rejoin offset a),
+5V run variant (V0 keep / V1 dive-to-In2 at (dx,in2y), rise (rx,in2y),
w0.2 stubs to both staircase bases, SE seg1 re-added verbatim),
INTVCC dive (x,y), journey layer+path, rise (x,y).
Gates: exact item model (t_ai_lib). Fast margins (bounding-circle
prefilter, provably identical minima) for search; finalists re-gated
with the library's own pt_margin/seg_margin at step 0.01.
HV_INTVCC gated at its real class 0.20 (not in HV_NETS)."""
import sys, math, json, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, pt_margin, seg_margin, in_box_pool,
                      apply_rip, fmt_it, pair_clr)
from router import netclass, dist_to_item

b = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1
                     else 'hw/pdlvds_rx.exp231.kicad_pcb')
items = load_items(b)
BOX = (29.0, 34.6, -5.8, 1.5)

A0 = (30.375, -3.0)      # INTVCC pad east-edge point
R0 = (30.775, -0.5)      # C31.1 west-edge point

def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))
def via(net, x, y, d):
    return ('via', net, (x, y, d / 2), netclass(net)[1])

RIP_SHDN = [('via', 'HV_SHDN', 30.875, -2.875),
            ('seg', 'HV_SHDN', 30.400, -3.500),
            ('seg', 'HV_SHDN', 30.625, -3.375),
            ('seg', 'HV_SHDN', 30.875, -3.125),
            ('seg', 'HV_SHDN', 30.875, -2.875)]
RIP_P5V = [('seg', '+5V', 30.400, -4.000), ('seg', '+5V', 31.150, -4.000)]

statics_shdn, n_shdn = apply_rip(items, RIP_SHDN)
statics_v1, n_v1 = apply_rip(statics_shdn, RIP_P5V)
print(f'rips: SHDN {n_shdn} entries, +5V {n_v1} entries (V1)')

# ---------- fast margins (identical minima; prefilter is a bound) --
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
    m = 9.9
    worst = None
    for it, c, reach in pp:
        if it[1] == net:
            continue
        cd = math.hypot(x - c[0], y - c[1])
        if cd - reach - rad - pair_clr(net, it[1]) >= m:
            continue
        d = dist_to_item(it, x, y) - rad - pair_clr(net, it[1])
        if d < m:
            m, worst = d, it
    return m, worst

def segm_fast(pp, a, b, net, hw, step=0.05):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
    m = 9.9
    worst = None
    for k in range(n + 1):
        mm_, w_ = ptm_fast(pp, a[0] + (b[0] - a[0]) * k / n,
                           a[1] + (b[1] - a[1]) * k / n, net, hw)
        if mm_ < m:
            m, worst = mm_, w_
    return m, worst

# sanity: fast == library on random probes
_pool0 = in_box_pool(statics_shdn, BOX, pad=1.2)
import random
random.seed(7)
for _ in range(300):
    x = random.uniform(29.5, 34.0); y = random.uniform(-5.2, 1.2)
    li = random.randrange(3)
    f = ptm_fast(prep(_pool0[li]), x, y, 'HV_INTVCC', 0.25)[0]
    e = pt_margin(li, x, y, 'HV_INTVCC', 0.25, _pool0[li])[0]
    assert abs(f - e) < 1e-9, (x, y, li, f, e)
print('fast-margin sanity: 300 probes identical to library')

# ---------- config builders ----------------------------------------
def shdn_adds(sx, sy, sd, a):
    adds = [via('HV_SHDN', sx, sy, sd),
            seg('HV_SHDN', 0, (30.375, -3.500), (sx, sy), 0.2)]
    hx = sx + a
    if a > 0:
        adds.append(seg('HV_SHDN', 1, (sx, sy), (hx, sy), 0.25))
    adds.append(seg('HV_SHDN', 1, (hx, sy), (hx + 0.75, -2.875), 0.25))
    adds.append(seg('HV_SHDN', 1, (hx + 0.75, -2.875),
                    (43.375, -2.875), 0.25))
    return adds

def p5v_adds(dx, in2y, rx):
    return [seg('+5V', 0, (29.650, -4.000), (dx, in2y), 0.2),
            via('+5V', dx, in2y, 0.6),
            seg('+5V', 1, (dx, in2y), (rx, in2y), 0.6),
            via('+5V', rx, in2y, 0.6),
            seg('+5V', 0, (rx, in2y), (31.150, -4.000), 0.2),
            seg('+5V', 0, (31.150, -4.000), (31.625, -4.375), 0.6),
            seg('+5V', 0, (rx, in2y), (31.125, -3.875), 0.2)]

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
    """library-exact gate of every add vs pool (pool includes adds)."""
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

# ---------- stage A: SHDN via filter per +5V variant ----------------
VARIANTS = [('V0', None, None)]
for dx in (30.60, 30.80):
    for in2y in (-4.00, -4.30):
        for rx in (31.35, 31.60):
            VARIANTS.append((f'V1 dx{dx} y{in2y} rx{rx}', dx, in2y, rx))

stageA = []   # (score, vname, sx, sy, sd)
for var in VARIANTS:
    vname = var[0]
    if vname == 'V0':
        statics, vadds = statics_shdn, []
    else:
        _, dx, in2y, rx = var
        statics, vadds = statics_v1, p5v_adds(dx, in2y, rx)
    pool, _ = build_pool(statics, vadds)
    pp = {li: prep(pool[li]) for li in range(3)}
    # variant adds must gate vs statics+shdn-ripped pool on their own
    if vadds:
        wv = gate_adds_exact(vadds, pool)
        if wv[0][0] < -0.001:
            print(f'{vname}: variant adds fail vs statics '
                  f'{wv[0][0]:+.3f} ({wv[0][1]} vs {fmt_it(wv[0][2])})')
            continue
    cnt = 0
    for sd in (0.5, 0.6):
        for gx in range(27):
            sx = 30.35 + gx * 0.05
            for gy in range(20):
                sy = -3.85 + gy * 0.05
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
    print(f'{vname}: {cnt} SHDN via+web candidates pass stage A')
stageA.sort(reverse=True)
print(f'stage A total survivors: {len(stageA)}')
for s in stageA[:15]:
    print(f'   A {s[0]:+.3f} {s[1]} SHDN via ({s[2]:.2f},{s[3]:.2f}) '
          f'd{s[4]}')

# ---------- stage B: full configs -----------------------------------
def dive_scan(pp):
    feas = []
    for gx in range(33):
        x = 30.50 + gx * 0.025
        for gy in range(33):
            y = -3.20 + gy * 0.025
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
    for gx in range(27):
        x = 30.20 + gx * 0.05
        for gy in range(44):
            y = -1.90 + gy * 0.05
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

def journey(ppL, D, R, extra_pp):
    """chains on one layer; extra_pp = prepped dive+rise via items."""
    pool = ppL + extra_pp
    best = (None, -9.9)
    xcs = sorted({R[0]} | {31.7 + 0.1 * i for i in range(20)})
    chains = []
    for xc in xcs:
        chains.append([D, (xc, D[1]), (xc, R[1]), R])
        for ye in (D[1] - 0.25, D[1] - 0.50, -3.35):
            if ye < D[1] - 0.05:
                chains.append([D, (D[0], ye), (xc, ye), (xc, R[1]), R])
    for ch in chains:
        m = 9.9
        for a_, b_ in zip(ch, ch[1:]):
            if abs(a_[0] - b_[0]) < 1e-9 and abs(a_[1] - b_[1]) < 1e-9:
                continue
            mm_, _ = segm_fast(pool, a_, b_, 'HV_INTVCC', 0.10)
            m = min(m, mm_)
        if m > best[1]:
            best = (ch, m)
    return best

results = []
seen = set()
cands = []
for s in stageA:
    key = (s[1], round(s[2], 2), round(s[3], 2), s[4])
    if key in seen:
        continue
    seen.add(key)
    cands.append(s)
    if len(cands) >= 40:
        break
print(f'stage B configs: {len(cands)}')
for (ascore, vname, sx, sy, sd) in cands:
    if vname == 'V0':
        statics, vadds = statics_shdn, []
    else:
        parts = vname.split()
        dx = float(parts[1][2:]); in2y = float(parts[2][1:])
        rx = float(parts[3][2:])
        statics, vadds = statics_v1, p5v_adds(dx, in2y, rx)
    for a in (0.0, 0.45, 0.90):
        adds = vadds + shdn_adds(sx, sy, sd, a)
        pool, it2 = build_pool(statics, adds)
        wg = gate_adds_exact(adds, pool)
        if wg[0][0] < -0.001:
            continue
        pp = {li: prep(pool[li]) for li in range(3)}
        dives = dive_scan(pp)
        if not dives:
            continue
        rises = rise_scan(pp)
        if not rises:
            continue
        for (dsc, dx_, dy_) in dives[:3]:
            D = (dx_, dy_)
            dive_item = [('via', 'HV_INTVCC', (dx_, dy_, 0.25), 0.2)]
            for (rsc, rx_, ry_) in rises[:3]:
                R = (rx_, ry_)
                rise_item = [('via', 'HV_INTVCC', (rx_, ry_, 0.25), 0.2)]
                for L in (2, 1):
                    extra = prep(dive_item + rise_item)
                    ch, jm = journey(pp[L], D, R, extra)
                    if ch is None or jm < -0.001:
                        continue
                    fscore = min(wg[0][0], dsc, rsc, jm)
                    results.append((fscore, vname, (sx, sy, sd, a),
                                    D, R, L, ch, jm))
        # one line per (config,a) with its best dive
        print(f'  B {vname} SHDN({sx:.2f},{sy:.2f}) d{sd} a{a}: '
              f'adds {wg[0][0]:+.3f}, dives {len(dives)} '
              f'best {dives[0][0]:+.3f} @({dives[0][1]:.3f},'
              f'{dives[0][2]:.3f}), rises {len(rises)}')
results.sort(key=lambda t: -t[0])
print(f'\ncomplete fast designs: {len(results)}')
for r in results[:10]:
    print(f'   score {r[0]:+.3f} {r[1]} SHDN{r[2]} dive{r[3]} '
          f'rise{r[4]} L{r[5]} journey-margin {r[7]:+.3f}')

# ---------- finalists: exact re-gate of the complete design ---------
def exact_design_score(var, shdn, D, R, L, ch):
    vname = var
    if vname == 'V0':
        statics, vadds = statics_shdn, []
    else:
        parts = vname.split()
        dx = float(parts[1][2:]); in2y = float(parts[2][1:])
        rx = float(parts[3][2:])
        statics, vadds = statics_v1, p5v_adds(dx, in2y, rx)
    sx, sy, sd, a = shdn
    adds = vadds + shdn_adds(sx, sy, sd, a)
    adds.append(via('HV_INTVCC', D[0], D[1], 0.5))
    adds.append(seg('HV_INTVCC', 0, A0, D, 0.2))
    for a_, b_ in zip(ch, ch[1:]):
        if abs(a_[0] - b_[0]) < 1e-9 and abs(a_[1] - b_[1]) < 1e-9:
            continue
        adds.append(seg('HV_INTVCC', L, a_, b_, 0.2))
    adds.append(via('HV_INTVCC', R[0], R[1], 0.5))
    adds.append(seg('HV_INTVCC', 0, R, R0, 0.2))
    pool, it2 = build_pool(statics, adds)
    wg = gate_adds_exact(adds, pool)
    return wg, adds

print('\n=== exact re-gate of top designs ===')
final = []
for r in results[:5]:
    wg, adds = exact_design_score(r[1], r[2], r[3], r[4], r[5], r[6])
    print(f'fast {r[0]:+.3f} -> exact min {wg[0][0]:+.3f} '
          f'({wg[0][1]} vs {fmt_it(wg[0][2])})')
    for m, name, w in wg[:4]:
        print(f'     {m:+.3f} {name} vs {fmt_it(w)}')
    final.append((wg[0][0], r, wg))
final.sort(key=lambda t: -t[0])
if final:
    best = final[0]
    r = best[1]
    design = {'score_exact': best[0], 'variant': r[1],
              'shdn': {'x': r[2][0], 'y': r[2][1], 'd': r[2][2],
                       'a': r[2][3]},
              'dive': r[3], 'rise': r[4], 'journey_layer': r[5],
              'journey': r[6]}
    with open('scratch/work/an/hv-design.json', 'w') as f:
        json.dump(design, f, indent=1)
    print('\nBEST DESIGN saved to scratch/work/an/hv-design.json:')
    print(json.dumps(design, indent=1))
else:
    print('\nNO complete design found')
