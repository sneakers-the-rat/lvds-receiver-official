"""t_at19: full neighbourhood dump for a U9 move.
- All footprints whose centre is in x[62,76], y[-2,10]: refdes, centre,
  pads with nets (world coords).
- All items (any net) in box x[64,74], y[2.5,7.5] on F/In2/B.
- +3V3A via (69.125,4.375): every item touching it (all layers).
- THR_DAC: every item board-wide."""
import wx
_app = wx.App(False)
import pcbnew, sys
sys.path.insert(0, 'scratch/work/ai')
import t_ai_lib as L
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
print('== footprints in region:')
for fp in board.GetFootprints():
    pos = fp.GetPosition()
    cx, cy = pos.x / 1e6, pos.y / 1e6
    if 62 < cx < 76 and -2 < cy < 10:
        print(f'  {fp.GetReference()} centre ({cx:.3f},{cy:.3f}) '
              f'rot {fp.GetOrientationDegrees():.0f}')
        for pad in fp.Pads():
            pp = pad.GetPosition()
            print(f'    pad {pad.GetNumber()} net '
                  f'{pad.GetNetname()} at ({pp.x / 1e6:.3f},'
                  f'{pp.y / 1e6:.3f}) size {pad.GetSize().x / 1e6:.2f}x'
                  f'{pad.GetSize().y / 1e6:.2f}')
items = L.load_items(board)
LN = {0: 'F', 1: 'In2', 2: 'B'}
print('== items in box x[64,74] y[2.5,7.5]:')
for li in range(3):
    for it in items[li]:
        if it[0] == 'seg':
            d = it[2]
            cx, cy = (d[0] + d[2]) / 2, (d[1] + d[3]) / 2
            if 64 < cx < 74 and 2.5 < cy < 7.5:
                print(f'  {LN[li]} {it[1]} seg ({d[0]:.3f},{d[1]:.3f})->'
                      f'({d[2]:.3f},{d[3]:.3f}) w{2 * d[4]:.2f}')
        elif it[0] == 'via':
            d = it[2]
            if 64 < d[0] < 74 and 2.5 < d[1] < 7.5:
                print(f'  via {it[1]} ({d[0]:.3f},{d[1]:.3f}) r{d[2]:.3f}')
print('== THR_DAC all items:')
for li in range(3):
    for it in items[li]:
        if it[1] != 'THR_DAC':
            continue
        if it[0] == 'seg':
            d = it[2]
            print(f'  {LN[li]} seg ({d[0]:.3f},{d[1]:.3f})->'
                  f'({d[2]:.3f},{d[3]:.3f}) w{2 * d[4]:.2f}')
        elif it[0] == 'via':
            d = it[2]
            print(f'  via ({d[0]:.3f},{d[1]:.3f}) r{d[2]:.3f}')
        elif it[0] == 'pad':
            d = it[2]
            print(f'  pad ({d[0]:.3f},{d[1]:.3f})')
