import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
print('== pads/vias in (64,74,15,19.5):', flush=True)
for fp in b.GetFootprints():
    for p in fp.Pads():
        x, y = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
        if 64 < x < 74 and 15 < y < 19.5:
            print('  pad', fp.GetReference(), p.GetNetname(),
                  (round(x, 2), round(y, 2)), flush=True)
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = t.GetPosition().x / 1e6, t.GetPosition().y / 1e6
        if 64 < x < 74 and 15 < y < 19.5:
            print('  via', t.GetNetname(), (round(x, 2), round(y, 2)),
                  flush=True)
print('== footprints in the box:', flush=True)
for fp in b.GetFootprints():
    x, y = fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6
    if 63 < x < 75 and 14 < y < 20.5:
        print('  ', fp.GetReference(), (round(x, 2), round(y, 2)),
              'refdes field:',
              [(round(f.GetPosition().x / 1e6, 2),
                round(f.GetPosition().y / 1e6, 2))
               for f in fp.Fields() if f.GetName() == 'Reference'],
              flush=True)
