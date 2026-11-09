import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
print('== F items in (68,71,11.5,13.5):', flush=True)
seen = set()
for it in pool[0]:
    d = it[2]
    if 68 < d[0] < 71 and 11.5 < d[1] < 13.5:
        s = L.fmt_it(it)
        if s not in seen:
            seen.add(s)
            print('  ', s, flush=True)
astar = make_astar((65.0, 71.0, 5.0, 14.0), 0.05)
J = astar('GND', ((0,), 69.475, 12.75), (0, 66.2, 6.5), hw=0.10)
print('GND F run pad2 -> via (66.2,6.5):', 'FOUND' if J else 'NONE',
      flush=True)
if J:
    print('  vias:', J['vias'], flush=True)
