import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
worst = (9.9, None)
for l in range(3):
    it = ('via', 'GND', (75.25, 10.55, 0.25), 0.2)
    for o in pool[l]:
        if o[1] == 'GND':
            continue
        m = item_margin(l, it, [o])
        if m < worst[0]:
            worst = (m, o)
print('stitch via (75.25,10.55) gate worst', f"{worst[0]:+.3f}",
      'vs', L.fmt_it(worst[1]), flush=True)
if worst[0] < -0.001:
    print('ABORT: via does not gate')
    sys.exit(0)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
MM = 1000000
def V(x, y):
    return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
nc = b.GetNetcodeFromNetname('GND')
t = pcbnew.PCB_VIA(b)
t.SetPosition(V(75.25, 10.55))
t.SetWidth(500000)
t.SetDrill(300000)
t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
t.SetViaType(pcbnew.VIATYPE_THROUGH)
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
