import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')

def gate(its, net, pool, label):
    worst = (9.9, None, None)
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < worst[0]:
                    worst = (m, it, o)
    print(f'{label} gate worst {worst[0]:+.3f} {L.fmt_it(worst[1])} vs '
          f'{L.fmt_it(worst[2])}', flush=True)
    return worst[0]

# XI web items touching the staircase via (75.625,18.625)
print('== XI items touching (75.625,18.625):', flush=True)
for l in range(3):
    for it in pool[l]:
        if it[1] != 'XI':
            continue
        d = it[2]
        pts = [(d[0], d[1])] + ([(d[2], d[3])] if it[0] == 'seg' else [])
        if any(abs(p[0] - 75.625) < 0.01 and abs(p[1] - 18.625) < 0.01
               for p in pts):
            print('  ', 'FIB'[l], L.fmt_it(it), flush=True)

# 1. C20 0603 -> 0402 at (76.2,18.75) in the model
c20 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.5) < 0.01 and it[2][0] in (75.725, 77.275)]
print('C20 rip:', rip_items(c20), flush=True)
add_items({0: [('pad', 'XI', (75.72, 18.75, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (76.68, 18.75, 0.280, 0.310, 0.0), 0.2)]})
# rip staircase via + its F stub (keep In2 chain; its end dangles in model
# until XI re-plan joins it)
stv = [it for it in pool[0] if it[0] == 'via' and it[1] == 'XI'
       and abs(it[2][0] - 75.625) < 0.01 and abs(it[2][1] - 18.625) < 0.01]
print('staircase via rip:', rip_items(stv), flush=True)

# 2. STP stub + dive via
stub = {0: [('seg', 'ULPI_STP', (76.25, 16.4375, 76.18, 17.3, 0.10), 0.2),
            ('seg', 'ULPI_STP', (76.18, 17.3, 76.06, 17.99, 0.10), 0.2)],
        1: [], 2: []}
for l in range(3):
    stub[l].append(('via', 'ULPI_STP', (76.06, 17.99, 0.25), 0.2))
gate(stub, 'ULPI_STP', pool, 'STP stub+dive')
add_items(stub)
# STP long haul A*: dive via -> west stub via point (70.65,-2.25)
astar = make_astar((69.0, 78.5, -4.0, 19.0), 0.05)
J = astar('ULPI_STP', ((0, 1, 2), 76.06, 17.99), (0, 70.65, -2.25), hw=0.10)
print('STP haul:', 'FOUND' if J else 'NONE', flush=True)
if J:
    print('  vias:', J['vias'], flush=True)
    its = journey_items_dense(J, 'ULPI_STP', hw=0.10)
    gate(its, 'ULPI_STP', pool, 'STP haul')
    add_items(its)
    end = {0: [('seg', 'ULPI_STP', (70.65, -2.25, 71.3375, -2.25, 0.10),
                0.2)], 1: [], 2: []}
    for l in range(3):
        end[l].append(('via', 'ULPI_STP', (70.65, -2.25, 0.25), 0.2))
    gate(end, 'ULPI_STP', pool, 'STP mouth via+stub')
    add_items(end)
    json.dump({'stp': J}, open('scratch/work/ax/quad_design_ax144.json',
                               'w'))
    print('saved quad_design_ax144.json', flush=True)
