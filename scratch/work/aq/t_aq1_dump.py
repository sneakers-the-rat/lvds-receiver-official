"""t_aq1: wider dump around U11.14 (+3V3D) on exp234.
All +3V3D/+5V/GND/SW1/FB_3V3/SS_3V3/PG_3V3 copper in box
x[49,64], y[17,31], plus every +3V3D item in x[49,70],y[15,32]."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp234.kicad_pcb')
items = load_items(b)
NETS = {'+3V3D', '+5V', 'GND', 'SW1', 'FB_3V3', 'SS_3V3', 'PG_3V3'}


def centre(it):
    k, d = it[0], it[2]
    if k in ('pad', 'via'):
        return d[0], d[1]
    return (d[0] + d[2]) / 2, (d[1] + d[3]) / 2


for li in range(3):
    for it in items[li]:
        if it[1] not in NETS:
            continue
        cx, cy = centre(it)
        if 49 <= cx <= 70 and 15 <= cy <= 32:
            print(f'L{li} {fmt_it(it)}')
print('--- footprints in box ---')
for fp in b.GetFootprints():
    x, y = pcbnew.ToMM(fp.GetPosition())
    if 49 <= x <= 70 and 15 <= y <= 32:
        print(f'{fp.GetReference()} at ({x:.3f},{y:.3f}) rot {fp.GetOrientationDegrees():.0f}')
