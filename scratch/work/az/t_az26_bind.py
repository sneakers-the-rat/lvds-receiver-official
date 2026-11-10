import sys
sys.path.insert(0, 'scratch/work/ax'); sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *
import t_ai_lib as L
pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')
v = ('via', 'XI', (75.2, 10.2, 0.25), 0.2)
for l in range(3):
    ms = sorted((round(item_margin(l, v, [o]), 3), o) for o in pool[l] if o[1] != 'XI')
    print(f'L{l} binders:', [(m, L.fmt_it(o)) for m, o in ms[:3]])
try:
    ch = chain_segs(pool, 'PHY_1V8A', 2, (75.3, 11.35), (71.48, 15.38))
    pts = [(round(it[2][0],2), round(it[2][1],2)) for it in ch]
    pts.append((round(ch[-1][2][2],2), round(ch[-1][2][3],2)))
    print('1V8A B chain joints (every 6th):', pts[::6], '... total', len(ch))
    print('1V8A B chain bbox: x', min(p[0] for p in pts), max(p[0] for p in pts),
          'y', min(p[1] for p in pts), max(p[1] for p in pts))
except SystemExit as e:
    print('1V8A chain FAILED', e)
