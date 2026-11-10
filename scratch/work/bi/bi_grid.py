#!/usr/bin/env python3
"""bi via-lattice grid for the U7 south fanout on exp257.
Fixed obstacles: exp257 items EXCEPT ULPI_NXT/ULPI_DIR escape items
(F stubs + dive vias + first legs) which are being re-fanned.
Grids RST dive via (d0.40) and NXT via (d0.50); DIR via tried at
stock (74.82,18.10) and at (74.72,18.85). Scores = exact referee
margins vs obstacles (all layers); pairwise via-via included.
Also prices a straight F stub from each candidate to its pad."""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bi')
import gridroute as G
from bi_price import m_via, m_trk, BASE

ESC = {  # (net, kind, coords-ish) to exclude: escapes being re-fanned
    ('ULPI_NXT', 'via', (74.940, 17.360)),
    ('ULPI_DIR', 'via', (74.820, 18.100)),
}
ESC_TRK = [
    ('ULPI_NXT', 'F', (75.250, 16.875), (74.940, 17.360)),
    ('ULPI_NXT', 'In2', (74.940, 17.360), (74.100, 17.700)),
    ('ULPI_DIR', 'F', (75.750, 16.875), (75.600, 17.300)),
    ('ULPI_DIR', 'F', (75.600, 17.300), (75.420, 17.950)),
    ('ULPI_DIR', 'F', (75.420, 17.950), (74.820, 18.100)),
    ('ULPI_DIR', 'B', (74.820, 18.100), (73.300, 18.420)),
]


def near(p, q, tol=0.006):
    return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol


pool = []
for it in BASE:
    if it.kind == 'via' and any(it.net == n and near(it.a, at) for n, k, at in ESC):
        continue
    if it.kind == 'trk' and any(it.net == n and it.layer == l and
                                ((near(it.a, a) and near(it.b, b)) or (near(it.a, b) and near(it.b, a)))
                                for n, l, a, b in ESC_TRK):
        continue
    pool.append(it)


def score_via(c, r, net):
    m = m_via(c, r, net, pool)
    return m[0] if m else (9.9, '')


def grid(net, r, xs, ys, pad_from):
    out = []
    y = ys[0]
    while y <= ys[1] + 1e-9:
        x = xs[0]
        while x <= xs[1] + 1e-9:
            c = (round(x, 3), round(y, 3))
            mv, dv = score_via(c, r, net)
            stub = m_trk(pad_from, c, 'F', 0.10, net, pool)
            ms = stub[0][0] if stub else 9.9
            out.append((min(mv, ms), mv, ms, c, dv))
            x += 0.05
        y += 0.05
    out.sort(reverse=True)
    return out


rst = grid('USB_RST', 0.20, (74.40, 74.90), (17.30, 18.00), (74.25, 16.878))
nxtA = grid('ULPI_NXT', 0.25, (74.95, 75.65), (16.95, 18.30), (75.25, 16.875))
nxtB = grid('ULPI_NXT', 0.25, (74.55, 75.30), (18.55, 19.35), (75.25, 16.875))
for name, g in [('RST dive d0.40', rst), ('NXT east', nxtA), ('NXT south', nxtB)]:
    print(f'== {name} top6 (score, viaMargin, stubMargin, at, fence):')
    for s, mv, ms, c, dv in g[:6]:
        print(f'   {s:+.3f} via {mv:+.3f} stub {ms:+.3f} @{c} :: {dv}')
# pairwise: best combos
print('== best pairs (RST x NXT-east / NXT-south), DIR at stock vs (74.72,18.85):')
for dir_at in [(74.82, 18.10), (74.72, 18.85)]:
    dm, _ = score_via(dir_at, 0.25, 'ULPI_DIR')
    for gname, g in [('E', nxtA), ('S', nxtB)]:
        best = None
        for s1, v1, st1, c1, _ in rst[:40]:
            for s2, v2, st2, c2, _ in g[:40]:
                d = math.hypot(c1[0] - c2[0], c1[1] - c2[1])
                pair = d - 0.20 - 0.25 - 0.20
                dd = min(math.hypot(c1[0] - dir_at[0], c1[1] - dir_at[1]) - 0.45 - 0.20,
                         math.hypot(c2[0] - dir_at[0], c2[1] - dir_at[1]) - 0.50 - 0.20)
                tot = min(s1, s2, pair, dd, dm)
                if best is None or tot > best[0]:
                    best = (tot, c1, c2)
        print(f'   DIR@{dir_at} NXT-{gname}: worst {best[0]:+.3f} RST@{best[1]} NXT@{best[2]} (DIR via margin {dm:+.3f})')
