"""t_ao3: HV dive test under a SPREAD of SHDN placements (exp231).
t_ao2's sort was noise (structural stub tangency -0.000 for every
candidate) and only dive-tested the NE cluster (31.05..31.08,
-3.07..-3.20): dives dead there by -0.116..-0.134 (GATE pad / SHDN
stub). This run dive-tests a greedy max-distance spread of the
>= -0.10 SHDN candidate set per variant, explicitly including the
am config-B points (30.72,-3.55) and (30.60,-3.62) with the
single-diagonal In2 web. Variants V3 and V4 (V2's run geometry is
dominated by V4's)."""
import sys, math, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import load_items, in_box_pool, apply_rip, fmt_it, pair_clr
from router import netclass, dist_to_item

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp231.kicad_pcb')
items = load_items(b)
BOX = (29.0, 34.6, -6.4, 1.5)
A0 = (30.375, -3.0)

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
statics_b, _ = apply_rip(items, RIP_SHDN + RIP_NE + RIP_SE)
statics_v3, _ = apply_rip(statics_b, RIP_RUN2)
statics_v4, _ = apply_rip(statics_b, RIP_RUN2 + RIP_RUN1)

def ne_refan():
    return [seg('+5V', 0, (31.150, -4.000), (31.550, -4.350), 0.6),
            seg('+5V', 0, (31.550, -4.350), (32.000, -3.900), 0.6),
            seg('+5V', 0, (32.000, -3.900), (31.950, -3.350), 0.6),
            seg('+5V', 0, (31.950, -3.350), (31.875, -3.125), 0.6)]

def se_refan(e1, e2):
    return [seg('+5V', 0, (31.150, -4.000), e1, 0.6),
            seg('+5V', 0, e1, e2, 0.6),
            seg('+5V', 0, e2, (31.375, -5.500), 0.6)]

SE0 = ((31.95, -4.20), (31.70, -5.10))

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

def shdn_adds_diag(sx, sy):
    return [via('HV_SHDN', sx, sy, 0.5),
            seg('HV_SHDN', 0, (30.375, -3.500), (sx, sy), 0.2),
            seg('HV_SHDN', 1, (sx, sy), (31.900, -2.875), 0.25),
            seg('HV_SHDN', 1, (31.900, -2.875), (43.375, -2.875), 0.25)]

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
    return in_box_pool(it2, BOX, pad=1.2)

VARIANTS = [
    ('V3', statics_v3, p5v_v3_adds(30.85, -4.30, 31.55)
     + ne_refan() + se_refan(*SE0)),
    ('V4', statics_v4, p5v_v4_adds(-4.60, 31.15)
     + ne_refan() + se_refan(*SE0)),
]
FORCED = [(30.72, -3.55), (30.60, -3.62)]

for (vname, statics, vadds) in VARIANTS:
    pool = build_pool(statics, vadds)
    pp = {li: prep(pool[li]) for li in range(3)}
    cands = []
    for gx in range(37):
        sx = 30.40 + gx * 0.025
        for gy in range(35):
            sy = -3.80 + gy * 0.025
            mv = min(ptm_fast(pp[li], sx, sy, 'HV_SHDN', 0.25)[0]
                     for li in range(3))
            if mv < -0.10:
                continue
            mw, _ = segm_fast(pp[0], (30.375, -3.500), (sx, sy),
                              'HV_SHDN', 0.10)
            if min(mv, mw) >= -0.10:
                cands.append((sx, sy, mv))
    print(f'\n== {vname}: {len(cands)} SHDN candidates in band')
    # greedy spread: forced points first (if in band), then max-min-dist
    picked = []
    for f in FORCED:
        near = [c for c in cands
                if abs(c[0] - f[0]) < 0.03 and abs(c[1] - f[1]) < 0.03]
        if near:
            picked.append(near[0])
            print(f'   forced {f} -> band point {near[0]}')
        else:
            mv = min(ptm_fast(pp[li], f[0], f[1], 'HV_SHDN', 0.25)[0]
                     for li in range(3))
            print(f'   forced {f} NOT in band (via margin {mv:+.3f})')
            picked.append((f[0], f[1], mv))
    while len(picked) < 10 and len(picked) < len(cands):
        best = None
        for c in cands:
            if any(abs(c[0] - p[0]) < 0.01 and abs(c[1] - p[1]) < 0.01
                   for p in picked):
                continue
            d = min(math.hypot(c[0] - p[0], c[1] - p[1]) for p in picked)
            if best is None or d > best[0]:
                best = (d, c)
        if best is None:
            break
        picked.append(best[1])
    for (sx, sy, mv) in picked:
        pool2 = build_pool(statics, vadds + shdn_adds_diag(sx, sy))
        pp2 = {li: prep(pool2[li]) for li in range(3)}
        dives = []
        bestpt = []
        for gx in range(55):
            x = 30.45 + gx * 0.025
            for gy in range(49):
                y = -3.25 + gy * 0.025
                ms = [ptm_fast(pp2[li], x, y, 'HV_INTVCC', 0.25)
                      for li in range(3)]
                mv2 = min(m[0] for m in ms)
                ma, wa = segm_fast(pp2[0], A0, (x, y), 'HV_INTVCC', 0.10)
                tot = min(mv2, ma)
                li_w = min(range(3), key=lambda i: ms[i][0])
                bestpt.append((tot, x, y, mv2, ms[li_w][1], ma, wa))
                if tot >= -0.001:
                    dives.append((tot, x, y))
        dives.sort(reverse=True)
        bestpt.sort(reverse=True)
        print(f'   SHDN ({sx:.3f},{sy:.2f}) via-marg {mv:+.3f}: '
              f'dives {len(dives)}')
        for d in dives[:6]:
            print(f'      dive {d[0]:+.3f} @({d[1]:.3f},{d[2]:.3f})')
        if not dives:
            for bp in bestpt[:3]:
                print(f'      dead {bp[0]:+.3f} @({bp[1]:.3f},{bp[2]:.3f})'
                      f': via {bp[3]:+.3f} vs {fmt_it(bp[4])}; '
                      f'access {bp[5]:+.3f} vs {fmt_it(bp[6])}')
