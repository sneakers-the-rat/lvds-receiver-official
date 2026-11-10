#!/usr/bin/env python3
"""bh design pricer v3: USB_RST composite, west-B journey variant.
Arrival: CK via -> (75.42,6.12) d0.6, F escape via (75.33,5.62), In2 bow
(75.05,6.6)/(74.7,7.0) joining re-based column at (74.625,7.35);
RST surface via (74.82,5.84) d0.40 + F hop into U6.40 south end.
Shifts: BIST window dy=-0.049; MOSI seg dy=-0.014; I2C_SCL B corner
pieces (-0.035,+0.035); RBIAS In2 top section dx=-0.30 (for the dive).
Journey: dive via at U7.9 pad -> B west -> north column -> east leg ->
NE into the surface via. net='' pads priced on F only (loader artifact
on inner layers: banked CK horizontal threads them on In2, DRC clean).
Prices all new elements vs transformed pool, referee rules + gridroute
rules for tracks."""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
OUT = '/home/hatch/workspace/pdlvds-route/scratch/work/bh/design_bh3_out.txt'
BASE = G.load_items(BOARD)


def pt_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def seg_seg(a, b, c, d):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2 = orient(a, b, c), orient(a, b, d)
    o3, o4 = orient(c, d, a), orient(c, d, b)
    if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0):
        return 0.0
    return min(pt_seg(a, c, d), pt_seg(b, c, d), pt_seg(c, a, b), pt_seg(d, a, b))


def pt_rect(p, r):
    x0, y0, x1, y1 = r
    return math.hypot(max(x0 - p[0], 0.0, p[0] - x1), max(y0 - p[1], 0.0, p[1] - y1))


def seg_rect(a, b, r):
    x0, y0, x1, y1 = r
    if (x0 <= a[0] <= x1 and y0 <= a[1] <= y1) or (x0 <= b[0] <= x1 and y0 <= b[1] <= y1):
        return 0.0
    edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
             ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    if any(seg_seg(a, b, e0, e1) == 0.0 for e0, e1 in edges):
        return 0.0
    return min(pt_rect(a, r), pt_rect(b, r),
               min(pt_seg(c, a, b) for c in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))


def clr_ref(item_net):
    return 0.25 if G.is_power(item_net) else 0.20


def margins(a, b, layer, hw, pool, skip, mode):
    worst = (9.9, '')
    x0, x1 = min(a[0], b[0]) - 1.3, max(a[0], b[0]) + 1.3
    y0, y1 = min(a[1], b[1]) - 1.3, max(a[1], b[1]) + 1.3
    for it in pool:
        if it.net == skip:
            continue
        if it.kind == 'pad' and it.net == '' and layer != 'F':
            continue
        pts = [it.a] if it.kind == 'via' else ([it.a, it.b] if it.kind == 'trk'
               else [(it.rect[0], it.rect[1]), (it.rect[2], it.rect[3])])
        if not any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in pts):
            continue
        if it.kind == 'via':
            m = pt_seg(it.a, a, b) - hw - it.hw - G.via_clr(it.net)
            d = f'via {it.net}@{it.a}'
        elif it.kind == 'trk' and it.layer == layer:
            c = G.pair_clr(it.net, layer, it.layer) if mode == 'grid' else clr_ref(it.net)
            m = seg_seg(a, b, it.a, it.b) - hw - it.hw - c
            d = f'trk {it.net} {it.a}->{it.b}'
        elif it.kind == 'pad' and it.layer == layer:
            c = G.pair_clr(it.net, layer, layer) if mode == 'grid' else clr_ref(it.net)
            m = seg_rect(a, b, it.rect) - hw - c
            d = f'pad {it.net} {it.rect}'
        else:
            continue
        if m < worst[0]:
            worst = (m, d)
    return worst


