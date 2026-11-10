"""t_ba5: survey for the C23 lever + east fence map on exp252.
Dumps: PHY_1V8A items by layer; C23/C22/X1/U5 positions+pads;
B-layer foreign items in box x[73,80.5] y[6.5,17.5];
XI items; +3V3A items in the box."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import pcbnew

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
pool = load_board_pool(BOARD)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}

b = pcbnew.LoadBoard(BOARD)
for ref in ('C23', 'C22', 'C16', 'X1', 'U5', 'C20', 'C24', 'C28'):
    for fp in b.GetFootprints():
        if fp.GetReference() == ref:
            p = fp.GetPosition()
            print(f'{ref} at ({pcbnew.ToMM(p.x):.3f},{pcbnew.ToMM(p.y):.3f})'
                  f' rot {fp.GetOrientationDegrees():.0f} '
                  f'fp {fp.GetFPID().GetLibItemName()}')
            for pad in fp.Pads():
                pp = pad.GetPosition()
                print(f'    pad {pad.GetNumber()} net {pad.GetNetname()} '
                      f'at ({pcbnew.ToMM(pp.x):.3f},{pcbnew.ToMM(pp.y):.3f})')
            break

print('--- PHY_1V8A items ---')
for l in range(3):
    for it in pool[l]:
        if it[1] == 'PHY_1V8A':
            d = it[2]
            if it[0] == 'seg':
                print(f'  {LAYN[l]} seg ({d[0]:.3f},{d[1]:.3f})->'
                      f'({d[2]:.3f},{d[3]:.3f}) hw{d[4]}')
            elif it[0] == 'via':
                print(f'  via ({d[0]:.3f},{d[1]:.3f}) r{d[2]} (all layers)')
            elif it[0] == 'pad':
                print(f'  {LAYN[l]} pad c=({d[0]:.3f},{d[1]:.3f}) '
                      f'hw{d[2]} hh{d[3]}')

print('--- XI items ---')
for l in range(3):
    for it in pool[l]:
        if it[1] == 'XI':
            d = it[2]
            if it[0] == 'seg':
                print(f'  {LAYN[l]} seg ({d[0]:.3f},{d[1]:.3f})->'
                      f'({d[2]:.3f},{d[3]:.3f}) hw{d[4]}')
            elif it[0] == 'via':
                print(f'  via ({d[0]:.3f},{d[1]:.3f}) r{d[2]}')

print('--- B-layer items in box x[73,80.5] y[6.5,17.5], nets of interest ---')
for it in pool[2]:
    if it[1] in ('PHY_1V8A', 'ULPI_STP', 'PHY_1V8'):
        continue
    cc = C(it)
    if 73 <= cc[0] <= 80.5 and 6.5 <= cc[1] <= 17.5:
        d = it[2]
        if it[0] == 'seg':
            print(f'  B {it[1]} seg ({d[0]:.2f},{d[1]:.2f})->'
                  f'({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')
        elif it[0] == 'via':
            print(f'  B {it[1]} via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}')
        elif it[0] == 'pad':
            print(f'  B {it[1]} pad c=({d[0]:.2f},{d[1]:.2f})')
print('=== done ===')
