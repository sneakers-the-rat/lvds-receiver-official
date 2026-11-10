"""t_az4: flood-fill reachability for the 3 open nets on exp251 as-built.
From each net's smallest fragment, flood the A* passability model
(track cells: foreign field >= hw; via transitions: all-layer field
>= 0.25). Reports per other fragment: reached?, else the exact gap
and the foreign items fencing the narrowest strait.
Box x[64,92] y[0,26], step 0.125. Faithful pool via t_ax0_pre."""
import sys, math
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
import numpy as np
from collections import deque
from t_ax0_pre import *  # noqa
import t_ai_lib as L
from router import netclass, dist_to_item

pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')

X0, X1, Y0, Y1, STEP = 64.0, 92.0, 0.0, 26.0, 0.125
xs = np.arange(X0, X1 + 1e-9, STEP)
ys = np.arange(Y0, Y1 + 1e-9, STEP)
GX, GY = np.meshgrid(xs, ys)
NY, NX = GX.shape

def df_grid(it):
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

def bb(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        r = math.hypot(d[2], d[3])
        return d[0] - r, d[0] + r, d[1] - r, d[1] + r
    if kind == 'seg':
        return (min(d[0], d[2]) - d[4], max(d[0], d[2]) + d[4],
                min(d[1], d[3]) - d[4], max(d[1], d[3]) + d[4])
    return d[0] - d[2], d[0] + d[2], d[1] - d[2], d[1] + d[2]

def item_pts(it):
    """Sample points on an item (for fragment/gap analysis)."""
    kind, d = it[0], it[2]
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.25) + 1)
        return [(x1 + (x2 - x1) * i / (n - 1), y1 + (y2 - y1) * i / (n - 1))
                for i in range(n)]
    return [(d[0], d[1])]

for net in ('PHY_1V8', 'XI', 'USB_RST'):
    myclr = netclass(net)[1]
    frags = fragments(net, (X0, X1, Y0, Y1))
    print(f'##### {net}: {len(frags)} fragments in box')
    for i, fr in enumerate(frags):
        desc = [L.fmt_it(it) for (_, it) in fr[:4]]
        print(f'  frag{i}: {len(fr)} items: {desc}')
    # identify fragments by a signature item
    fields, ownd = {}, {}
    for l in range(3):
        f = np.full(GX.shape, 9.9)
        o = np.full(GX.shape, 9.9)
        for it in pool[l]:
            a, b, c2, d2 = bb(it)
            if b < X0 - 1 or a > X1 + 1 or d2 < Y0 - 1 or c2 > Y1 + 1:
                continue
            if it[1] == net:
                o = np.minimum(o, df_grid(it))
                continue
            req = max(myclr, it[3])
            f = np.minimum(f, df_grid(it) - req)
        fields[l] = f
        ownd[l] = o
    track = {l: fields[l] >= 0.10 for l in range(3)}
    viafit = np.minimum(np.minimum(fields[0], fields[1]),
                        fields[2]) >= 0.25
    # start fragment = the one NOT containing the 'main' anchor pad
    anchor = {'PHY_1V8': (77.25, 16.4375), 'XI': (85.75, 18.25),
              'USB_RST': (74.75, 4.662)}[net]
    start_frag = None
    for i, fr in enumerate(frags):
        has_anchor = any(abs(p[0] - anchor[0]) < 0.3
                         and abs(p[1] - anchor[1]) < 0.3
                         for (_, it) in fr for p in item_pts(it))
        if not has_anchor and start_frag is None:
            start_frag = i
    print(f'  start fragment: {start_frag}')
    seen = {l: np.zeros(GX.shape, dtype=bool) for l in range(3)}
    dq = deque()
    for l in range(3):
        cells = np.argwhere((ownd[l] <= 0.30) & track[l])
        for iy, ix in cells:
            if not seen[l][iy, ix]:
                seen[l][iy, ix] = True
                dq.append((l, iy, ix))
    while dq:
        l, iy, ix = dq.popleft()
        for l2 in range(3):
            if l2 != l and viafit[iy, ix] and track[l2][iy, ix] \
                    and not seen[l2][iy, ix]:
                seen[l2][iy, ix] = True
                dq.append((l2, iy, ix))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                jy, jx = iy + dy, ix + dx
                if 0 <= jy < NY and 0 <= jx < NX and track[l][jy, jx] \
                        and not seen[l][jy, jx]:
                    seen[l][jy, jx] = True
                    dq.append((l, jy, jx))
    for l in range(3):
        ys_s, xs_s = np.where(seen[l])
        if len(xs_s):
            print(f'  reached L{l}: x[{xs[xs_s].min():.2f},{xs[xs_s].max():.2f}]'
                  f' y[{ys[ys_s].min():.2f},{ys[ys_s].max():.2f}]'
                  f' cells={len(xs_s)}')
    # gap analysis to every other fragment
    reached_pts = []
    for l in range(3):
        ys_s, xs_s = np.where(seen[l])
        reached_pts += [(l, xs[ix], ys[iy]) for iy, ix in zip(ys_s, xs_s)]
    for i, fr in enumerate(frags):
        if i == start_frag:
            continue
        pts = [(l, p[0], p[1]) for (l, it) in fr for p in item_pts(it)]
        best = (1e9, None, None)
        for (l, px, py) in pts:
            if seen[l][int(round((py - Y0) / STEP)),
                      int(round((px - X0) / STEP))]:
                best = (0.0, (l, px, py), None)
                break
            for (rl, rx, ry) in reached_pts:
                if rl != l:
                    continue
                d = math.hypot(px - rx, py - ry)
                if d < best[0]:
                    best = (d, (l, px, py), (rl, rx, ry))
        print(f'  frag{i}: {"REACHED" if best[0] == 0 else "gap %.3f" % best[0]}'
              f' closest={best[1]} from={best[2]}')
        if 0 < best[0] < 1e8:
            (l, px, py), (_, rx, ry) = best[1], best[2]
            mx, my = (px + rx) / 2, (py + ry) / 2
            print(f'    strait mid ({mx:.3f},{my:.3f}) L{l}; fence items'
                  f' within 0.75mm of the strait segment:')
            for l2 in range(3):
                for it in pool[l2]:
                    if it[1] == net:
                        continue
                    # distance from item to segment (rx,ry)-(px,py)
                    d = it[2]
                    # coarse centre distance first
                    cx, cy = C(it)
                    if math.hypot(cx - mx, cy - my) > 2.5:
                        continue
                    # exact: min distance from item to the segment pts
                    segd = 1e9
                    for t in np.linspace(0, 1, 9):
                        qx, qy = rx + (px - rx) * t, ry + (py - ry) * t
                        segd = min(segd, dist_to_item(it, qx, qy))
                    if segd < 0.75:
                        print(f'      L{l2} {L.fmt_it(it)} clr={it[3]}'
                              f' dist-to-strait={segd:.3f}')
    sys.stdout.flush()
print('=== done ===')
