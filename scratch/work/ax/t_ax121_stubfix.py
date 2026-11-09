import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
MM = 1000000
def V(x, y):
    return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
nc = b.GetNetcodeFromNetname('PHY_1V8A')
t = pcbnew.PCB_TRACK(b)
t.SetStart(V(71.48, 15.15))
t.SetEnd(V(71.525, 14.75))
t.SetLayer(pcbnew.F_Cu)
t.SetWidth(200000)
t.SetNetCode(nc)
b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp250.kicad_pcb')
print('stub extended to pad centre; saved')
