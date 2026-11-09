import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
box = (71.0, 78.5, 8.0, 19.5)
cur = ((2,), 76.35, 18.1)
for label, g in (('B (75.5,16.9)', (2, 75.5, 16.9)),
                 ('B (73.9,16.9)', (2, 73.9, 16.9)),
                 ('B (72.75,15.0)', (2, 72.75, 15.0)),
                 ('B (72.75,12.0)', (2, 72.75, 12.0)),
                 ('B (73.5,9.5)', (2, 73.5, 9.5))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', cur, g, hw=0.10)
    print(f'stage -> {label}:', 'FOUND' if J else 'NONE',
          ('vias=' + str(J['vias'])) if J else '', flush=True)
    if not J:
        break
    cur = ((g[0],), g[1], g[2])
