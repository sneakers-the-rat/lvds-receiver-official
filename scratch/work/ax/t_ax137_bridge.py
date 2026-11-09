import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
trk = {0: [('seg', 'GND', (73.1, 10.15, 73.0, 10.7, 0.10), 0.2)], 1: [], 2: []}
worst = (9.9, None, None)
for l in range(3):
    for it in trk[l]:
        for o in pool[l]:
            if o[1] == 'GND':
                continue
            m = item_margin(l, it, [o])
            if m < worst[0]:
                worst = (m, it, o)
print('bridge track gate worst', f"{worst[0]:+.3f}", L.fmt_it(worst[1]),
      'vs', L.fmt_it(worst[2]), flush=True)
if worst[0] < -0.001:
    print('ABORT')
    sys.exit(0)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
MM = 1000000
def V(x, y):
    return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
nc = b.GetNetcodeFromNetname('GND')
t = pcbnew.PCB_TRACK(b)
t.SetStart(V(73.1, 10.15))
t.SetEnd(V(73.0, 10.7))
t.SetLayer(pcbnew.F_Cu)
t.SetWidth(200000)
t.SetNetCode(nc)
b.Add(t)
for fp in b.GetFootprints():
    if fp.GetReference() == 'C23':
        for f in fp.Fields():
            if f.GetName() == 'Reference':
                f.SetPosition(V(67.3, 16.9))
                print('C23 refdes -> (67.3,16.9)')
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp250.kicad_pcb')
print('saved')
