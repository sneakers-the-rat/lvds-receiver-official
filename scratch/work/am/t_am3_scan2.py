"""HV pocket scan B2: SHDN via (30.6,-3.62) d0.5; +5V joint moved east
to (31.45,-4) with SE+NE staircases re-fanned. Gates all adds, scans
INTVCC dives (U10 side) and rises (C31.1 side)."""
import sys, math, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool, apply_rip, fmt_it
from router import netclass

b = pcbnew.LoadBoard(sys.argv[1])
items = load_items(b)
BOX = (29.5, 34.0, -5.2, 1.2)

def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2), netclass(net)[1]))
def via(net, x, y, d):
    return (('via', net, (x, y, d / 2), netclass(net)[1]))

RIPS = [('via', 'HV_SHDN', 30.875, -2.875),
        ('seg', 'HV_SHDN', 30.400, -3.500), ('seg', 'HV_SHDN', 30.625, -3.375),
        ('seg', 'HV_SHDN', 30.875, -3.125), ('seg', 'HV_SHDN', 30.875, -2.875),
        ('seg', '+5V', 30.400, -4.000), ('seg', '+5V', 31.150, -4.000),
        ('seg', '+5V', 31.125, -3.875), ('seg', '+5V', 31.375, -3.625),
        ('seg', '+5V', 31.625, -3.375)]
ADDS = [seg('+5V', 0, (29.650, -4.000), (31.450, -4.000), 0.2),
        seg('+5V', 0, (31.450, -4.000), (31.900, -4.500), 0.6),
        seg('+5V', 0, (31.900, -4.500), (32.125, -4.875), 0.6),
        seg('+5V', 0, (31.450, -4.000), (31.800, -4.320), 0.6),
        seg('+5V', 0, (31.800, -4.320), (32.050, -3.850), 0.6),
        seg('+5V', 0, (32.050, -3.850), (31.950, -3.300), 0.6),
        seg('+5V', 0, (31.950, -3.300), (31.875, -3.125), 0.6),
        via('HV_SHDN', 30.60, -3.62, 0.5),
        seg('HV_SHDN', 0, (30.400, -3.500), (30.600, -3.620), 0.2),
        seg('HV_SHDN', 1, (30.600, -3.620), (31.900, -2.875), 0.25),
        seg('HV_SHDN', 1, (31.900, -2.875), (43.375, -2.875), 0.25)]

it2, n = apply_rip(items, RIPS)
for a in ADDS:
    if isinstance(a[0], int):
        it2[a[0]].append(a[1])
    else:
        for li in range(3):
            it2[li].append(a)
pool = in_box_pool(it2, BOX, pad=1.2)
print(f'ripped {n}')
allok = True
for a in ADDS:
    if isinstance(a[0], int):
        li, o = a
        if o[0] == 'seg':
            m, w = seg_margin(li, (o[2][0], o[2][1]), (o[2][2], o[2][3]), o[1], o[2][4], pool[li])
        print(f'  L{li} {o[1]} seg ({o[2][0]:.2f},{o[2][1]:.2f})->({o[2][2]:.2f},{o[2][3]:.2f}) margin {m:+.3f} worst {fmt_it(w)}')
        allok = allok and m >= -0.001
    else:
        for li in range(3):
            m, w = pt_margin(li, a[2][0], a[2][1], a[1], a[2][2], pool[li])
            print(f'  L{li} {a[1]} via ({a[2][0]},{a[2][1]}) margin {m:+.3f} worst {fmt_it(w)}')
            allok = allok and m >= -0.001
print('ADDS ALL GATE CLEAN:', allok)

feas = []
for gx in range(0, 69):
    for gy in range(0, 77):
        x = 30.45 + gx * 0.05
        y = -3.75 + gy * 0.05
        ms = [pt_margin(li, x, y, 'HV_INTVCC', 0.25, pool[li])[0] for li in range(3)]
        if min(ms) < 0:
            continue
        ma, _ = seg_margin(0, (30.375, -3.0), (x, y), 'HV_INTVCC', 0.10, pool[0])
        if ma < 0:
            continue
        feas.append((min(ms), x, y, ms, ma))
feas.sort(reverse=True)
print(f'DIVES feasible: {len(feas)}')
for f in feas[:12]:
    print(f'  ({f[1]:.2f},{f[2]:.2f}) min {f[0]:+.3f} layers {[round(v, 3) for v in f[3]]} access {f[4]:+.3f}')

rises = []
for gx in range(0, 27):
    for gy in range(0, 43):
        x = 30.20 + gx * 0.05
        y = -1.90 + gy * 0.05
        ms = [pt_margin(li, x, y, 'HV_INTVCC', 0.25, pool[li])[0] for li in range(3)]
        if min(ms) < 0:
            continue
        ma, _ = seg_margin(0, (x, y), (30.775, -0.5), 'HV_INTVCC', 0.10, pool[0])
        if ma < 0:
            continue
        rises.append((min(ms), x, y, ms, ma))
rises.sort(reverse=True)
print(f'RISES feasible (via ok + straight F seg to C31.1 west edge): {len(rises)}')
for f in rises[:12]:
    print(f'  ({f[1]:.2f},{f[2]:.2f}) min {f[0]:+.3f} layers {[round(v, 3) for v in f[3]]} access {f[4]:+.3f}')
