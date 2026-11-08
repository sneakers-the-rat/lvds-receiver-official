"""t_aq5: SPI endpoints survey on exp235.
U6 pad map (pins 105-120 + 26 + 40), copper within 4 mm of
U6.111/U6.113 (south face) and of U8.7/U8.8, and the west corridor
x[64,72], y[-18,8] all layers (journey field)."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp235.kicad_pcb')
items = load_items(b)

for fp in b.GetFootprints():
    if fp.GetReference() in ('U6', 'U8'):
        for pad in fp.Pads():
            n = pad.GetNetname()
            if n in ('SPI_SCK', 'SPI_MOSI', 'DAC_SYNC', 'USB_RST',
                     'ULPI_STP'):
                x, y = pcbnew.ToMM(pad.GetPosition())
                sx, sy = pcbnew.ToMM(pad.GetSize())
                print(f'{fp.GetReference()}.{pad.GetNumber()} {n} '
                      f'({x:.3f},{y:.3f}) size {sx:.3f}x{sy:.3f}')


def centre(it):
    k, d = it[0], it[2]
    if k in ('pad', 'via'):
        return d[0], d[1]
    return (d[0] + d[2]) / 2, (d[1] + d[3]) / 2


def dump(cx, cy, r, label):
    print(f'=== {label} near ({cx},{cy}) r={r}')
    for li in range(3):
        for it in items[li]:
            x, y = centre(it)
            if abs(x - cx) <= r and abs(y - cy) <= r:
                print(f'  L{li} {fmt_it(it)}')


# U6 south face SPI pads: find coords first from the pad map above;
# survey boxes are filled in by the prints; corridor dump:
print('=== corridor x[64,72] y[-18,8] (seg/via centres only, no pads) ===')
for li in range(3):
    for it in items[li]:
        if it[0] == 'pad':
            continue
        x, y = centre(it)
        if 64 <= x <= 72 and -18 <= y <= 8:
            print(f'  L{li} {fmt_it(it)}')
