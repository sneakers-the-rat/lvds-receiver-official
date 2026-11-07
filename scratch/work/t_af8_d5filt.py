"""t_af8: best D5 joint combos SUBJECT TO via-via distance >= 0,
ranked by worst remaining margin, with the top-3 binding pairs
printed per combo. Uses t_af6's cached pair scores (recomputed
inline, fast) on t_af4's current option sets.
"""
import math, sys, itertools
sys.path.insert(0, 'hw')

sys.argv = ['t_af4_d5opt2.py', 'hw/pdlvds_rx.exp216.kicad_pcb']
src = open('scratch/work/t_af4_d5opt2.py').read()
head = src.split('sols = []')[0]
g = {'__name__': 'af4model'}
exec(compile(head, 't_af4_head', 'exec'), g)

opts = g['opts']; RAD = g['RAD']; ANCH = g['ANCH']
layered = g['layered']; item_pair_margin = g['item_pair_margin']
launch_best = g['launch_best']

def describe(it):
    k, net, d = it[0], it[1], it[2]
    if k == 'via':
        return f'via[{net}]@({d[0]:.3f},{d[1]:.3f})r{d[2]}'
    return f'seg[{net}]({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f})'

def option_items(net, opt):
    _w, _vm, V, sp, _cm = opt
    f, i = layered(sp, net, V, ANCH[net] if net != 'ULPI_D5' else None)
    via = ('via', net, (V[0], V[1], RAD[net]), 0.2)
    return {0: list(f), 1: [via] + list(i), 2: [via]}

def pair_detail(A, B):
    out = []
    for li in range(3):
        for a in A[li]:
            for b in B[li]:
                out.append((item_pair_margin(li, a, b),
                            f'L{li} {describe(a)} vs {describe(b)}'))
    out.sort()
    return out

sets = {net: [option_items(net, o) for o in opts[net]]
        for net in ('ULPI_D4', 'ULPI_D6', 'ULPI_D5')}
print({n: len(opts[n]) for n in opts})

def vv(oa, ob, na, nb):
    Va, Vb = oa[2], ob[2]
    return math.hypot(Va[0]-Vb[0], Va[1]-Vb[1]) - (RAD[na]+RAD[nb]+0.2)

res = []
for i4, o4 in enumerate(opts['ULPI_D4']):
    for i6, o6 in enumerate(opts['ULPI_D6']):
        if vv(o4, o6, 'ULPI_D4', 'ULPI_D6') < 0.005:
            continue
        d46 = pair_detail(sets['ULPI_D4'][i4], sets['ULPI_D6'][i6])
        w46 = d46[0][0]
        if min(o4[0], o6[0], w46) < -0.45:
            continue
        for i5, o5 in enumerate(opts['ULPI_D5']):
            if vv(o4, o5, 'ULPI_D4', 'ULPI_D5') < 0.005:
                continue
            if vv(o6, o5, 'ULPI_D6', 'ULPI_D5') < 0.005:
                continue
            d45 = pair_detail(sets['ULPI_D4'][i4], sets['ULPI_D5'][i5])
            d65 = pair_detail(sets['ULPI_D6'][i6], sets['ULPI_D5'][i5])
            allw = sorted([(w46, d46[0][1]), (d45[0][0], d45[0][1]),
                           (d65[0][0], d65[0][1]),
                           (o4[0], 'D4 statics'), (o6[0], 'D6 statics'),
                           (o5[0], 'D5 statics')])
            res.append((allw[0][0], i4, i6, i5,
                        [x for x in allw[:3]]))
res.sort(key=lambda r: -r[0])
print(f'{len(res)} combos pass via-via filter; top 10:')
for worst, i4, i6, i5, binds in res[:10]:
    o4, o6, o5 = opts['ULPI_D4'][i4], opts['ULPI_D6'][i6], opts['ULPI_D5'][i5]
    print(f'  worst {worst:+.3f}')
    for m, b in binds:
        print(f'      {m:+.3f}  {b}')
    print(f'      V4={o4[2]} stub4={o4[3]}')
    print(f'      V6={o6[2]} stub6={o6[3]}')
    print(f'      V5={o5[2]} stub5={o5[3]}')
    _f4, i_4 = layered(o4[3], 'ULPI_D4', o4[2], ANCH['ULPI_D4'])
    _f6, i_6 = layered(o6[3], 'ULPI_D6', o6[2], ANCH['ULPI_D6'])
    lm, ldir = launch_best(o5[2], {1: i_4 + i_6})
    print(f'      D5 launch: {lm:+.3f} {ldir}')
