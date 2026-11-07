"""t_af12: full-chain near-miss ranking for the rip-3 search
space (t_af11 model: D4 via r0.25). Scores every combination of
static-passing options by worst F-layer pairwise margin using
cached per-net-pair scores; prints the top combos with their
three binding pairs. Grouting is checked only for combos whose
F chain is fully >= 0.
"""
import math, sys, itertools
sys.path.insert(0, 'hw')

sys.argv = ['t_af11_d5d4small.py', 'hw/pdlvds_rx.exp216.kicad_pcb']
src = open('scratch/work/t_af11_d5d4small.py').read()
head = src.split('# ---- option build')[0]
g = {'__name__': 'af11model'}
exec(compile(head, 't_af11_head', 'exec'), g)

# rebuild options exactly as t_af11 does
feas = g['feas']; stub_variants = g['stub_variants']
poly_margin = g['poly_margin']; static_box = g['static_box']
TRK_HW = g['TRK_HW']; RAD = g['RAD']; poly_items = g['poly_items']
item_pair_margin = g['item_pair_margin']
opts = {}
for net in ('ULPI_D4', 'ULPI_D6', 'ULPI_D5'):
    opts[net] = []
    for vm, V in feas[net]:
        for sp in stub_variants(net, V):
            sm = poly_margin(0, sp, net, TRK_HW, static_box[0])
            if sm >= 0:
                opts[net].append((min(vm, sm), vm, V, sp))
    print(f'{net}: {len(opts[net])} options')

def describe(it):
    k, net, d = it[0], it[1], it[2]
    if k == 'via':
        return f'via[{net}]@({d[0]:.3f},{d[1]:.3f})r{d[2]}'
    return f'seg[{net}]({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f})'

def f_items(net, o):
    _w, _vm, V, sp = o
    return poly_items(net, sp) + [('via', net, (V[0], V[1], RAD[net]), 0.2)]

def pair_detail(A, B):
    out = [(item_pair_margin(0, a, b), f'{describe(a)} vs {describe(b)}')
           for a in A for b in B]
    out.sort(key=lambda t: t[0])
    return out

F = {net: [f_items(net, o) for o in opts[net]] for net in opts}
print('scoring D4-D6 pairs...')
p46 = {}
for i, j in itertools.product(range(len(F['ULPI_D4'])),
                              range(len(F['ULPI_D6']))):
    p46[(i, j)] = pair_detail(F['ULPI_D4'][i], F['ULPI_D6'][j])
print('scoring D4-D5 pairs...')
p45 = {}
for i, j in itertools.product(range(len(F['ULPI_D4'])),
                              range(len(F['ULPI_D5']))):
    p45[(i, j)] = pair_detail(F['ULPI_D4'][i], F['ULPI_D5'][j])
print('scoring D6-D5 pairs...')
p65 = {}
for i, j in itertools.product(range(len(F['ULPI_D6'])),
                              range(len(F['ULPI_D5']))):
    p65[(i, j)] = pair_detail(F['ULPI_D6'][i], F['ULPI_D5'][j])

res = []
for i4, o4 in enumerate(opts['ULPI_D4']):
    for i6, o6 in enumerate(opts['ULPI_D6']):
        w46, b46 = p46[(i4, i6)][0]
        base = min(o4[0], o6[0], w46)
        if base < -0.35:
            continue
        for i5, o5 in enumerate(opts['ULPI_D5']):
            w45, b45 = p45[(i4, i5)][0]
            w65, b65 = p65[(i6, i5)][0]
            binds = sorted([(w46, '46 ' + b46), (w45, '45 ' + b45),
                            (w65, '65 ' + b65), (o4[0], 'D4 statics'),
                            (o6[0], 'D6 statics'), (o5[0], 'D5 statics')])
            res.append((binds[0][0], i4, i6, i5, binds[:3]))
res.sort(key=lambda r: -r[0])
print(f'\ntop 12 full combos (F chain):')
for worst, i4, i6, i5, binds in res[:12]:
    o4, o6, o5 = opts['ULPI_D4'][i4], opts['ULPI_D6'][i6], opts['ULPI_D5'][i5]
    print(f'  worst {worst:+.3f}')
    for m, b in binds:
        print(f'      {m:+.3f}  {b}')
    print(f'      V4={o4[2]} stub4={o4[3]}')
    print(f'      V6={o6[2]} stub6={o6[3]}')
    print(f'      V5={o5[2]} stub5={o5[3]}')
print(f'combos with F chain >= 0: {sum(1 for r in res if r[0] >= 0)}')
