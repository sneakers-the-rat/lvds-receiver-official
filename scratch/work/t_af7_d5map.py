"""t_af7: ASCII feasibility maps for D4/D5/D6 via placement.

For each net, at every 0.125 grid point in the district window,
compute the via's static margin (exact item model, D4/D6 rip set
removed) and print a map: '.' infeasible (<0), digits = margin
in 0.05 steps capped at 9, plus the binding item at selected
probe points. Shows the true shape of each net's via region.
"""
import math, sys
sys.path.insert(0, 'hw')

sys.argv = ['t_af4_d5opt2.py', 'hw/pdlvds_rx.exp216.kicad_pcb']
src = open('scratch/work/t_af4_d5opt2.py').read()
head = src.split('# ---- stub shape variants')[0]
g = {'__name__': 'af4model'}
exec(compile(head, 't_af4_head', 'exec'), g)

static_box = g['static_box']; RAD = g['RAD']; pt_margin = g['pt_margin']
dist_to_item = g['dist_to_item']; pair_clr = g['pair_clr']

def bind_at(net, V, r):
    worst, what = 9.9, None
    for li in range(3):
        for it in static_box[li]:
            if it[1] == net:
                continue
            d = dist_to_item(it, V[0], V[1]) - r - pair_clr(net, it[1])
            if d < worst:
                worst, what = d, (li, it)
    return worst, what

def describe(it):
    k, net, d = it[0], it[1], it[2]
    if k == 'via':
        return f'via[{net}]@({d[0]:.2f},{d[1]:.2f})r{d[2]}'
    if k == 'seg':
        return f'seg[{net}]({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f})'
    return f'pad[{net}]@({d[0]:.2f},{d[1]:.2f})'

XS = [78.75 + 0.125 * i for i in range(22)]   # 78.75 .. 81.375
YS = [16.125 - 0.125 * i for i in range(20)]  # 16.125 .. 13.75
for net in ('ULPI_D4', 'ULPI_D5', 'ULPI_D6'):
    print(f'\n=== {net} via map (r={RAD[net]}), rows y desc, cols x asc '
          f'from 78.75 step 0.125 ===')
    print('      ' + ''.join(str(int((x % 1) * 8)) if x % 0.5 == 0 else ' '
                            for x in XS))
    for y in YS:
        row = ''
        for x in XS:
            m, _ = bind_at(net, (x, y), RAD[net])
            row += '.' if m < 0 else str(min(9, int(m / 0.05) + 1))
        print(f'{y:6.3f} {row}')
    # binding items at the pocket and at astray probes
    for V in [(80.75, 15.0), (80.875, 15.0), (80.625, 15.25),
              (80.5, 14.75), (79.5, 14.375), (79.375, 14.625),
              (80.375, 15.0), (81.0, 14.75), (80.875, 14.75)]:
        m, what = bind_at(net, V, RAD[net])
        li, it = what if what else (None, None)
        print(f'  probe {V}: margin {m:+.3f} bind L{li} '
              f'{describe(it) if it else None}')
