import sys, math
import numpy as np
sys.path.insert(0, 'scratch/work/ax')

src = open('scratch/work/ax/t_ax246_design214ad.py').read()
head = src.split("\nbox = (64.0")[0]
exec(head)


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


def gmap(layer, x0, x1, y0, y1, label):
    step = 0.05
    xs = np.arange(x0, x1 + 1e-9, step)
    ys = np.arange(y0, y1 + 1e-9, step)
    GX, GY = np.meshgrid(xs, ys)
    f = np.full(GX.shape, 9.9)
    for it in pool[layer]:
        if it[1] == 'ULPI_STP':
            continue
        req = max(0.2, it[3])
        f = np.minimum(f, df_of(it, GX, GY) - req)
    print(f'=== G[{layer}] {label} (x {x0}..{x1}; # <0.10, + 0.10-0.24, '
          f'o 0.25-0.34, . >=0.35) ===', flush=True)
    print('      ' + ''.join(str(int(round(x * 10)) % 10) for x in xs),
          flush=True)
    for j in range(len(ys) - 1, -1, -1):
        row = ''
        for i in range(len(xs)):
            g = f[j, i]
            row += '#' if g < 0.10 else ('+' if g < 0.25 else
                                         ('o' if g < 0.35 else '.'))
        print(f'{ys[j]:6.2f}' + row, flush=True)
    return f


# north crossing + mouth region, all layers
for l, nm in ((0, 'F'), (1, 'In2'), (2, 'B')):
    gmap(l, 66.4, 72.2, -3.6, 2.2, f'{nm} mouth/north')

# item dump: F and B items in the region (for the hand design)
print('=== F/B items in (66.4..72.2, -3.6..2.2) ===', flush=True)
for l in (0, 2):
    for it in pool[l]:
        kind, d = it[0], it[2]
        if kind == 'pad':
            cx, cy = d[0], d[1]
            if 65.4 < cx < 73.2 and -4.6 < cy < 3.2:
                print(f'  L{l}', L.fmt_it(it), flush=True)
        elif kind == 'seg':
            if max(d[0], d[2]) >= 65.4 and min(d[0], d[2]) <= 73.2 \
               and max(d[1], d[3]) >= -4.6 and min(d[1], d[3]) <= 3.2:
                print(f'  L{l}', L.fmt_it(it), flush=True)
        else:
            if 65.4 < d[0] < 73.2 and -4.6 < d[1] < 3.2:
                print(f'  L{l}', L.fmt_it(it), flush=True)
print('MAPS DONE', flush=True)
