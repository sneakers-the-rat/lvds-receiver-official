"""t_af5: near-miss ranking for the D5 joint re-fanout.

Reuses t_af4's model/options, but instead of requiring every
margin >= 0, it scores EVERY combination of static-passing
options by its worst pairwise margin and prints the top
near-misses WITH the binding pair named (which two items, which
nets, which layer). Purpose: identify the single constraint
family that binds, so shape variants can be aimed at it.
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
launch_best = g['launch_best']; static_box = g['static_box']
pt_margin = g['pt_margin']

def describe(it):
    k, net, d = it[0], it[1], it[2]
    if k == 'via':
        return f'via[{net}]@({d[0]:.3f},{d[1]:.3f})r{d[2]}'
    if k == 'seg':
        return f'seg[{net}]({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f})'
    return f'{k}[{net}]'

results = []
for w4, vm4, V4, sp4, cm4 in opts['ULPI_D4']:
    f4, i4 = layered(sp4, 'ULPI_D4', V4, ANCH['ULPI_D4'])
    via4 = ('via', 'ULPI_D4', (V4[0], V4[1], RAD['ULPI_D4']), 0.2)
    for w6, vm6, V6, sp6, cm6 in opts['ULPI_D6']:
        f6, i6 = layered(sp6, 'ULPI_D6', V6, ANCH['ULPI_D6'])
        via6 = ('via', 'ULPI_D6', (V6[0], V6[1], RAD['ULPI_D6']), 0.2)
        for w5, vm5, V5, sp5, _ in opts['ULPI_D5']:
            f5, i5 = layered(sp5, 'ULPI_D5', V5, None)
            via5 = ('via', 'ULPI_D5', (V5[0], V5[1], RAD['ULPI_D5']), 0.2)
            by_layer = {0: f4 + f6 + f5,
                        1: [via4, via6, via5] + i4 + i6,
                        2: [via4, via6, via5]}
            worst = min(w4, w6, w5)
            bind = 'statics'
            for li in range(3):
                pool = by_layer[li]
                for i in range(len(pool)):
                    for j in range(i + 1, len(pool)):
                        if pool[i][1] == pool[j][1]:
                            continue
                        m = item_pair_margin(li, pool[i], pool[j])
                        if m < worst:
                            worst = m
                            bind = (f'L{li} ' + describe(pool[i])
                                    + ' vs ' + describe(pool[j]))
            if worst > -0.5:
                lm, ldir = launch_best(V5, {1: i4 + i6})
                if lm < worst:
                    worst = lm
                    bind = f'D5 launch {ldir}'
            results.append((worst, V4, sp4, V6, sp6, V5, sp5, bind))
results.sort(key=lambda r: -r[0])
print(f'{len(results)} combos scored; top 15 near-misses:')
for r in results[:15]:
    print(f'  worst {r[0]:+.3f}  bind: {r[7]}')
    print(f'      V4={r[1]} stub4_tail={r[2][-2:]}')
    print(f'      V6={r[3]} stub6_tail={r[4][-2:]}')
    print(f'      V5={r[5]} stub5={r[6]}')
