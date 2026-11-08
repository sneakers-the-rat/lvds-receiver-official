"""t_ao2: HV pocket wall diagnostic (exp231).
t_ao1 result: all 660 stage-B configs died at the DIVE stage.
Question: which fences kill (a) SW SHDN via placements (the am
config-B geometry, via ~(30.6..0.72,-3.55..-3.62) + single-diagonal
In2 web, under which the only known dives live), and (b) the dives
themselves under those placements. Builders copied from t_ao1
(t_an1c lineage); gates are the library fast margins, with killers
named. DIVE box widened: x[30.45,31.80] y[-3.25,-2.05]."""
import sys, math, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, in_box_pool, apply_rip, fmt_it,
                      pair_clr)
from router import netclass, dist_to_item

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp231.kicad_pcb')
items = load_items(b)
BOX = (29.0, 34.6, -6.4, 1.5)
A0 = (30.375, -3.0)
print('pair_clr SHDN/+5V:', pair_clr('HV_SHDN', '+5V'),
      ' SHDN/INTVCC:', pair_clr('HV_SHDN', 'HV_INTVCC'),
      ' INTVCC/+5V:', pair_clr('HV_INTVCC', '+5V'),
      ' INTVCC/FBX:', pair_clr('HV_INTVCC', 'HV_FBX'),
      ' INTVCC/GATE:', pair_clr('HV_INTVCC', 'HV_GATE'))

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
    """Single-diagonal web (am config-B shape)."""
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
    ('V2', statics_b, ne_refan() + se_refan(*SE0)),
    ('V3', statics_v3, p5v_v3_adds(30.85, -4.30, 31.55)
     + ne_refan() + se_refan(*SE0)),
    ('V4', statics_v4, p5v_v4_adds(-4.60, 31.15)
     + ne_refan() + se_refan(*SE0)),
]

for (vname, statics, vadds) in VARIANTS:
    pool = build_pool(statics, vadds)
    pp = {li: prep(pool[li]) for li in range(3)}
    cands = []
    for gx in range(37):
        sx = 30.40 + gx * 0.025
        for gy in range(35):
            sy = -3.80 + gy * 0.025
            ms = [ptm_fast(pp[li], sx, sy, 'HV_SHDN', 0.25)
                  for li in range(3)]
            mv = min(m[0] for m in ms)
            if mv < -0.10:
                continue
            mw, ww = segm_fast(pp[0], (30.375, -3.500), (sx, sy),
                               'HV_SHDN', 0.10)
            tot = min(mv, mw)
            if tot >= -0.10:
                li_w = min(range(3), key=lambda i: ms[i][0])
                cands.append((tot, sx, sy, mv, ms[li_w][1], mw, ww))
    cands.sort(reverse=True)
    print(f'\n== {vname}: {len(cands)} SHDN points with margin >= -0.10')
    for c in cands[:8]:
        print(f'   {c[0]:+.3f} via ({c[1]:.3f},{c[2]:.2f}) via-marg '
              f'{c[3]:+.3f} vs {fmt_it(c[4])}; stub {c[5]:+.3f} '
              f'vs {fmt_it(c[6])}')
    # dive scan under the best few SHDN placements (diagonal web)
    tested = 0
    for c in cands:
        if c[0] < -0.001 or tested >= 4:
            break
        tested += 1
        sx, sy = c[1], c[2]
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
                mv = min(m[0] for m in ms)
                ma, wa = segm_fast(pp2[0], A0, (x, y), 'HV_INTVCC',
                                   0.10)
                tot = min(mv, ma)
                bestpt.append((tot, x, y, mv, ma, wa,
                               ms[min(range(3),
                                      key=lambda i: ms[i][0])][1]))
                if tot >= -0.001:
                    dives.append((tot, x, y))
        dives.sort(reverse=True)
        bestpt.sort(reverse=True)
        print(f'   SHDN ({sx:.3f},{sy:.2f}): dives {len(dives)}')
        for d in dives[:5]:
            print(f'      dive {d[0]:+.3f} @({d[1]:.3f},{d[2]:.3f})')
        if not dives:
            bp = bestpt[0]
            print(f'      best dead dive {bp[0]:+.3f} @({bp[1]:.3f},'
                  f'{bp[2]:.3f}): via {bp[3]:+.3f} vs '
                  f'{fmt_it(bp[6])}; access {bp[4]:+.3f} vs '
                  f'{fmt_it(bp[5])}')
