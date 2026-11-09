import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp242.kicad_pcb')
nc = b.GetNetcodeFromNetname('GND')
tmpl = None
for t in b.GetTracks():
    if type(t).__name__ == 'PCB_VIA' \
            and abs(t.GetPosition().x / 1e6 - 72.875) < 0.01 \
            and abs(t.GetPosition().y / 1e6 - 3.375) < 0.01:
        tmpl = t
        break
v = pcbnew.PCB_VIA(b)
v.SetPosition(pcbnew.VECTOR2I(int(67.29 * 1e6), int(0.86 * 1e6)))
v.SetWidth(tmpl.GetWidth())
v.SetDrill(tmpl.GetDrillValue())
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNetCode(nc)
b.Add(v)
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp243.kicad_pcb')
print('saved exp243 with stitch via (67.29,0.86)', flush=True)
