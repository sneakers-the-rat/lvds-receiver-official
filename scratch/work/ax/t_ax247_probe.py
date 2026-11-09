import sys, math
import numpy as np
sys.path.insert(0, 'scratch/work/ax')

# exec the t_ax246 prep (everything before the stage loop) verbatim
src = open('scratch/work/ax/t_ax246_design214ad.py').read()
head = src.split("\nbox = (64.0")[0]
exec(head)

# ---- 1. dump In2 items intersecting the rounding region ----
RX0, RX1, RY0, RY1 = 66.5, 71.5, -6.2, -2.3
print('=== In2 items in rounding region ===', flush=True)
for it in pool[1]:
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy = d[0], d[1]
        if RX0 - 1 < cx < RX1 + 1 and RY0 - 1 < cy < RY1 + 1:
            print('  ', L.fmt_it(it), flush=True)
    elif kind == 'seg':
        if max(d[0], d[2]) >= RX0 - 1 and min(d[0], d[2]) <= RX1 + 1 \
           and max(d[1], d[3]) >= RY0 - 1 and min(d[1], d[3]) <= RY1 + 1:
            print('  ', L.fmt_it(it), flush=True)
    else:
        if RX0 - 1 < d[0] < RX1 + 1 and RY0 - 1 < d[1] < RY1 + 1:
            print('  ', L.fmt_it(it), flush=True)

# ---- 2. G[1] field map over the region (replicates make_astar df) ----
step = 0.05
xs = np.arange(67.6, 70.45, step)
ys = np.arange(-5.9, -2.9, step)
GX, GY = np.meshgrid(xs, ys)


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


f = np.full(GX.shape, 9.9)
for it in pool[1]:
    if it[1] == 'ULPI_STP':
        continue
    req = max(0.2, it[3])
    f = np.minimum(f, df_of(it, GX, GY) - req)
print('=== G[1] map (x 67.6..70.4 step .05; # <0.10 dead, + 0.10-0.34, '
      '. >=0.35) ===', flush=True)
hdr = '      ' + ''.join(str(int(round(x * 10)) % 10) for x in xs)
print(hdr, flush=True)
for j in range(len(ys) - 1, -1, -1):
    row = ''
    for i in range(len(xs)):
        g = f[j, i]
        row += '#' if g < 0.10 else ('+' if g < 0.35 else '.')
    print(f'{ys[j]:6.2f}' + row, flush=True)

# ---- 3. culprit at key cells ----
def culprit(x, y):
    best, who = 9.9, None
    for it in pool[1]:
        if it[1] == 'ULPI_STP':
            continue
        req = max(0.2, it[3])
        v = float(df_of(it, np.array([[x]]), np.array([[y]]))[0, 0]) - req
        if v < best:
            best, who = v, it
    print(f'  cell ({x},{y}): G={best:+.3f} culprit {L.fmt_it(who)}',
          flush=True)


print('=== culprits ===', flush=True)
for (x, y) in ((69.65, -3.6), (68.45, -4.75), (69.3, -4.6), (69.0, -4.9),
               (68.7, -4.9), (68.45, -5.2), (68.9, -4.4), (69.5, -4.3)):
    culprit(x, y)

# ---- 4. single-stage A* tests on a tight box ----
box = (67.0, 71.2, -6.2, -1.5)
tests = [
    (((1,), 69.65, -3.6), (1, 68.45, -4.75)),   # sanity: known NONE
    (((1,), 69.65, -3.6), (1, 69.3, -4.95)),    # south lane east of chain end
    (((1,), 69.65, -3.6), (1, 68.9, -5.2)),     # deeper south
    (((1,), 69.65, -3.6), (1, 68.3, -4.9)),     # SW corner direct
    (((1,), 69.3, -4.95), (1, 68.45, -4.75)),   # west along the south lane
    (((1,), 68.3, -4.9), (1, 68.3, -3.9)),      # north return, west side
    (((1,), 68.45, -4.75), (1, 68.3, -3.9)),    # original stage 18
    (((1,), 68.3, -3.9), (1, 68.6, -2.0)),      # original stage 19
    (((1,), 68.6, -2.0), (0, 71.3375, -2.25)),  # original stage 20 (F pad)
]
for s, g in tests:
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', s, g, hw=0.10)
    print(f'A* {s} -> {g}:', 'FOUND' if J else 'NONE',
          ('vias=' + str(J['vias'])) if J else '', flush=True)
print('PROBE DONE', flush=True)
