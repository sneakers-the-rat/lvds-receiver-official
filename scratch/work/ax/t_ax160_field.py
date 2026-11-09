import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
box = (75.0, 77.0, 17.0, 19.0)
astar = make_astar(box, 0.05)
cells = dict(zip(astar.__code__.co_freevars, astar.__closure__))
G = cells['GXm'].cell_contents
xs = cells['xs'].cell_contents
ys = cells['ys'].cell_contents
print('field shape:', G.shape, 'xs', xs[:3], xs[-3:], 'ys', ys[:3], ys[-3:],
      flush=True)
# find the G array for net ULPI_STP: GXm may be per-net computed lazily;
# instead call astar once to force computation then re-read
J = astar('ULPI_STP', ((2,), 76.065, 17.99), (2, 76.2, 17.99), hw=0.10)
cells = dict(zip(astar.__code__.co_freevars, astar.__closure__))
G = cells['GXm'].cell_contents
print('after call shape:', getattr(G, 'shape', None), flush=True)
import numpy as np
G = np.asarray(G)
print('ndim', G.ndim, flush=True)
if G.ndim == 3:
    Gb = G[2]
    for iy, y in enumerate(ys):
        if 17.6 <= y <= 18.6:
            row = ''
            for ix, x in enumerate(xs):
                if 75.6 <= x <= 76.5:
                    row += f'{Gb[iy, ix]:+.2f} '
            print(f'y={y:.2f}: {row}', flush=True)
    print('x cols: ', [round(float(x), 2) for x in xs if 75.6 <= x <= 76.5],
          flush=True)
