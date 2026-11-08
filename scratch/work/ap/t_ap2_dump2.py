"""t_ap2: corridor dump (exp233) -- all In2 items in the J1->D3
corridor box, all items in the D3 box, F items in the J1 box."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp233.kicad_pcb')
items = load_items(b)

def inbox(it, box):
    k, net, d, clr = it
    x0, x1, y0, y1 = box
    if k == 'seg':
        return x0 <= (d[0] + d[2]) / 2 <= x1 and y0 <= (d[1] + d[3]) / 2 <= y1
    return x0 <= d[0] <= x1 and y0 <= d[1] <= y1

print('--- In2 items, corridor box x[27,47] y[44,75] ---')
for it in items[1]:
    if inbox(it, (27, 47, 44, 75)):
        print(' ', fmt_it(it))
print('--- ALL layers, D3 box x[40,49] y[42,53] ---')
for li in range(3):
    for it in items[li]:
        if inbox(it, (40, 49, 42, 53)):
            print(f'  L{li}', fmt_it(it))
print('--- F items, J1 box x[25.5,35.5] y[65,75.5] ---')
for it in items[0]:
    if inbox(it, (25.5, 35.5, 65, 75.5)):
        print(' ', fmt_it(it))
