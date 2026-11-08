"""t_aq8: exact chains needed for the SPI prep build on exp235:
SWCLK full chain (all layers), +3V3D items in box x[69,76] y[3,9],
DAC_SYNC items in box x[69,76] y[3,9], BOOT0/DBG_RX items in box
x[86,92] y[-21,-14]."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp235.kicad_pcb')
items = load_items(b)
print('=== SWCLK full chain ===')
for li in range(3):
    for it in items[li]:
        if it[1] == 'SWCLK':
            print(f'L{li} {fmt_it(it)}')


def centre(it):
    k, d = it[0], it[2]
    if k in ('pad', 'via'):
        return d[0], d[1]
    return (d[0] + d[2]) / 2, (d[1] + d[3]) / 2


print('=== +3V3D / DAC_SYNC in x[69,76] y[3,9] ===')
for li in range(3):
    for it in items[li]:
        if it[1] not in ('+3V3D', 'DAC_SYNC'):
            continue
        x, y = centre(it)
        if 69 <= x <= 76 and 3 <= y <= 9:
            print(f'L{li} {fmt_it(it)}')
print('=== J4 footprint + pads ===')
for fp in b.GetFootprints():
    x, y = pcbnew.ToMM(fp.GetPosition())
    if 84 <= x <= 96 and -26 <= y <= -18:
        print(f'{fp.GetReference()} at ({x:.3f},{y:.3f})')
        for pad in fp.Pads():
            px, py = pcbnew.ToMM(pad.GetPosition())
            print(f'   .{pad.GetNumber()} {pad.GetNetname()} ({px:.3f},{py:.3f})')
