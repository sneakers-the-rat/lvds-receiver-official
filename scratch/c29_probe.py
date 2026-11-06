import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
src = open('scratch/island_stitch.py').read()
exec(src.split('gnd_net = ')[0].replace("sys.argv[1]", "'scratch/grid182b.kicad_pcb'").replace("sys.argv[2]", "'/dev/null'"))
# note: island_stitch's via_ok lacks the stub's own-net exception needs; reuse as-is (GND via)
# free-cell component of C29.2 on F at 0.125 grid (same passability as grid_route)
width, clr_net = netclass('GND'); HW = width / 2
def cell_clear(x, y):
    for it in items[0].near(0, x, y):
        if it[1] == 'GND': continue
        clr = max(clr_net, netclass(it[1])[1]) + 0.02
        if router.dist_to_item(it, x, y) < HW + clr: return False
    return True
X0, X1, Y0, Y1 = 18.0, 28.0, -9.0, 6.5
CELL = 0.125
NX = int((X1 - X0) / CELL) + 1; NY = int((Y1 - Y0) / CELL) + 1
pad = None
for fp in board.GetFootprints():
    if fp.GetReference() == 'C29':
        for p in fp.Pads():
            if p.GetNumber() == '2': pad = p
pos = pcbnew.ToMM(pad.GetPosition()); size = pcbnew.ToMM(pad.GetSize())
pad_t = ('pad', 'GND', (pos[0], pos[1], size[0]/2, size[1]/2, math.radians(pad.GetOrientationDegrees())), 0.2)
def is_start(x, y): return router.dist_to_item(pad_t, x, y) <= 0.05
comp = set()
stack = []
for i in range(NX):
    for j in range(NY):
        x, y = X0 + i * CELL, Y0 + j * CELL
        if is_start(x, y): stack.append((i, j)); comp.add((i, j))
while stack:
    i, j = stack.pop()
    for di, dj in ((1,0),(-1,0),(0,1),(0,-1)):
        nb = (i + di, j + dj)
        if nb in comp or not (0 <= nb[0] < NX and 0 <= nb[1] < NY): continue
        x, y = X0 + nb[0] * CELL, Y0 + nb[1] * CELL
        if cell_clear(x, y): comp.add(nb); stack.append(nb)
xs = [X0 + i * CELL for i, j in comp]; ys = [Y0 + j * CELL for i, j in comp]
print(f'C29.2 free component: {len(comp)} cells, x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}]')
# candidate via points inside the component (on 0.25 lattice), tested with via_ok
best = []
for i, j in comp:
    x, y = X0 + i * CELL, Y0 + j * CELL
    if abs(x * 4 - round(x * 4)) > 1e-6 or abs(y * 4 - round(y * 4)) > 1e-6: continue
    if via_ok(x, y):
        best.append((round(math.hypot(x - 26.4, y - 0.23), 1), x, y))
best.sort()
print('via_ok points in component (dist to R24.2 via, x, y):', best[:8])
