"""t_av7: two long-bridge A* shots for XO + knot footprint census.
Pool state: au93 model with RBIAS staircase (19) ripped, no ride."""
import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au')
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
g = {'__name__': 'av7'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
make_astar = g['make_astar']
import pcbnew
import t_ai_lib as L

R2 = lambda v: round(v, 3)
STUB = (73.875, 11.625, 73.875, 12.875)
VERT = (73.875, 12.875, 73.875, 16.375)
n = 0
for it in list(pool[1]):
    if it[0] == 'seg' and it[1] == 'RBIAS':
        if tuple(R2(v) for v in it[2]) not in (STUB, VERT):
            pool[1].remove(it)
            n += 1
print(f'ripped {n} staircase segs', flush=True)

print('=== shot I: In2 long ride (87.5,10.75) -> XO vertical ===',
      flush=True)
aI = make_astar((72.5, 88.5, 9.5, 17.0), step=0.025)
for goal in ((1, 73.125, 13.5), (1, 73.125, 11.375)):
    J = aI('XO', ((1,), 87.5, 10.75), goal, 0.10)
    print(f'  goal {goal}: ' +
          ('NONE' if J is None else
           f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'),
          flush=True)

print('=== shot N: B ride (87.5,10.75) -> frag-1 B seg (74.125,12.25)'
      ' ===', flush=True)
aN = make_astar((71.5, 88.5, 9.5, 14.0), step=0.025)
J = aN('XO', ((2,), 87.5, 10.75), (2, 74.125, 12.25), 0.10)
print('  ' + ('NONE' if J is None else
              f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'),
      flush=True)

print('=== knot footprints (pads in x[67,75] y[17,23]) ===', flush=True)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
for fp in b.GetFootprints():
    hits = []
    for pad in fp.Pads():
        x, y = pcbnew.ToMM(pad.GetPosition())
        if 67 < x < 75 and 17 < y < 23:
            hits.append((pad.GetName(), pad.GetNetname(),
                         round(x, 3), round(y, 3)))
    if hits:
        fx, fy = pcbnew.ToMM(fp.GetPosition())
        print(f'{fp.GetReference()} at ({fx:.3f},{fy:.3f}) '
              f'rot={fp.GetOrientationDegrees():.0f}:', flush=True)
        for h in sorted(hits):
            print(f'    pad {h[0]} {h[1]} ({h[2]},{h[3]})', flush=True)
print('done', flush=True)
