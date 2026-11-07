"""t_af13: local refinement search around the af12 skeleton.

af12's best full combos (rip-3, D4 via d0.5) sit at worst
-0.063, all binds in a +/-0.07 band:
  V4=(80.0,14.5) d0.5, stub4 short prefix
  V6=(80.75,14.625) d0.6 eastern approach
  V5=(80.125,15.125), stub5 bend (79.0,14.75)
binds: V4-V5 via distance (-0.063), D6 y15.625 row vs V5
(-0.050). This search refines via positions on a 0.0625 grid
around that skeleton, adds a y15.6875 D6 tail row, and runs
the full chain (statics -> F pairwise -> In2 groute) from
t_af9/t_af11. Radii: D4 d0.5, D5 d0.5, D6 d0.6.
"""
import math, sys, heapq
sys.path.insert(0, 'hw')

sys.argv = ['t_af11_d5d4small.py', 'hw/pdlvds_rx.exp216.kicad_pcb']
src = open('scratch/work/t_af11_d5d4small.py').read()
head = src.split('# ---- option build')[0]
g = {'__name__': 'af11model'}
exec(compile(head, 't_af11_head', 'exec'), g)

static_box = g['static_box']; RAD = g['RAD']; PAD = g['PAD']
ANCH = g['ANCH']; TRK_HW = g['TRK_HW']
pt_margin = g['pt_margin']; seg_margin = g['seg_margin']
poly_margin = g['poly_margin']
poly_items = g['poly_items']; item_pair_margin = g['item_pair_margin']
groute_in2 = g['groute_in2']

def fgrid(x0, x1, y0, y1, step=0.0625):
    xs = [x0 + i*step for i in range(int(round((x1-x0)/step)) + 1)]
    ys = [y0 + i*step for i in range(int(round((y1-y0)/step)) + 1)]
    return [(round(x, 4), round(y, 4)) for x in xs for y in ys]

CAND = {'ULPI_D4': fgrid(79.875, 80.4375, 14.3125, 14.625),
        'ULPI_D5': fgrid(79.875, 80.4375, 14.9375, 15.3125),
        'ULPI_D6': [(80.75, 14.625), (80.75, 14.75), (80.875, 14.625),
                    (80.6875, 14.6875), (80.8125, 14.5625)]}
feas = {}
for net, cand in CAND.items():
    feas[net] = []
    for V in cand:
        m = min(pt_margin(li, V[0], V[1], net, RAD[net], static_box[li])
                for li in range(3))
        if m >= 0.0:
            feas[net].append((m, V))
    feas[net].sort(reverse=True)
    print(f'{net}: {len(feas[net])}/{len(cand)} refined vias feasible')

PRE4 = [[(78.4375, 14.25), (78.6875, 14.25), (79.125, 14.375),
         (79.375, 14.625)],
        [(78.4375, 14.25), (78.6875, 14.25), (79.125, 14.375)]]
PRE6A = [(78.4375, 15.25), (78.6875, 15.25), (79.125, 15.375),
         (79.375, 15.625), (79.875, 15.625)]
def stub_variants(net, V):
    if net == 'ULPI_D4':
        return [pre + [V] for pre in PRE4]
    if net == 'ULPI_D6':
        out = []
        for rowy in (15.625, 15.6875):
            for wx in (80.625, 80.75, 80.875, 80.95):
                out.append(PRE6A + [(wx, rowy), V])
            out.append(PRE6A + [V])
        return out
    out = [[PAD[net], V]]
    for B in [(79.0, 14.75), (79.25, 14.75), (79.5, 14.75),
              (79.25, 15.0), (79.5, 15.125)]:
        out.append([PAD[net], B, V])
    out.append([PAD[net], (V[0], 14.75), V] if V[1] != 14.75
               else [PAD[net], V])
    return out

opts = {}
for net in ('ULPI_D4', 'ULPI_D6', 'ULPI_D5'):
    opts[net] = []
    for vm, V in feas[net]:
        for sp in stub_variants(net, V):
            sm = poly_margin(0, sp, net, TRK_HW, static_box[0])
            if sm >= 0:
                opts[net].append((min(vm, sm), vm, V, sp))
    print(f'{net}: {len(opts[net])} options')

def vv(oa, ob, na, nb):
    Va, Vb = oa[2], ob[2]
    return math.hypot(Va[0]-Vb[0], Va[1]-Vb[1]) - (RAD[na]+RAD[nb]+0.2)

sols = []
for o4 in opts['ULPI_D4']:
    V4 = o4[2]
    via4 = ('via', 'ULPI_D4', (V4[0], V4[1], RAD['ULPI_D4']), 0.2)
    for o6 in opts['ULPI_D6']:
        if vv(o4, o6, 'ULPI_D4', 'ULPI_D6') < 0.005:
            continue
        V6 = o6[2]
        via6 = ('via', 'ULPI_D6', (V6[0], V6[1], RAD['ULPI_D6']), 0.2)
        f46 = min([item_pair_margin(0, a, b)
                   for a in poly_items('ULPI_D4', o4[3]) + [via4]
                   for b in poly_items('ULPI_D6', o6[3]) + [via6]])
        if f46 < 0:
            continue
        for o5 in opts['ULPI_D5']:
            if vv(o4, o5, 'ULPI_D4', 'ULPI_D5') < 0.005:
                continue
            if vv(o6, o5, 'ULPI_D6', 'ULPI_D5') < 0.005:
                continue
            V5 = o5[2]
            via5 = ('via', 'ULPI_D5', (V5[0], V5[1], RAD['ULPI_D5']), 0.2)
            f45 = min([item_pair_margin(0, a, b)
                       for a in poly_items('ULPI_D4', o4[3]) + [via4]
                       for b in poly_items('ULPI_D5', o5[3]) + [via5]])
            f65 = min([item_pair_margin(0, a, b)
                       for a in poly_items('ULPI_D6', o6[3]) + [via6]
                       for b in poly_items('ULPI_D5', o5[3]) + [via5]])
            if f45 < 0 or f65 < 0:
                continue
            c4 = groute_in2('ULPI_D4', V4,
                            lambda x, y, A=ANCH['ULPI_D4']:
                            math.hypot(x-A[0], y-A[1]) <= 0.03,
                            [via6, via5])
            if c4 is None:
                continue
            i4 = poly_items('ULPI_D4', c4)
            c6 = groute_in2('ULPI_D6', V6,
                            lambda x, y, A=ANCH['ULPI_D6']:
                            math.hypot(x-A[0], y-A[1]) <= 0.03,
                            [via4, via5] + i4)
            if c6 is None:
                continue
            i6 = poly_items('ULPI_D6', c6)
            c5 = groute_in2('ULPI_D5', V5,
                            lambda x, y: x >= 84.25 or y <= 11.25,
                            [via4, via6] + i4 + i6)
            if c5 is None:
                continue
            worst = min(o4[0], o6[0], o5[0], f46, f45, f65)
            sols.append((worst, o4, o6, o5, c4, c6, c5))
            print(f'FEASIBLE: worst {worst:+.3f} V4={V4} V6={V6} V5={V5}')
            if len(sols) >= 6:
                break
        if len(sols) >= 6:
            break
    if len(sols) >= 6:
        break
print(f'\n{len(sols)} feasible refined solutions')
for s in sols:
    print(f'  worst {s[0]:+.3f}')
    print(f'    V4={s[1][2]} stub4={s[1][3]} conn4={s[4]}')
    print(f'    V6={s[2][2]} stub6={s[2][3]} conn6={s[5]}')
    print(f'    V5={s[3][2]} stub5={s[3][3]} conn5={s[6]}')
