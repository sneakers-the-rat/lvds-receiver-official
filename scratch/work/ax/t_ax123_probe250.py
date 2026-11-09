import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
# +3V3D chain around (74.875,8.875) on the BOARD
print('== tracks touching (74.875,8.875)/(74.875,8.625):', flush=True)
for t in b.GetTracks():
    s = (round(t.GetStart().x / 1e6, 3), round(t.GetStart().y / 1e6, 3))
    e = (round(t.GetEnd().x / 1e6, 3), round(t.GetEnd().y / 1e6, 3)) \
        if hasattr(t, 'GetEnd') else s
    if (abs(s[0] - 74.875) < 0.01 and abs(s[1] - 8.875) < 0.3) or \
       (abs(e[0] - 74.875) < 0.01 and abs(e[1] - 8.875) < 0.3):
        print('  ', t.GetNetname(), s, '->', e,
              'via' if isinstance(t, pcbnew.PCB_VIA) else 'seg', flush=True)
# C23 refdes position
for fp in b.GetFootprints():
    if fp.GetReference() in ('C23', 'C16'):
        print(fp.GetReference(), 'pos',
              (round(fp.GetPosition().x / 1e6, 2),
               round(fp.GetPosition().y / 1e6, 2)), 'refdes via fields:',
              flush=True)
        for f in fp.Fields():
            print('   field', f.GetName(),
                  (round(f.GetPosition().x / 1e6, 2),
                   round(f.GetPosition().y / 1e6, 2)), flush=True)
# GND F zone islands: outlines + bboxes, exp249 vs exp250
def islands(path):
    bb = pcbnew.LoadBoard(path)
    out = []
    for z in bb.Zones():
        if z.GetNetname() == 'GND':
            polys = z.GetFilledPolysList(pcbnew.F_Cu)
            for i in range(polys.OutlineCount()):
                bx = polys.Outline(i).BBox()
                out.append((round(bx.GetLeft() / 1e6, 2),
                            round(bx.GetTop() / 1e6, 2),
                            round(bx.GetRight() / 1e6, 2),
                            round(bx.GetBottom() / 1e6, 2)))
    return sorted(out)
i249 = islands('hw/pdlvds_rx.exp249.kicad_pcb')
i250 = islands('hw/pdlvds_rx.exp250.kicad_pcb')
print(f'GND F islands exp249: {len(i249)}  exp250: {len(i250)}', flush=True)
s249, s250 = set(i249), set(i250)
for x in sorted(s250 - s249):
    print('  NEW island bbox', x, flush=True)
for x in sorted(s249 - s250):
    print('  GONE island bbox', x, flush=True)
