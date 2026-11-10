"""t_az5: fine-grid (0.125) A* probes for the 3 open nets on exp251
as-built, using the proven au71 make_astar via t_ax0_pre. If a journey
is FOUND, print its vias + run point counts so it can be gated exactly.
"""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')

def probe(net, box, start, goals, hw=0.10):
    astar = make_astar(box, 0.125)
    for (gl, gx, gy) in goals:
        r = astar(net, start, (gl, gx, gy), hw)
        if r:
            print(f'  {net} -> L{gl} ({gx},{gy}): FOUND vias={r["vias"]} '
                  f'runs={[(rn["layer"], len(rn["pts"])) for rn in r["runs"]]}',
                  flush=True)
        else:
            print(f'  {net} -> L{gl} ({gx},{gy}): NONE', flush=True)

print('PHY_1V8 (start C22.1 F):')
probe('PHY_1V8', (68.0, 82.0, 6.0, 22.0), ((0,), 72.02, 18.0),
      [(0, 77.25, 16.4375), (2, 77.8, 16.2), (2, 78.1, 17.5),
       (0, 77.9, 10.08), (2, 76.95, 13.0)])
print('XI (start U7.28 F):')
probe('XI', (70.0, 88.0, 8.0, 23.0), ((0,), 76.25, 11.562),
      [(2, 75.625, 18.625), (0, 75.625, 18.625), (1, 75.625, 18.625),
       (0, 75.72, 18.73), (2, 78.375, 21.125), (0, 85.75, 18.25)])
print('USB_RST (start U7.9 F):')
probe('USB_RST', (68.0, 84.0, 0.0, 20.0), ((0,), 74.25, 16.4375),
      [(0, 74.75, 4.662), (2, 74.75, 4.662), (1, 74.75, 4.662)])
print('=== done ===')
