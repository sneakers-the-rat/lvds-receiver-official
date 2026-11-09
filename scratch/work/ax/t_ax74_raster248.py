"""t_ax64: raster-diff of GND F.Cu fill, exp241 vs exp244, over the
south box (64.5,73.5,-12,2.5) at 0.25 mm. Prints: fill components of
exp244 in the box (labelled grid), and the sever map (fill in 241,
gone in 244)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

BOX = (64.5, 70.5, -0.5, 2.5)
STEP = 0.25


def fillset(path):
    b = pcbnew.LoadBoard(path)
    polys = []
    for z in b.Zones():
        if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu):
            continue
        ps = z.GetFilledPolysList(pcbnew.F_Cu)
        for i in range(ps.OutlineCount()):
            ol = ps.Outline(i)
            pts = [(ol.GetPoint(j).x / 1e6, ol.GetPoint(j).y / 1e6)
                   for j in range(ol.PointCount())]
            polys.append(pts)
    return polys


def inside(polys, x, y):
    # even-odd across all outlines
    cnt = 0
    for pts in polys:
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if xi > x:
                    cnt += 1
    return cnt % 2 == 1


p241 = fillset('hw/pdlvds_rx.exp241.kicad_pcb')
p244 = fillset('hw/pdlvds_rx.exp248.kicad_pcb')
nx = int((BOX[1] - BOX[0]) / STEP)
ny = int((BOX[3] - BOX[2]) / STEP)
g241 = [[inside(p241, BOX[0] + (i + 0.5) * STEP,
                BOX[3] - (j + 0.5) * STEP) for i in range(nx)]
        for j in range(ny)]
g244 = [[inside(p244, BOX[0] + (i + 0.5) * STEP,
                BOX[3] - (j + 0.5) * STEP) for i in range(nx)]
        for j in range(ny)]
# components of g244 (4-connectivity)
comp = [[-1] * nx for _ in range(ny)]
nc = 0
for j in range(ny):
    for i in range(nx):
        if g244[j][i] and comp[j][i] < 0:
            stack = [(j, i)]
            comp[j][i] = nc
            while stack:
                cj, ci = stack.pop()
                for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    jj, ii = cj + dj, ci + di
                    if 0 <= jj < ny and 0 <= ii < nx \
                            and g244[jj][ii] and comp[jj][ii] < 0:
                        comp[jj][ii] = nc
                        stack.append((jj, ii))
            nc += 1
print(f'exp244 fill components in box: {nc}', flush=True)
sizes = [0] * nc
for j in range(ny):
    for i in range(nx):
        if comp[j][i] >= 0:
            sizes[comp[j][i]] += 1
print('sizes:', sizes, flush=True)
print('map: digit = component%10, . = no fill, X = fill in 241 only',
      flush=True)
for j in range(ny):
    row = ''
    for i in range(nx):
        if g244[j][i]:
            row += str(comp[j][i] % 10)
        elif g241[j][i]:
            row += 'X'
        else:
            row += '.'
    print(f'y={BOX[3] - (j + 0.5) * STEP:6.2f} {row}', flush=True)
print('x from', BOX[0], 'step', STEP, flush=True)
