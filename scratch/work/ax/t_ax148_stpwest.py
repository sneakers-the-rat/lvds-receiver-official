import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
c20 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.5) < 0.01 and it[2][0] in (75.725, 77.275)]
rip_items(c20)
add_items({0: [('pad', 'XI', (75.72, 18.75, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (76.68, 18.75, 0.280, 0.310, 0.0), 0.2)]})
astar = make_astar((73.5, 77.5, 15.5, 19.5), 0.05)
Js = astar('ULPI_STP', ((0,), 76.25, 16.4375), (0, 74.9, 17.9), hw=0.10)
print('stub-west A*:', 'FOUND' if Js else 'NONE', flush=True)
if Js:
    its = journey_items_dense(Js, 'ULPI_STP', hw=0.10)
    worst = (9.9, None, None)
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == 'ULPI_STP':
                    continue
                m = item_margin(l, it, [o])
                if m < worst[0]:
                    worst = (m, it, o)
    print('  gate', f"{worst[0]:+.3f}", 'vs', L.fmt_it(worst[2]), flush=True)
    add_items(its)
    add_items({l: [('via', 'ULPI_STP', (74.9, 17.9, 0.25), 0.2)]
               for l in range(3)})
    box = (69.0, 78.5, -4.0, 19.0)
    for label, g in (('pad F', (0, 71.3375, -2.25)),
                     ('mouth B', (2, 70.65, -2.25)),
                     ('(72,0) B', (2, 72.0, 0.0)),
                     ('(74,6) B', (2, 74.0, 6.0)),
                     ('(74,6) I', (1, 74.0, 6.0))):
        astar = make_astar(box, 0.05)
        J = astar('ULPI_STP', ((0,), 74.9, 17.9), g, hw=0.10)
        print(f'haul -> {label}:', 'FOUND' if J else 'NONE',
              ('vias=' + str(J['vias'])) if J else '', flush=True)
