"""t_aq6: full DAC_SYNC chain on exp235 + south-face fence around
U6.110-113 + south corridor items x[82,96], y[-20,-12]."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp235.kicad_pcb')
items = load_items(b)
print('=== DAC_SYNC full chain ===')
for li in range(3):
    for it in items[li]:
        if it[1] == 'DAC_SYNC':
            print(f'L{li} {fmt_it(it)}')


def centre(it):
    k, d = it[0], it[2]
    if k in ('pad', 'via'):
        return d[0], d[1]
    return (d[0] + d[2]) / 2, (d[1] + d[3]) / 2


print('=== box x[82,96] y[-20,-12] all items ===')
for li in range(3):
    for it in items[li]:
        x, y = centre(it)
        if 82 <= x <= 96 and -20 <= y <= -12:
            print(f'L{li} {fmt_it(it)}')
print('=== footprints x[82,96] y[-20,-12] ===')
for fp in b.GetFootprints():
    x, y = pcbnew.ToMM(fp.GetPosition())
    if 82 <= x <= 96 and -20 <= y <= -12:
        print(f'{fp.GetReference()} at ({x:.3f},{y:.3f})')
