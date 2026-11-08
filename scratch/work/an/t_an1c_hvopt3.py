"""t_an1c: HV pocket joint optimizer v3 (exp231).
Fixes vs t_an1b: (1) SHDN In2 rejoin = EAST-RUN shape: horizontal at
the via latitude to cx, climb (cx,sy)->(cx+0.75,-2.875), east to the
kept run end -- B's single diagonal shaved the dive cluster to
+0.005; the east-run keeps In2 copper at sy (<= -3.475) while the
dive sits at y>=-2.95, and the climb sits east of the B journey.
(2) Stage B iterates ALL stage-A survivors (t_an1b's top-40 cutoff
starved it: every survivor scores the structural 0.000 tangency of
the SHDN pad root vs the +5V pad corner, so ranking is noise).
Variants: V2 = keep run seg2 + NE/SE re-fans; V3 = +5V run dives.
Fast margins for search; library-exact re-gate for finalists.
HV_INTVCC gated at its real class 0.20."""
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

statics_b, n_b = apply_rip(items, RIP_SHDN + RIP_NE + RIP_SE)
statics_v3, n_v3 = apply_rip(statics_b, RIP_RUN2)
print(f'rips: base {n_b} entries, V3 extra {n_v3}')

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
    """cx = east-run climb x; cx=None -> config-B single diagonal."""
    adds = [via('HV_SHDN', sx, sy, sd),
            seg('HV_SHDN', 0, (30.375, -3.500), (sx, sy), 0.2)]
    if cx is None:
        adds.append(seg('HV_SHDN', 1, (sx, sy), (31.900, -2.875), 0.25))
    else:
        adds.append(seg('HV_SHDN', 1, (sx, sy), (cx, sy), 0.25))
        adds.append(seg('HV_SHDN', 1, (cx, sy), (cx + 0.75, -2.875),
                        0.25))
        cx = cx + 0.75
    adds.append(seg('HV_SHDN', 1, (cx if cx else 31.900, -2.875),
                    (43.375, -2.875), 0.25))
    return adds

def p5v_v3_adds(dx, in2y, rx):
    return [seg('+5V', 0, (29.650, -4.000), (dx, in2y), 0.2),
            via('+5V', dx, in2y, 0.6),
            seg('+5V', 1, (dx, in2y), (rx, in2y), 0.6),
            via('+5V', rx, in2y, 0.6),
            seg('+5V', 0, (rx, in2y), (31.150, -4.000), 0.2),
            seg('+5V', 0, (rx, in2y), (31.125, -3.875), 0.2)]

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

SE_OPTS = [((31.95, -4.20), (31.70, -5.10)),
           ((32.10, -4.35), (31.80, -5.05)),
           ((31.80, -4.10), (31.60, -5.15))]
VARIANTS = []
for i, (e1, e2) in enumerate(SE_OPTS):
    VARIANTS.append((f'V2 se{i}', statics_b,
                     ne_refan() + se_refan(e1, e2)))
for dx in (30.85, 31.05):
    for i, (e1, e2) in enumerate(SE_OPTS[:2]):
        VARIANTS.append((f'V3 dx{dx} y-4.3 rx31.55 se{i}', statics_v3,
                         p5v_v3_adds(dx, -4.30, 31.55)
                         + ne_refan() + se_refan(e1, e2)))
VMAP = {v[0]: v for v in VARIANTS}

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
    for sd in (0.5, 0.6):
        for gx in range(32):
            sx = 30.35 + gx * 0.05
            for gy in range(25):
                sy = -4.10 + gy * 0.05
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
    pool = ppL + extra_pp
    best = (None, -9.9)
    xcs = sorted({R[0]} | {31.7 + 0.1 * i for i in range(18)})
    chains = []
    for xc in xcs:
        chains.append([D, (xc, D[1]), (xc, R[1]), R])
        for ye in (D[1] - 0.25, D[1] - 0.50, -3.35):
            if ye < D[1] - 0.05:
                chains.append([D, (D[0], ye), (xc, ye), (xc, R[1]), R])
    for ch in chains:
        m = 9.9
        for a_, b_ in zip(ch, ch[1:]):
            if a_ == b_:
                continue
            mm_, _ = segm_fast(pool, a_, b_, 'HV_INTVCC', 0.10)
            m = min(m, mm_)
        if m > best[1]:
            best = (ch, m)
    return best

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

results = []
nfail = {'adds': 0, 'dives': 0, 'rises': 0, 'journey': 0}
for (ascore, vname, sx, sy, sd) in stageA:
    _, statics, vadds = VMAP[vname]
    for cx in (32.90, 33.60, None):
        adds = vadds + shdn_adds(sx, sy, sd, cx)
        pool, it2 = build_pool(statics, adds)
        pp = {li: prep(pool[li]) for li in range(3)}
        wgfast = gate_adds_fast(adds, pp)
        if wgfast < -0.001:
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
        got = False
        for (dsc, dx_, dy_) in dives[:3]:
            D = (dx_, dy_)
            for (rsc, rx_, ry_) in rises[:3]:
                R = (rx_, ry_)
                extra = prep([('via', 'HV_INTVCC', (dx_, dy_, 0.25),
                               0.2),
                              ('via', 'HV_INTVCC', (rx_, ry_, 0.25),
                               0.2)])
                for L in (2, 1):
                    ch, jm = journey(pp[L], D, R, extra)
                    if ch is None or jm < -0.001:
                        continue
                    got = True
                    results.append((min(wgfast, dsc, rsc, jm),
                                    vname, (sx, sy, sd, cx), D, R, L,
                                    ch, jm))
        if not got:
            nfail['journey'] += 1
        else:
            print(f'  B {vname} SHDN({sx:.2f},{sy:.2f}) d{sd} cx{cx}: '
                  f'adds {wgfast:+.3f}, dives {len(dives)} best '
                  f'{dives[0][0]:+.3f} @({dives[0][1]:.3f},'
                  f'{dives[0][2]:.3f}), rises {len(rises)}')
print(f'stage B failure counts: {nfail}')
results.sort(key=lambda t: -t[0])
print(f'\ncomplete fast designs: {len(results)}')
for r in results[:10]:
    print(f'   score {r[0]:+.3f} {r[1]} SHDN{r[2]} dive{r[3]} rise{r[4]}'
          f' L{r[5]} journey {r[7]:+.3f}')

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
for r in results[:5]:
    wg, adds = exact_design_score(r[1], r[2], r[3], r[4], r[5], r[6])
    print(f'fast {r[0]:+.3f} -> exact min {wg[0][0]:+.3f} '
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
    with open('scratch/work/an/hv-design.json', 'w') as f:
        json.dump(design, f, indent=1)
    print('\nBEST DESIGN saved:')
    print(json.dumps(design, indent=1))
else:
    print('\nNO complete design found')