def margin_via(c, r, pool, skip):
    worst = (9.9, '')
    for it in pool:
        if it.net == skip:
            continue
        if it.kind == 'pad' and it.net == '':
            layers = [it.layer]
            if 'F' not in layers:
                continue
        pts = [it.a] if it.kind == 'via' else ([it.a, it.b] if it.kind == 'trk'
               else [(it.rect[0], it.rect[1]), (it.rect[2], it.rect[3])])
        if not any(abs(p[0] - c[0]) < 1.4 and abs(p[1] - c[1]) < 1.4 for p in pts):
            continue
        if it.kind == 'via':
            m = math.hypot(c[0] - it.a[0], c[1] - it.a[1]) - r - it.hw - G.via_clr(it.net)
            d = f'via {it.net}@{it.a}'
        elif it.kind == 'trk':
            m = pt_seg(c, it.a, it.b) - r - it.hw - G.via_clr(it.net)
            d = f'trk[{it.layer}] {it.net} {it.a}->{it.b}'
        else:
            if it.layer != 'F':
                continue
            m = pt_rect(c, it.rect) - r - G.via_clr(it.net)
            d = f'pad[F] {it.net} {it.rect}'
        if m < worst[0]:
            worst = (m, d)
    return worst


def close(p, q, tol=0.03):
    return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol


def seg_is(it, net, layer, a, b):
    return it.net == net and it.kind == 'trk' and it.layer == layer and \
        ((close(it.a, a) and close(it.b, b)) or (close(it.a, b) and close(it.b, a)))


def trk(net, layer, a, b, w):
    return G.Item(net, 'trk', layer=layer, a=a, b=b, hw=w / 2)


def via(net, c, d):
    return G.Item(net, 'via', a=c, hw=d / 2)


