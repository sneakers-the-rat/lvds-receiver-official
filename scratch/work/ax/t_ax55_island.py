import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
for path in ('hw/pdlvds_rx.exp244.kicad_pcb',):
    b = pcbnew.LoadBoard(path)
    print('==', path, flush=True)
    for z in b.Zones():
        if z.GetNetname() != 'GND':
            continue
        for lay, nm in ((pcbnew.F_Cu, 'F'), (pcbnew.In1_Cu, 'In1')):
            if not z.IsOnLayer(lay):
                continue
            polys = z.GetFilledPolysList(lay)
            n = polys.OutlineCount()
            print(f'  zone {z.GetZoneName() or "-"} L{nm}: {n} outlines',
                  flush=True)
            for i in range(n):
                bb = polys.Outline(i).BBox()
                print(f'    outline{i}: x {bb.GetLeft()/1e6:.2f}..'
                      f'{bb.GetRight()/1e6:.2f} y {bb.GetTop()/1e6:.2f}'
                      f'..{bb.GetBottom()/1e6:.2f}', flush=True)
