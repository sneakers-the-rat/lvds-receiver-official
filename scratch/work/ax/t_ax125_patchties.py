import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
patches = [(68.48, 11.39, 70.35, 14.02), (68.62, 7.62, 72.46, 12.58),
           (72.68, 8.93, 75.5, 10.72), (75.09, 7.01, 77.69, 10.45),
           (68.79, 14.23, 72.37, 21.55)]
vias = []
pads = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == 'GND':
        vias.append((round(t.GetPosition().x / 1e6, 3),
                     round(t.GetPosition().y / 1e6, 3)))
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == 'GND':
            pads.append((fp.GetReference() + '.' + p.GetNumber(),
                         round(p.GetPosition().x / 1e6, 3),
                         round(p.GetPosition().y / 1e6, 3)))
for i, (x0, y0, x1, y1) in enumerate(patches):
    inv = [v for v in vias if x0 <= v[0] <= x1 and y0 <= v[1] <= y1]
    inp = [p for p in pads if x0 <= p[1] <= x1 and y0 <= p[2] <= y1]
    print(f'patch {i} bbox ({x0},{y0},{x1},{y1}):', flush=True)
    print('   vias:', inv, flush=True)
    print('   pads:', inp, flush=True)
