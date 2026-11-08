"""t_aq19: R16 + TP3 neighbourhood on exp235: BOOT0/GND/DBG_RX
items in x[84,93] y[-24,-17]; R16/TP3 footprint geometry."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp235.kicad_pcb')
items = load_items(b)


def centre(it):
    d = it[2]
    if it[0] in ('pad', 'via'):
        return d[0], d[1]
    return (d[0] + d[2]) / 2, (d[1] + d[3]) / 2


for li in range(3):
    print(f'--- L{li} BOOT0/GND/DBG_RX x[84,93] y[-24,-17] ---')
    for it in items[li]:
        if it[1] not in ('BOOT0', 'GND', 'DBG_RX'):
            continue
        x, y = centre(it)
        if 84 <= x <= 93 and -24 <= y <= -17:
            print(fmt_it(it))
for fp in b.GetFootprints():
    if fp.GetReference() in ('R16', 'TP3'):
        x, y = pcbnew.ToMM(fp.GetPosition())
        print(f'{fp.GetReference()} at ({x:.3f},{y:.3f}) '
              f'orient {fp.GetOrientationDegrees():.0f}')
        bb = fp.GetBoundingBox()
        print(f'   bbox x[{pcbnew.ToMM(bb.GetLeft()):.3f},'
              f'{pcbnew.ToMM(bb.GetRight()):.3f}] '
              f'y[{pcbnew.ToMM(bb.GetTop()):.3f},'
              f'{pcbnew.ToMM(bb.GetBottom()):.3f}]')
        for pad in fp.Pads():
            px, py = pcbnew.ToMM(pad.GetPosition())
            sx, sy = pcbnew.ToMM(pad.GetSize())
            print(f'   .{pad.GetNumber()} {pad.GetNetname()} '
                  f'({px:.3f},{py:.3f}) size {sx:.2f}x{sy:.2f}')
