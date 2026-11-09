import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp248.kicad_pcb')
print('F items in (67.8,68.9,0.4,1.4):', flush=True)
for it in pool[0]:
    d = it[2]
    if 67.8 < d[0] < 68.9 and 0.4 < d[1] < 1.4:
        print('  ', L.fmt_it(it), flush=True)
others = [o for o in pool[0] if o[1] != 'GND']
for (x, y) in ((68.3, 0.9), (68.3, 0.75), (68.15, 0.95), (68.45, 1.0)):
    m, b = L.pt_margin(0, x, y, 'GND', 0.15, others)
    print(f'F GND w0.3 pt ({x},{y}): {m:+.3f} binder {L.fmt_it(b)}',
          flush=True)
seg = ('seg', 'GND', (67.95, 0.92, 68.65, 0.92, 0.15), 0.2)
m = min(item_margin(0, seg, [o]) for o in pool[0] if o[1] != 'GND')
print(f'GND tracklet (67.95,0.92)->(68.65,0.92) w0.3 gate: {m:+.3f}',
      flush=True)
