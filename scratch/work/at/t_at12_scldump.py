"""t_at12: raw dump of I2C_SCL / I2C_SDA / HV_SHDN items (all layers)
from exp241esc — exact stored endpoints, no chain inference."""
import wx
_app = wx.App(False)
import pcbnew, sys
sys.path.insert(0, 'scratch/work/ai')
import t_ai_lib as L
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)
LN = {0: 'F', 1: 'In2', 2: 'B'}
for net in ('I2C_SCL', 'I2C_SDA', 'HV_SHDN'):
    print(f'== {net}')
    for li in range(3):
        for it in items[li]:
            if it[1] != net:
                continue
            if it[0] == 'seg':
                d = it[2]
                if 60 < d[0] < 76 and -3 < d[1] < 10:
                    print(f'  {LN[li]} seg ({d[0]:.3f},{d[1]:.3f})->'
                          f'({d[2]:.3f},{d[3]:.3f}) w{2 * d[4]:.2f}')
            elif it[0] == 'via':
                d = it[2]
                if 60 < d[0] < 76 and -3 < d[1] < 10:
                    print(f'  via ({d[0]:.3f},{d[1]:.3f}) r{d[2]:.3f}')
            elif it[0] == 'pad':
                d = it[2]
                if 60 < d[0] < 76 and -3 < d[1] < 10:
                    print(f'  pad ({d[0]:.3f},{d[1]:.3f}) '
                          f'{2 * d[2]:.2f}x{2 * d[3]:.2f}')
