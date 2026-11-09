import sys, math
import numpy as np
sys.path.insert(0, 'scratch/work/ax')

src = open('scratch/work/ax/t_ax246_design214ad.py').read()
head = src.split("\nbox = (64.0")[0]
exec(head)

box = (68.8, 72.6, -5.2, -0.8)
for s, g in ((((1,), 71.5, -3.3), (0, 71.3375, -2.25)),
             (((1,), 69.65, -3.6), (0, 71.3375, -2.25))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', s, g, hw=0.10)
    print(f'ML A* {s} -> {g}:', 'FOUND' if J else 'NONE',
          ('vias=' + str(J['vias'])) if J else '', flush=True)
    if J:
        print('  runs:', [(r[0][0], len(r)) for r in J['runs']], flush=True)


def df_of(it, GX, GY):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = GX - cx, GY - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = GX - x1, GY - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    return np.hypot(GX - d[0], GY - d[1]) - d[2]


# viafit census over the tail box
step = 0.05
xs = np.arange(box[0], box[1] + 1e-9, step)
ys = np.arange(box[2], box[3] + 1e-9, step)
GX, GY = np.meshgrid(xs, ys)
G = []
for l in range(3):
    f = np.full(GX.shape, 9.9)
    for it in pool[l]:
        if it[1] == 'ULPI_STP':
            continue
        req = max(0.2, it[3])
        f = np.minimum(f, df_of(it, GX, GY) - req)
    G.append(f)
VF = np.minimum(np.minimum(G[0], G[1]), G[2])
print('=== viafit map (V = viafit>=0.25 & all G>=0.10; v = viafit>=0.25 '
      'only; . = G_F>=0.35; # else) ===', flush=True)
print('      ' + ''.join(str(int(round(x * 10)) % 10) for x in xs), flush=True)
for j in range(len(ys) - 1, -1, -1):
    row = ''
    for i in range(len(xs)):
        if VF[j, i] >= 0.25 and G[0][j, i] >= 0.10 and G[1][j, i] >= 0.10 \
           and G[2][j, i] >= 0.10:
            row += 'V'
        elif VF[j, i] >= 0.25:
            row += 'v'
        elif G[0][j, i] >= 0.35:
            row += '.'
        else:
            row += '#'
    print(f'{ys[j]:6.2f}' + row, flush=True)
cells = [(float(xs[i]), float(ys[j])) for j in range(len(ys))
         for i in range(len(xs)) if VF[j, i] >= 0.25]
print('viafit cells:', len(cells), flush=True)
if cells:
    xs_c = [c[0] for c in cells]
    ys_c = [c[1] for c in cells]
    print(f'  x range {min(xs_c):.2f}..{max(xs_c):.2f}, '
          f'y range {min(ys_c):.2f}..{max(ys_c):.2f}', flush=True)
print('ML PROBE DONE', flush=True)
