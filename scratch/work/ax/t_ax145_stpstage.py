import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
c20 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.5) < 0.01 and it[2][0] in (75.725, 77.275)]
rip_items(c20)
add_items({0: [('pad', 'XI', (75.72, 18.75, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (76.68, 18.75, 0.280, 0.310, 0.0), 0.2)]})
stv = [it for it in pool[0] if it[0] == 'via' and it[1] == 'XI'
       and abs(it[2][0] - 75.625) < 0.01 and abs(it[2][1] - 18.625) < 0.01]
rip_items(stv)
stub = {0: [('seg', 'ULPI_STP', (76.25, 16.4375, 76.08, 17.3, 0.10), 0.2),
            ('seg', 'ULPI_STP', (76.08, 17.3, 76.065, 17.99, 0.10), 0.2)],
        1: [], 2: []}
for l in range(3):
    stub[l].append(('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2))
worst = (9.9, None, None)
for l in range(3):
    for it in stub[l]:
        for o in pool[l]:
            if o[1] == 'ULPI_STP':
                continue
            m = item_margin(l, it, [o])
            if m < worst[0]:
                worst = (m, it, o)
print('STP stub v2 gate', f"{worst[0]:+.3f}", 'vs', L.fmt_it(worst[2]),
      flush=True)
add_items(stub)
box = (69.0, 78.5, -4.0, 19.0)
for label, s, g in (
        ('dive->(76,10) B', ((2,), 76.065, 17.99), (2, 76.0, 10.0)),
        ('dive->(76,10) I', ((1,), 76.065, 17.99), (1, 76.0, 10.0)),
        ('(76,10)B->(74,4)B', ((2,), 76.0, 10.0), (2, 74.0, 4.0)),
        ('(76,10)B->(70.65,-2.25)B', ((2,), 76.0, 10.0), (2, 70.65, -2.25)),
        ('dive->mouth ML', ((0,), 76.065, 17.99), (2, 70.65, -2.25)),
        ('dive->(72,0)B', ((2,), 76.065, 17.99), (2, 72.0, 0.0)),
        ('dive->(73,6)I', ((1,), 76.065, 17.99), (1, 73.0, 6.0))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', s, g, hw=0.10)
    print(f'{label}:', 'FOUND' if J else 'NONE',
          ('vias=' + str(J['vias'])) if J else '', flush=True)
