"""t_aq20: U6 south inner region on exp235: all pads of U6 with
y in [-17, -12], all layers' items in x[84,94] y[-17,-12]."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp235.kicad_pcb')
for fp in b.GetFootprints():
    if fp.GetReference() == 'U6':
        x, y = pcbnew.ToMM(fp.GetPosition())
        print(f'U6 at ({x:.3f},{y:.3f})')
        for pad in fp.Pads():
            px, py = pcbnew.ToMM(pad.GetPosition())
            if -17.5 <= py <= -11.5:
                sx, sy = pcbnew.ToMM(pad.GetSize())
                print(f'   .{pad.GetNumber()} {pad.GetNetname()} '
                      f'({px:.3f},{py:.3f}) size {sx:.2f}x{sy:.2f}')
items = load_items(b)


def centre(it):
    d = it[2]
    if it[0] in ('pad', 'via'):
        return d[0], d[1]
    return (d[0] + d[2]) / 2, (d[1] + d[3]) / 2


for li in range(3):
    print(f'--- L{li} tracks x[84,94] y[-17,-12] ---')
    for it in items[li]:
        if it[0] == 'pad':
            continue
        x, y = centre(it)
        if 84 <= x <= 94 and -17 <= y <= -12:
            print(fmt_it(it))
