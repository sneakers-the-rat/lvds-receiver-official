import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp249.kicad_pcb')
print('== footprints in (71,82,4,13):', flush=True)
for fp in b.GetFootprints():
    p = fp.GetPosition()
    x, y = p.x / 1e6, p.y / 1e6
    if 71 < x < 82 and 4 < y < 13:
        print(f'  {fp.GetReference()} ({x:.2f},{y:.2f}) rot '
              f'{fp.GetOrientationDegrees()}', flush=True)
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
print('== +3V3D items in (72,80,6,13):', flush=True)
seen = set()
for lay in range(3):
    for it in pool[lay]:
        if it[1] != '+3V3D':
            continue
        d = it[2]
        if 72 < d[0] < 80 and 6 < d[1] < 13:
            s = 'L%d ' % lay + L.fmt_it(it)
            if s not in seen:
                seen.add(s)
                print('  ', s, flush=True)
