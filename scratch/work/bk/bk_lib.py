#!/usr/bin/env python3
"""bk common: exp257 item pool minus composite rips, plus fixed adds.
Composite BK-A:
 - DM_PHY F loop re-lay west (nudged past bj v2)
 - USB_RST: F stub -> dive via (74.45,18.25) -> In2 west-channel journey
   (RBIAS column shifted -0.30, RBIAS via -> (73.48,10.82), thread between
   RBIAS-via disc and CK jog endpoint, CK jog KEPT) -> diagonal into
   bh arrival: surf via (74.82,5.84) d0.4, F hop; CK via -> (75.42,6.12) d0.5
 - +3V3A west via (73.625,10.625) DELETED; U7.25 F feed re-laid east to
   existing +3V3A via (75.625,8.625); B vertical + B diagonal ripped
 - BIST/MOSI/SCL nudges per bh/bj
DIR/NXT fanout is priced separately (bk_fanout.py) on this pool.
Referee margins: 0.20 / 0.25 power (gridroute is_power)."""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
items = G.load_items(BOARD)


def ref_clr(net):
    return 0.25 if G.is_power(net) else 0.20


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


def m_trk(a, b, layer, hw, net, pool):
    worst = (9.9, '')
    for it in pool:
        if it.net == net:
            continue
        if it.kind == 'via':
            m = pt_seg(it.a, a, b) - hw - it.hw - ref_clr(it.net)
            d = f'via {it.net}@{it.a}'
        elif it.kind == 'trk' and it.layer == layer:
            m = seg_seg(a, b, it.a, it.b) - hw - it.hw - ref_clr(it.net)
            d = f'trk[{layer}] {it.net} {it.a}->{it.b}'
        elif it.kind == 'pad' and it.layer == layer:
            m = seg_rect(a, b, it.rect) - hw - ref_clr(it.net)
            d = f'pad {it.net} {it.rect}'
        else:
            continue
        if m < worst[0]:
            worst = (m, d)
    return worst


def m_via(c, r, net, pool):
    worst = (9.9, '')
    for it in pool:
        if it.net == net:
            continue
        if it.kind == 'via':
            m = math.hypot(c[0] - it.a[0], c[1] - it.a[1]) - r - it.hw - ref_clr(it.net)
            d = f'via {it.net}@{it.a}'
        elif it.kind == 'trk':
            m = pt_seg(c, it.a, it.b) - r - it.hw - ref_clr(it.net)
            d = f'trk[{it.layer}] {it.net} {it.a}->{it.b}'
        elif it.kind == 'pad':
            m = pt_rect(c, it.rect) - r - ref_clr(it.net)
            d = f'pad[{it.layer}] {it.net} {it.rect}'
        else:
            continue
        if m < worst[0]:
            worst = (m, d)
    return worst


def near(p, q, tol=0.03):
    return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol


def find_trk(net, layer, a, b):
    return [it for it in items if it.net == net and it.kind == 'trk' and it.layer == layer
            and ((near(it.a, a) and near(it.b, b)) or (near(it.a, b) and near(it.b, a)))]


def find_via(net, c):
    return [it for it in items if it.net == net and it.kind == 'via' and near(it.a, c)]


# ---------------- rips ----------------
RIPS = []
def rip_trk(net, layer, a, b):
    RIPS.append(('trk', net, layer, a, b))
def rip_via(net, c):
    RIPS.append(('via', net, None, c, None))

# DM F loop west part (keep via (73.625,19.125) + north vertical)
rip_trk('DM_PHY', 'F', (74.125, 18.625), (74.125, 17.375))
rip_trk('DM_PHY', 'F', (74.125, 17.375), (73.562, 17.000))
rip_trk('DM_PHY', 'F', (73.875, 18.875), (74.125, 18.625))
rip_trk('DM_PHY', 'F', (73.625, 19.125), (73.875, 18.875))
# DIR U7 escape
rip_trk('ULPI_DIR', 'F', (75.750, 16.875), (75.600, 17.300))
rip_trk('ULPI_DIR', 'F', (75.600, 17.300), (75.420, 17.950))
rip_trk('ULPI_DIR', 'F', (75.420, 17.950), (74.820, 18.100))
rip_via('ULPI_DIR', (74.820, 18.100))
rip_trk('ULPI_DIR', 'B', (74.820, 18.100), (73.300, 18.420))
# NXT U7 escape
rip_trk('ULPI_NXT', 'F', (75.250, 16.875), (74.940, 17.360))
rip_via('ULPI_NXT', (74.940, 17.360))
rip_trk('ULPI_NXT', 'In2', (74.940, 17.360), (74.100, 17.700))
rip_trk('ULPI_NXT', 'In2', (74.100, 17.700), (74.500, 19.250))
# CK arrival (bh): via + F escape + In2 foot + column seg to 9.4 (jog KEPT)
rip_via('ULPI_CK', (75.125, 5.875))
rip_trk('ULPI_CK', 'F', (75.125, 5.875), (75.250, 5.162))
rip_trk('ULPI_CK', 'In2', (74.625, 6.375), (74.875, 6.125))
rip_trk('ULPI_CK', 'In2', (74.875, 6.125), (75.125, 5.875))
rip_trk('ULPI_CK', 'In2', (74.625, 6.375), (74.625, 9.400))
# RBIAS via + F stub piece
rip_via('RBIAS', (73.875, 11.625))
rip_trk('RBIAS', 'F', (74.000, 11.562), (73.875, 11.625))
# RBIAS In2 column window + boundary (bj machinery)
def in_win(p):
    return 73.7 <= p[0] <= 74.2 and 11.4 <= p[1] <= 16.7
