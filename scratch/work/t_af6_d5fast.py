"""t_af6: fast joint scoring for the D5 re-fanout.

Same model/options as t_af4 (incl. the eastern D6 approaches),
but pairwise margins between two nets' option item-sets are
cached (they do not depend on the third net), so all
|D4| x |D6| x |D5| combos score in seconds. Prints the top
near-misses with the binding pair, and any fully feasible
solution verbatim.
"""
import math, sys
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
    by_layer = {0: list(f), 1: [via] + list(i), 2: [via]}
    return by_layer

def pair_score(A, B):
    """Worst margin between two nets' layered item sets + binder."""
    worst, bind = 9.9, ''
    for li in range(3):
        for a in A[li]:
            for b in B[li]:
                m = item_pair_margin(li, a, b)
                if m < worst:
                    worst, bind = m, f'L{li} {describe(a)} vs {describe(b)}'
    return worst, bind

sets = {net: [option_items(net, o) for o in opts[net]]
        for net in ('ULPI_D4', 'ULPI_D6', 'ULPI_D5')}
print({n: len(opts[n]) for n in opts})

import itertools
p46 = {}
for i, j in itertools.product(range(len(sets['ULPI_D4'])),
                              range(len(sets['ULPI_D6']))):
    p46[(i, j)] = pair_score(sets['ULPI_D4'][i], sets['ULPI_D6'][j])
p45 = {}
for i, j in itertools.product(range(len(sets['ULPI_D4'])),
                              range(len(sets['ULPI_D5']))):
    p45[(i, j)] = pair_score(sets['ULPI_D4'][i], sets['ULPI_D5'][j])
p65 = {}
for i, j in itertools.product(range(len(sets['ULPI_D6'])),
                              range(len(sets['ULPI_D5']))):
    p65[(i, j)] = pair_score(sets['ULPI_D6'][i], sets['ULPI_D5'][j])
print('pair caches done')

results = []
for i4, o4 in enumerate(opts['ULPI_D4']):
    for i6, o6 in enumerate(opts['ULPI_D6']):
        s46, b46 = p46[(i4, i6)]
        base = min(o4[0], o6[0], s46)
        if base < -0.6:
            continue
        for i5, o5 in enumerate(opts['ULPI_D5']):
            s45, b45 = p45[(i4, i5)]
            s65, b65 = p65[(i6, i5)]
            worst = min(base, o5[0], s45, s65)
            bind = b46
            if s45 <= worst:
                bind = b45
            if s65 <= worst:
                bind = b65
            if worst == min(o4[0], o6[0], o5[0]):
                bind = 'statics'
            results.append((worst, i4, i6, i5, bind))
results.sort(key=lambda r: -r[0])
print(f'{len(results)} combos within -0.6; top 15:')
for worst, i4, i6, i5, bind in results[:15]:
    o4, o6, o5 = opts['ULPI_D4'][i4], opts['ULPI_D6'][i6], opts['ULPI_D5'][i5]
    print(f'  worst {worst:+.3f} bind: {bind}')
    print(f'      V4={o4[2]} stub4={o4[3]}')
    print(f'      V6={o6[2]} stub6={o6[3]}')
    print(f'      V5={o5[2]} stub5={o5[3]}')
feas = [r for r in results if r[0] >= 0]
print(f'FEASIBLE (pairwise+statics): {len(feas)} -- launch check pending')
for worst, i4, i6, i5, bind in feas[:10]:
    o4, o6, o5 = opts['ULPI_D4'][i4], opts['ULPI_D6'][i6], opts['ULPI_D5'][i5]
    _f4, i_4 = layered(o4[3], 'ULPI_D4', o4[2], ANCH['ULPI_D4'])
    _f6, i_6 = layered(o6[3], 'ULPI_D6', o6[2], ANCH['ULPI_D6'])
    lm, ldir = launch_best(o5[2], {1: i_4 + i_6})
    print(f'  cand worst {worst:+.3f} launch {lm:+.3f} {ldir}')
    print(f'      V4={o4[2]} stub4={o4[3]}')
    print(f'      V6={o6[2]} stub6={o6[3]}')
    print(f'      V5={o5[2]} stub5={o5[3]}')
