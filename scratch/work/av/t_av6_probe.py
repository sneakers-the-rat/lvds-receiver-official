"""t_av6: probe the XO dip A* fields in the dip-first pool state
(RBIAS staircase ripped, no ride). Print goal/start cell legality,
the killing fences, and a legality map."""
import wx
_app = wx.App(False)
import sys, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av6'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
import t_ai_lib as L
import numpy as np

R2 = lambda v: round(v, 3)
STUB = (73.875, 11.625, 73.875, 12.875)
VERT = (73.875, 12.875, 73.875, 16.375)
n = 0
for it in list(pool[1]):
    if it[0] == 'seg' and it[1] == 'RBIAS':
        rg = tuple(R2(v) for v in it[2])
        if rg not in (STUB, VERT):
            pool[1].remove(it)
            n += 1
print(f'ripped {n} staircase segs', flush=True)

NET = 'XO'
myclr = L.netclass(NET)[1]
box = (68.3, 74.6, 18.9, 22.6)
X0, X1, Y0, Y1 = box
step = 0.025
xs = np.arange(X0, X1 + 1e-9, step)
ys = np.arange(Y0, Y1 + 1e-9, step)
GX, GY = np.meshgrid(xs, ys)


def df(it):
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


G = {}
worst = {}
for l in range(3):
    f = np.full(GX.shape, 9.9)
    w = np.full(GX.shape, '', dtype=object)
    for it in pool[l]:
        if it[1] == NET:
            continue
        req = max(myclr, it[3])
        cand = df(it) - req
        upd = cand < f
        f = np.where(upd, cand, f)
        w = np.where(upd, L.fmt_it(it), w)
    G[l] = f
    worst[l] = w

track = {l: G[l] >= 0.10 for l in range(3)}
viafit = np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25


def cell(x, y):
    return (int(round((y - Y0) / step)), int(round((x - X0) / step)))


for name, (x, y) in (('start B stub', (71.875, 19.625)),
                     ('goal In2', (68.875, 20.375))):
    iy, ix = cell(x, y)
    print(f'{name} ({x},{y}): ' +
          ' '.join(f'L{l} field={G[l][iy, ix]:+.3f} '
                   f'track={track[l][iy, ix]}' for l in range(3)) +
          f' viafit={viafit[iy, ix]}', flush=True)
    for l in range(3):
        print(f'    L{l} worst fence: {worst[l][iy, ix]}', flush=True)

print('--- ALL viafit cells in box (0.025 grid) ---', flush=True)
cells = [(float(xs[ix]), float(ys[iy]))
         for iy in range(len(ys)) for ix in range(len(xs))
         if viafit[iy, ix]]
print(f'viafit cells: {len(cells)}', flush=True)
for c in cells[:40]:
    print(f'   {c}', flush=True)

print('--- candidate via points: viafit + fields ---', flush=True)
for (x, y) in [(70.6, 20.05), (70.6, 20.1), (70.4, 20.0), (70.8, 19.95),
               (70.2, 20.2), (70.9, 20.0), (71.0, 19.9), (70.5, 19.85),
               (71.7, 20.6), (71.65, 20.55), (71.75, 20.7), (71.6, 20.5),
               (69.95, 20.25)]:
    iy, ix = cell(x, y)
    print(f'  ({x},{y}): viafit={viafit[iy, ix]} ' +
          ' '.join(f'L{l}={G[l][iy, ix]:+.3f}' for l in range(3)),
          flush=True)
    for l in range(3):
        print(f'      worst L{l}: {worst[l][iy, ix]}', flush=True)

print('--- map (rows y=21.2 -> 18.9 step 0.1; cols x=68.3 -> 72.6 '
      'step 0.1) ---', flush=True)
print('legend: V=viafit, B=B-track only, I=In2-track only, '
      'X=both tracks, .=none, S=start, G=goal', flush=True)
for iy in range(len(ys) - 1, -1, -2):
    row = ''
    for ix in range(0, len(xs), 2):
        ch = '.'
        if track[2][iy, ix] and track[1][iy, ix]:
            ch = 'X'
        elif track[2][iy, ix]:
            ch = 'B'
        elif track[1][iy, ix]:
            ch = 'I'
        if viafit[iy, ix]:
            ch = 'V'
        row += ch
    print(f'y={ys[iy]:.2f} {row}', flush=True)
print('done', flush=True)