rbias_col = [it for it in items if it.net == 'RBIAS' and it.kind == 'trk' and it.layer == 'In2'
             and in_win(it.a) and in_win(it.b)]
for it in rbias_col:
    RIPS.append(('trk', 'RBIAS', 'In2', it.a, it.b))
rbias_bnd = [it for it in items if it.net == 'RBIAS' and it.kind == 'trk' and it.layer == 'In2'
             and in_win(it.a) != in_win(it.b)]
for it in rbias_bnd:
    RIPS.append(('trk', 'RBIAS', 'In2', it.a, it.b))
# +3V3A west via + its F horizontal + B vertical + B diagonal (DELETED via)
rip_via('+3V3A', (73.625, 10.625))
rip_trk('+3V3A', 'F', (74.375, 10.625), (73.625, 10.625))
rip_trk('+3V3A', 'F', (75.125, 11.125), (74.250, 10.625))
rip_trk('+3V3A', 'B', (73.625, 8.625), (73.625, 10.625))
rip_trk('+3V3A', 'B', (73.625, 10.625), (75.625, 8.625))
# BIST window (bh3: 5 segs)
rip_trk('BIST_DRV', 'In2', (73.875, 6.125), (74.125, 5.875))
rip_trk('BIST_DRV', 'In2', (74.125, 5.875), (74.375, 5.625))
rip_trk('BIST_DRV', 'In2', (74.375, 5.625), (74.625, 5.375))
rip_trk('BIST_DRV', 'In2', (74.625, 5.375), (74.875, 5.125))
rip_trk('BIST_DRV', 'In2', (74.875, 5.125), (75.375, 5.125))
# SPI_MOSI window (bh nudge)
rip_trk('SPI_MOSI', 'In2', (71.900, 7.250), (73.400, 5.200))
rip_trk('SPI_MOSI', 'In2', (73.400, 5.200), (75.100, 4.550))
rip_trk('SPI_MOSI', 'In2', (75.100, 4.550), (76.400, 3.350))
# I2C_SCL B corner (bh nudge)
rip_trk('I2C_SCL', 'B', (74.125, 5.875), (74.375, 6.125))
rip_trk('I2C_SCL', 'B', (74.375, 6.125), (74.625, 6.375))
rip_trk('I2C_SCL', 'B', (74.625, 6.375), (74.875, 6.625))
rip_trk('I2C_SCL', 'B', (74.875, 6.625), (75.125, 6.875))


def rip_report():
    bad = []
    rip_ids = set()
    for kind, net, layer, a, b in RIPS:
        hits = find_via(net, a) if kind == 'via' else find_trk(net, layer, a, b)
        if len(hits) < 1:
            bad.append((kind, net, layer, a, b))
        for h in hits:
            rip_ids.add(id(h))
    return bad, rip_ids


_bad, _rip_ids = rip_report()
pool = [it for it in items if id(it) not in _rip_ids]

# ---------------- fixed adds ----------------
ADDS = []
def add_trk(label, net, layer, a, b, w):
    ADDS.append((label, G.Item(net, 'trk', layer=layer, a=a, b=b, hw=w / 2)))
def add_poly(label, net, layer, pts, w):
    for a, b in zip(pts, pts[1:]):
        add_trk(label, net, layer, a, b, w)
def add_via(label, net, c, dia):
    ADDS.append((label, G.Item(net, 'via', a=c, hw=dia / 2)))

