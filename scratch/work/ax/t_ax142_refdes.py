import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
def V(x, y):
    return pcbnew.VECTOR2I(int(round(x * 1000000)), int(round(y * 1000000)))
for fp in b.GetFootprints():
    if fp.GetReference() == 'C23':
        for f in fp.Fields():
            if f.GetName() == 'Reference':
                f.SetPosition(V(59.85, 16.25))
                print('C23 refdes -> (59.85,16.25)')
b.Save('hw/pdlvds_rx.exp250.kicad_pcb')
print('saved')
