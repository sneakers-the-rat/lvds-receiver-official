#!/usr/bin/env python3
"""bh design pricer v2: the full USB_RST composite on exp257.
- ULPI_CK via -> (75.45,6.05); F sag escape; In2 SOUTH BOW escape
  (75.45,6.05)->(75.35,6.95)->(74.95,7.45)->(74.625,7.35); CK column
  re-based at y7.35 (rip 6.375->9.4 seg, re-add 7.35->9.4).
- BIST window dy=-0.049; SPI_MOSI seg dy=-0.014.
- USB_RST: dive via U7.9 (74.25,16.438); In2 -> (74.55,15.7) ->
  via (75.05,14.2); B jog -> via (75.45,12.85); In2 corridor x75.45/
  x75.07 south -> bend west -> surface via (74.83,5.78); F hop into
  U6.40 pad end (74.78,5.30).
Prices every new element vs the transformed pool under BOTH rule
sets: gridroute (In2-In2 0.30) and referee (KiCad 0.20/0.25 edge)."""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
OUT = '/home/hatch/workspace/pdlvds-route/scratch/work/bh/design_bh2_out.txt'
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


def clr_ref(item_net, layer, item_layer):
    return 0.25 if G.is_power(item_net) else 0.20


def margins(a, b, layer, hw, pool, skip, mode):
    """mode 'ref': referee clr for trk-trk; 'grid': gridroute pair_clr.
    Returns worst (margin, desc)."""
    worst = (9.9, '')
    x0, x1 = min(a[0], b[0]) - 1.3, max(a[0], b[0]) + 1.3
    y0, y1 = min(a[1], b[1]) - 1.3, max(a[1], b[1]) + 1.3
    for it in pool:
        if it.net == skip:
            continue
        pts = [it.a] if it.kind == 'via' else ([it.a, it.b] if it.kind == 'trk'
               else [(it.rect[0], it.rect[1]), (it.rect[2], it.rect[3])])
        if not any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in pts):
            continue
        if it.kind == 'via':
            m = pt_seg(it.a, a, b) - hw - it.hw - G.via_clr(it.net)
            d = f'via {it.net}@{it.a}'
        elif it.kind == 'trk' and it.layer == layer:
            c = G.pair_clr(it.net, layer, it.layer) if mode == 'grid' else clr_ref(it.net, layer, it.layer)
            m = seg_seg(a, b, it.a, it.b) - hw - it.hw - c
            d = f'trk {it.net} {it.a}->{it.b}'
        elif it.kind == 'pad' and it.layer == layer:
            c = G.pair_clr(it.net, layer, layer) if mode == 'grid' else clr_ref(it.net, layer, layer)
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
        pts = [it.a] if it.kind == 'via' else ([it.a, it.b] if it.kind == 'trk'
               else [(it.rect[0], it.rect[1]), (it.rect[2], it.rect[3])])
        if not any(abs(p[0] - c[0]) < 1.3 and abs(p[1] - c[1]) < 1.3 for p in pts):
            continue
        if it.kind == 'via':
            m = math.hypot(c[0] - it.a[0], c[1] - it.a[1]) - r - it.hw - G.via_clr(it.net)
            d = f'via {it.net}@{it.a}'
        elif it.kind == 'trk':
            m = pt_seg(c, it.a, it.b) - r - it.hw - G.via_clr(it.net)
            d = f'trk[{it.layer}] {it.net} {it.a}->{it.b}'
        else:
            m = pt_rect(c, it.rect) - r - G.via_clr(it.net)
            d = f'pad[{it.layer}] {it.net} {it.rect}'
        if m < worst[0]:
            worst = (m, d)
    return worst


def close(p, q, tol=0.03):
    return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol


def seg_is(it, net, layer, a, b):
    return it.net == net and it.kind == 'trk' and it.layer == layer and \
        ((close(it.a, a) and close(it.b, b)) or (close(it.a, b) and close(it.b, a)))


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


def trk(net, layer, a, b, w):
    return G.Item(net, 'trk', layer=layer, a=a, b=b, hw=w / 2)


def via(net, c, d):
    return G.Item(net, 'via', a=c, hw=d / 2)


ADDS = []  # (label, item)
def add_poly(net, layer, pts, w, label):
    for a, b in zip(pts, pts[1:]):
        ADDS.append((f'{label} {a}->{b}', trk(net, layer, a, b, w)))


add_poly('ULPI_CK', 'F', [(75.25, 5.162), (75.22, 5.6), (75.45, 6.05)], 0.20, 'CK-F')
ADDS.append(('CK via', via('ULPI_CK', (75.45, 6.05), 0.6)))
add_poly('ULPI_CK', 'In2', [(75.45, 6.05), (75.35, 6.95), (74.95, 7.45), (74.625, 7.35)], 0.25, 'CK-bow')
add_poly('ULPI_CK', 'In2', [(74.625, 7.35), (74.625, 9.4)], 0.25, 'CK-col')
bist_pts = [(x, y - 0.049) if 0 < i < len(BIST_WIN) - 1 else (x, y)
            for i, (x, y) in enumerate(BIST_WIN)]
add_poly('BIST_DRV', 'In2', bist_pts, 0.25, 'BIST')
add_poly('SPI_MOSI', 'In2', [(71.9, 7.25), (73.4, 5.186), (75.1, 4.536), (76.4, 3.35)], 0.20, 'MOSI')
ADDS.append(('RST dive via', via('USB_RST', (74.25, 16.438), 0.5)))
add_poly('USB_RST', 'In2', [(74.25, 16.438), (74.55, 15.7), (75.05, 14.2)], 0.20, 'RST-N')
ADDS.append(('RST via N', via('USB_RST', (75.05, 14.2), 0.5)))
add_poly('USB_RST', 'B', [(75.05, 14.2), (75.45, 12.85)], 0.20, 'RST-Bjog')
ADDS.append(('RST via S', via('USB_RST', (75.45, 12.85), 0.5)))
add_poly('USB_RST', 'In2', [(75.45, 12.85), (75.45, 9.6), (75.07, 9.3), (75.07, 7.05),
                            (74.72, 6.55), (74.5, 6.05), (74.83, 5.78)], 0.20, 'RST-corridor')
ADDS.append(('RST surface via', via('USB_RST', (74.83, 5.78), 0.5)))
add_poly('USB_RST', 'F', [(74.83, 5.78), (74.78, 5.50), (74.78, 5.30)], 0.20, 'RST-hop')

pool = [it for it in BASE if not is_rip(it)] + [it for _, it in ADDS]
rows = []
for label, it in ADDS:
    if it.kind == 'via':
        m, d = margin_via(it.a, it.hw, pool, it.net)
        rows.append((m, m, label, d))
    else:
        mg, dg = margins(it.a, it.b, it.layer, it.hw, pool, it.net, 'grid')
        mr, dr = margins(it.a, it.b, it.layer, it.hw, pool, it.net, 'ref')
        rows.append((mg, mr, label, f'grid:{dg} | ref:{dr}'))
rows.sort()
with open(OUT, 'w') as f:
    for mg, mr, label, d in rows:
        f.write(f'grid {mg:+.3f} ref {mr:+.3f}  {label}  :: {d}\n')
print('worst 14 (grid | ref):')
for mg, mr, label, d in rows[:14]:
    print(f'  {mg:+.3f} {mr:+.3f}  {label} :: {d[:95]}')