# ---- window shifts on the BASE pool (densified chains) ----
def window_shift(pool, net, layer, box, dx, dy):
    """Rip segs of net/layer with both endpoints in box; re-add shifted;
    add connectors at boundary vertices (endpoints shared with survivors).
    Returns (new_pool, n_ripped, n_boundary)."""
    x0, y0, x1, y1 = box
    def inbox(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    ripped, surv = [], []
    for it in pool:
        if it.net == net and it.kind == 'trk' and it.layer == layer and \
           inbox(it.a) and inbox(it.b):
            ripped.append(it)
        else:
            surv.append(it)
    surv_pts = set()
    for it in surv:
        if it.net == net and it.kind == 'trk' and it.layer == layer:
            surv_pts.add((round(it.a[0], 3), round(it.a[1], 3)))
            surv_pts.add((round(it.b[0], 3), round(it.b[1], 3)))
    out = list(surv)
    boundary = []
    for it in ripped:
        na, nb = (it.a[0] + dx, it.a[1] + dy), (it.b[0] + dx, it.b[1] + dy)
        out.append(trk(net, layer, na, nb, it.hw * 2))
        for p, np_ in ((it.a, na), (it.b, nb)):
            if (round(p[0], 3), round(p[1], 3)) in surv_pts:
                boundary.append((p, np_))
    for p, np_ in boundary:
        out.append(trk(net, layer, p, np_, 0.25 if net != 'SPI_MOSI' else 0.20))
    return out, len(ripped), len(boundary)


RIPS = [
    ('ULPI_CK', 'via', (75.125, 5.875), None),
    ('ULPI_CK', 'F', (75.125, 5.875), (75.25, 5.162)),
    ('ULPI_CK', 'In2', (74.875, 6.125), (75.125, 5.875)),
    ('ULPI_CK', 'In2', (74.625, 6.375), (74.875, 6.125)),
    ('ULPI_CK', 'In2', (74.625, 6.375), (74.625, 9.4)),
    ('SPI_MOSI', 'In2', (73.4, 5.2), (75.1, 4.55)),
]
BIST_WIN = [(73.875, 6.125), (74.125, 5.875), (74.375, 5.625),
            (74.625, 5.375), (74.875, 5.125), (75.375, 5.125), (75.625, 4.875)]
for a, b in zip(BIST_WIN, BIST_WIN[1:]):
    RIPS.append(('BIST_DRV', 'In2', a, b))


def is_rip(it):
    for net, kind, a, b in RIPS:
        if it.net != net:
            continue
        if kind == 'via' and it.kind == 'via' and close(it.a, a):
            return True
        if kind != 'via' and seg_is(it, net, kind, a, b):
            return True
    return False


pool = [it for it in BASE if not is_rip(it)]
pool, n1, b1 = window_shift(pool, 'RBIAS', 'In2', (73.40, 15.82, 74.10, 16.80), -0.30, 0.0)
pool, n2, b2 = window_shift(pool, 'I2C_SCL', 'B', (74.30, 6.00, 74.95, 6.75), -0.035, 0.035)
print(f'shifts: RBIAS ripped {n1} boundary {b1}; SCL ripped {n2} boundary {b2}')

ADDS = []
def add_poly(net, layer, pts, w, label):
    for a, b in zip(pts, pts[1:]):
        ADDS.append((f'{label} {a}->{b}', trk(net, layer, a, b, w)))


add_poly('ULPI_CK', 'F', [(75.25, 5.162), (75.33, 5.62), (75.42, 6.12)], 0.20, 'CK-F')
ADDS.append(('CK via', via('ULPI_CK', (75.42, 6.12), 0.6)))
add_poly('ULPI_CK', 'In2', [(75.42, 6.12), (75.05, 6.6), (74.7, 7.0), (74.625, 7.35)], 0.25, 'CK-bow')
add_poly('ULPI_CK', 'In2', [(74.625, 7.35), (74.625, 9.4)], 0.25, 'CK-col')
bist_pts = [(x, y - 0.049) if 0 < i < len(BIST_WIN) - 1 else (x, y)
            for i, (x, y) in enumerate(BIST_WIN)]
add_poly('BIST_DRV', 'In2', bist_pts, 0.25, 'BIST')
add_poly('SPI_MOSI', 'In2', [(71.9, 7.25), (73.4, 5.186), (75.1, 4.536), (76.4, 3.35)], 0.20, 'MOSI')
ADDS.append(('RST surface via', via('USB_RST', (74.82, 5.84), 0.4)))
add_poly('USB_RST', 'F', [(74.82, 5.84), (74.78, 5.50), (74.78, 5.30)], 0.20, 'RST-hop')
ADDS.append(('RST dive via', via('USB_RST', (74.25, 16.438), 0.5)))
# journey variants on B: (west column x, east-leg y)
JOURNEYS = {
    'J1': [(74.25, 16.438), (73.6, 16.95), (68.3, 16.95), (68.3, 4.62),
           (74.3, 4.62), (74.82, 5.84)],
    'J2': [(74.25, 16.438), (73.6, 16.95), (67.9, 16.95), (67.9, 4.75),
           (74.3, 4.75), (74.82, 5.84)],
    'J3': [(74.25, 16.438), (73.6, 16.95), (68.7, 16.95), (68.7, 4.5),
           (74.3, 4.5), (74.82, 5.84)],
}
pool_all = pool + [it for _, it in ADDS]
rows = []
for label, it in ADDS:
    if it.kind == 'via':
        m, d = margin_via(it.a, it.hw, pool_all, it.net)
        rows.append((m, m, label, d))
    else:
        mg, dg = margins(it.a, it.b, it.layer, it.hw, pool_all, it.net, 'grid')
        mr, dr = margins(it.a, it.b, it.layer, it.hw, pool_all, it.net, 'ref')
        rows.append((mg, mr, label, f'grid:{dg} | ref:{dr}'))
# shifted neighbours priced as their new items
for net, layer in (('RBIAS', 'In2'), ('I2C_SCL', 'B')):
    pass  # priced implicitly: they are in pool; their own-net skip hides self-binds;
    # cross-binds appear in the ADDS rows and in a dedicated check below.
for jn, pts in JOURNEYS.items():
    jitems = []
    for a, b in zip(pts, pts[1:]):
        jitems.append(trk('USB_RST', 'B', a, b, 0.20))
    jp = pool_all + jitems
    for it in jitems:
        mg, dg = margins(it.a, it.b, 'B', it.hw, jp, 'USB_RST', 'grid')
        mr, dr = margins(it.a, it.b, 'B', it.hw, jp, 'USB_RST', 'ref')
        rows.append((mg, mr, f'{jn} {it.a}->{it.b}', f'grid:{dg} | ref:{dr}'))
rows.sort()
with open(OUT, 'w') as f:
    for mg, mr, label, d in rows:
        f.write(f'grid {mg:+.3f} ref {mr:+.3f}  {label}  :: {d}\n')
print('worst 16 (grid | ref):')
for mg, mr, label, d in rows[:16]:
    print(f'  {mg:+.3f} {mr:+.3f}  {label} :: {d[:100]}')
