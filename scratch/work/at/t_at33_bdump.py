import wx
_app = wx.App(False)
import pcbnew, sys
sys.path.insert(0, 'scratch/work/ai')
import t_ai_lib as L
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)
print('--- B (L2) items in corridor box x[61,68] y[3,18]:')
for it in items[2]:
    d = it[2]
    if it[0] == 'seg':
        cx, cy = (d[0]+d[2])/2, (d[1]+d[3])/2
    else:
        cx, cy = d[0], d[1]
    if 61 <= cx <= 68 and 3 <= cy <= 18:
        print('  ', L.fmt_it(it))
print('--- B (L2) items in south box x[68,72] y[-3,4]:')
for it in items[2]:
    d = it[2]
    if it[0] == 'seg':
        cx, cy = (d[0]+d[2])/2, (d[1]+d[3])/2
    else:
        cx, cy = d[0], d[1]
    if 68 <= cx <= 72 and -3 <= cy <= 4:
        print('  ', L.fmt_it(it))
