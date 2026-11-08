"""HV pocket: INTVCC dive-point scan under joint configurations.
A = current board (control). B = SHDN via south (30.72,-3.55) d0.5 +
web/In2 re-lay, +5V NE staircase joints moved south.
C = GATE needle+via ripped only (attribution)."""
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

RIP_SHDN = [('via', 'HV_SHDN', 30.875, -2.875),
            ('seg', 'HV_SHDN', 30.400, -3.500), ('seg', 'HV_SHDN', 30.625, -3.375),
            ('seg', 'HV_SHDN', 30.875, -3.125), ('seg', 'HV_SHDN', 30.875, -2.875)]
RIP_P5V = [('seg', '+5V', 30.400, -4.000), ('seg', '+5V', 31.125, -3.875),
           ('seg', '+5V', 31.375, -3.625), ('seg', '+5V', 31.625, -3.375)]
RIP_NEEDLE = [('seg', 'HV_GATE', 30.375, -2.500), ('via', 'HV_GATE', 31.700, -1.500)]

def config(name, rips, adds):
    it2, n = apply_rip(items, rips)
    for (li, obj) in [(a[0], a[1]) for a in adds if isinstance(a[0], int)]:
        it2[li].append(obj)
    for obj in [a for a in adds if not isinstance(a[0], int)]:
        for li in range(3):
            it2[li].append(obj)
    pool = in_box_pool(it2, BOX, pad=1.2)
    # gate the additions themselves
    print(f'--- config {name}: ripped {n}, adds gated:')
    ok = True
    for a in adds:
        if isinstance(a[0], int):
            li, o = a
            if o[0] == 'seg':
                m, w = seg_margin(li, (o[2][0], o[2][1]), (o[2][2], o[2][3]), o[1], o[2][4], pool[li])
            else:
                m, w = pt_margin(li, o[2][0], o[2][1], o[1], o[2][2], pool[li])
            print(f'    L{li} {o[1]} {o[0]} margin {m:+.3f} worst {fmt_it(w)}')
            ok = ok and m >= -0.001
        else:
            for li in range(3):
                m, w = pt_margin(li, a[2][0], a[2][1], a[1], a[2][2], pool[li])
                print(f'    L{li} {a[1]} via ({a[2][0]},{a[2][1]}) margin {m:+.3f} worst {fmt_it(w)}')
                ok = ok and m >= -0.001
    # dive scan
    feas = []
    for gx in range(0, 69):
        for gy in range(0, 77):
            x = 30.45 + gx * 0.05
            y = -3.75 + gy * 0.05
            ms = []
            for li in range(3):
                m, w = pt_margin(li, x, y, 'HV_INTVCC', 0.25, pool[li])
                ms.append(m)
            if min(ms) < 0:
                continue
            ma, _ = seg_margin(0, (30.375, -3.0), (x, y), 'HV_INTVCC', 0.10, pool[0])
            if ma < 0:
                continue
            feas.append((min(ms), x, y, ms, ma))
    feas.sort(reverse=True)
    print(f'  feasible dives (via ok all layers + straight F access): {len(feas)}')
    for f in feas[:14]:
        print(f'    ({f[1]:.2f},{f[2]:.2f}) min {f[0]:+.3f} layers {[round(v,3) for v in f[3]]} access {f[4]:+.3f}')
    return ok, feas

ADD_B = [seg('+5V', 0, (31.150, -4.000), (31.550, -4.350), 0.6),
         seg('+5V', 0, (31.550, -4.350), (32.000, -3.900), 0.6),
         seg('+5V', 0, (32.000, -3.900), (31.950, -3.350), 0.6),
         seg('+5V', 0, (31.950, -3.350), (31.875, -3.125), 0.6),
         via('HV_SHDN', 30.72, -3.55, 0.5),
         seg('HV_SHDN', 0, (30.400, -3.500), (30.720, -3.550), 0.2),
         seg('HV_SHDN', 1, (30.720, -3.550), (31.900, -2.875), 0.25),
         seg('HV_SHDN', 1, (31.900, -2.875), (43.375, -2.875), 0.25)]

config('A current', [], [])
config('B SHDN-south + P5V-south', RIP_SHDN + RIP_P5V, ADD_B)
config('C needle ripped only', RIP_NEEDLE, [])