# DM re-lay west v3 (extra west nudge vs GND via (73.434,17.685))
add_poly('DM-west', 'DM_PHY', 'F',
         [(73.562, 17.000), (73.100, 17.120), (72.790, 17.600), (72.790, 18.500),
          (73.625, 19.125)], 0.25)
# RST F stub + dive via
add_poly('RST-stub', 'USB_RST', 'F', [(74.250, 16.878), (74.320, 17.550), (74.450, 18.250)], 0.20)
add_via('RST-dive', 'USB_RST', (74.450, 18.250), 0.50)
# RST In2 journey: dive -> channel -> jog thread (east approach) -> arrival
JOURNEY = [(74.450, 18.250), (74.300, 17.350), (74.160, 16.550), (74.160, 12.000),
           (74.200, 10.620), (73.960, 10.550), (73.800, 9.900), (74.140, 9.000),
           (74.140, 7.050), (74.820, 5.840)]
add_poly('RST-journey', 'USB_RST', 'In2', JOURNEY, 0.20)
# arrival (bh shape, CK via shifted to (75.48,5.92): D0-vs-surf jaw solution)
add_via('CK-via', 'ULPI_CK', (75.480, 5.920), 0.50)
add_poly('CK-F', 'ULPI_CK', 'F', [(75.250, 5.162), (75.280, 5.600), (75.480, 5.920)], 0.20)
add_poly('CK-bow', 'ULPI_CK', 'In2',
         [(75.480, 5.920), (75.050, 6.600), (74.700, 7.000), (74.625, 7.350)], 0.25)
add_poly('CK-col', 'ULPI_CK', 'In2', [(74.625, 7.350), (74.625, 9.400)], 0.25)
add_via('RST-surf', 'USB_RST', (74.820, 5.840), 0.40)
add_poly('RST-hop', 'USB_RST', 'F', [(74.820, 5.840), (74.780, 5.500), (74.780, 5.300)], 0.20)
# +3V3A In2 re-feed: U7.25 pad south edge -> staircase -> via (75.625,8.625)
add_poly('P3V3A-feed', '+3V3A', 'In2',
         [(75.250, 11.200), (75.300, 10.000), (75.450, 9.350), (75.580, 8.950),
          (75.625, 8.625)], 0.20)
# RBIAS via west-north + F stub + In2 connector (bowed east vs XO endpoint)
add_via('RBIAS-via', 'RBIAS', (73.510, 10.950), 0.60)
add_poly('RBIAS-F', 'RBIAS', 'F', [(74.000, 11.562), (73.510, 10.950)], 0.20)
add_poly('RBIAS-conn', 'RBIAS', 'In2', [(73.510, 10.950), (73.680, 11.150), (73.575, 11.625)], 0.25)
# RBIAS column shifted -0.30 + boundary connectors (bj machinery)
for it in rbias_col:
    ADDS.append(('RBIAS-col', G.Item('RBIAS', 'trk', layer='In2',
                                     a=(it.a[0] - 0.30, it.a[1]), b=(it.b[0] - 0.30, it.b[1]),
                                     hw=it.hw)))
for it in rbias_bnd:
    inside, outside = (it.a, it.b) if in_win(it.a) else (it.b, it.a)
    add_trk('RBIAS-bnd', 'RBIAS', 'In2', (inside[0] - 0.30, inside[1]), outside, it.hw * 2)
# BIST re-add (bh3: interior joints dy -0.049, end joint to (75.375,5.076) + connector)
add_poly('BIST', 'BIST_DRV', 'In2',
         [(73.875, 6.125), (74.125, 5.826), (74.375, 5.576), (74.625, 5.326),
          (74.875, 5.076), (75.375, 5.076), (75.375, 5.125)], 0.25)
# MOSI re-add (bh3 polyline)
add_poly('MOSI', 'SPI_MOSI', 'In2',
         [(71.900, 7.250), (73.400, 5.186), (75.100, 4.536), (76.400, 3.350)], 0.20)
# SCL re-add (bj shifted + connectors)
add_poly('SCL', 'I2C_SCL', 'B',
         [(74.125, 5.875), (74.340, 6.160), (74.590, 6.410), (74.840, 6.660), (75.125, 6.875)], 0.25)

full = pool + [it for _, it in ADDS]


def price(adds, env):
    rows = []
    for label, it in adds:
        if it.kind == 'via':
            m, d = m_via(it.a, it.hw, it.net, env)
        else:
            m, d = m_trk(it.a, it.b, it.layer, it.hw, it.net, env)
        rows.append((m, label, it, d))
    rows.sort(key=lambda r: r[0])
    return rows
