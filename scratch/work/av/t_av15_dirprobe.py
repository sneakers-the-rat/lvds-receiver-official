"""t_av15: probe ULPI_DIR B field for the tail re-lay, exact state."""
import wx
_app = wx.App(False)
import sys, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av15'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
import t_ai_lib as L
import numpy as np

R2 = lambda v: round(v, 3)
STUB = (73.875, 11.625, 73.875, 12.875)
VERT = (73.875, 12.875, 73.875, 16.375)
for it in list(pool[1]):
    if it[0] == 'seg' and it[1] == 'RBIAS':
        rg = tuple(R2(v) for v in it[2])
        if rg not in (STUB, VERT):
            pool[1].remove(it)
# C49 move (pads only; web journey irrelevant to B field fences
# except its B items - include none: web was A* multi-layer; to be
# safe this probe only checks the B field with dummies, matching
# t_av13's state approximately: DIR seg still present here is
# REMOVED as in t_av13)
for it in list(pool[2]):
    if it[0] == 'seg' and it[1] == 'ULPI_DIR' and \
            tuple(R2(v) for v in it[2]) == (71.375, 19.125, 68.875,
                                            29.0, 0.1):
        pool[2].remove(it)
        print('DIR seg removed', flush=True)
DUM = 'BLOCK_RSVD'
for l in range(3):
    pool[l].append(('via', DUM, (70.45, 20.25, 0.35), 0.2))
pool[2].append(('seg', DUM, (71.875, 19.625, 70.45, 20.25, 0.15), 0.2))

NET = 'ULPI_DIR'
myclr = L.netclass(NET)[1]
box = (68.3, 72.2, 18.6, 29.6)
X0, X1, Y0, Y1 = box
step = 0.05
xs = np.arange(X0, X1 + 1e-9, step)
ys = np.arange(Y0, Y1 + 1e-9, step)
GX, GY = np.meshgrid(xs, ys)


def dfun(it):
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


f = np.full(GX.shape, 9.9)
w = np.full(GX.shape, '', dtype=object)
for it in pool[2]:
    if it[1] == NET:
        continue
    req = max(myclr, it[3])
    cand = dfun(it) - req
    upd = cand < f
    f = np.where(upd, cand, f)
    w = np.where(upd, L.fmt_it(it), w)
track = f >= 0.10


def cell(x, y):
    return (int(round((y - Y0) / step)), int(round((x - X0) / step)))


for name, (x, y) in (('start', (71.375, 19.125)),
                     ('goal', (68.875, 29.0))):
    iy, ix = cell(x, y)
    print(f'{name} ({x},{y}): field={f[iy, ix]:+.3f} '
          f'track={track[iy, ix]} worst={w[iy, ix]}', flush=True)

print('--- B track map (y 29.6 -> 18.6 step 0.2, x 68.3 -> 72.2 '
      'step 0.1) ---', flush=True)
for iy in range(len(ys) - 1, -1, -4):
    row = ''
    for ix in range(0, len(xs), 2):
        row += ('#' if track[iy, ix] else '.')
    print(f'y={ys[iy]:.1f} {row}', flush=True)
print('done', flush=True)
