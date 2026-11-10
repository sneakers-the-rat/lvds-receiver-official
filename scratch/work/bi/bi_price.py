#!/usr/bin/env python3
"""bi composite pricer for USB_RST on exp257 (referee rules: 0.20 /
0.25 power edge classes; NO 0.30 census band).
Composite: DIR/NXT re-fan variants + RST dive (74.30,17.50) + B journey
(x70.7 column, In2 hop over +3V3A B w0.6 horizontal) + bh arrival
(CK via (75.44,6.04) d0.5, RST surface (74.80,5.82) d0.40, nudges).
Pool = exp257 items - rips + shifted copies; new items priced against
pool AND each other (cross-net)."""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
BASE = G.load_items(BOARD)


def pt_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def seg_seg(a, b, c, d):
    def o(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = o(a, b, c), o(a, b, d), o(c, d, a), o(c, d, b)
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
    edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    if any(seg_seg(a, b, e0, e1) == 0.0 for e0, e1 in edges):
        return 0.0
    return min(pt_rect(a, r), pt_rect(b, r),
               min(pt_seg(c, a, b) for c in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))


def clr(net):
    return 0.25 if G.is_power(net) else 0.20


def m_trk(a, b, layer, hw, net, pool):
    out = []
    for it in pool:
        if it.net == net:
            continue
        if it.kind == 'via':
            out.append((pt_seg(it.a, a, b) - hw - it.hw - clr(it.net), f'via {it.net}@{it.a}'))
        elif it.kind == 'trk' and it.layer == layer:
            out.append((seg_seg(a, b, it.a, it.b) - hw - it.hw - clr(it.net),
                        f'trk {it.net} {it.a}->{it.b}'))
        elif it.kind == 'pad' and it.layer == layer:
            out.append((seg_rect(a, b, it.rect) - hw - clr(it.net), f'pad {it.net} {it.rect}'))
    return sorted(out)


def m_via(c, r, net, pool):
    out = []
    for it in pool:
        if it.net == net:
            continue
        if it.kind == 'via':
            d = math.hypot(c[0] - it.a[0], c[1] - it.a[1])
            out.append((d - r - it.hw - clr(it.net), f'via {it.net}@{it.a}'))
        elif it.kind == 'trk':
            out.append((pt_seg(c, it.a, it.b) - r - it.hw - clr(it.net),
                        f'trk[{it.layer}] {it.net} {it.a}->{it.b}'))
        elif it.kind == 'pad':
            out.append((pt_rect(c, it.rect) - r - clr(it.net), f'pad[{it.layer}] {it.net} {it.rect}'))
    return sorted(out)


def key_trk(it):
    return (it.net, it.kind, it.layer, it.a, it.b)


RIPS = [
    # CK arrival
    ('ULPI_CK', 'F', (75.125, 5.875), (75.250, 5.162)),
    ('ULPI_CK', 'In2', (74.625, 6.375), (74.875, 6.125)),
    ('ULPI_CK', 'In2', (74.875, 6.125), (75.125, 5.875)),
    ('ULPI_CK', 'In2', (74.625, 6.375), (74.625, 9.400)),
    # NXT escape
    ('ULPI_NXT', 'F', (75.250, 16.875), (74.940, 17.360)),
    ('ULPI_NXT', 'In2', (74.940, 17.360), (74.100, 17.700)),
    ('ULPI_NXT', 'In2', (74.100, 17.700), (74.500, 19.250)),
]
RIP_VIAS = [('ULPI_CK', (75.125, 5.875)), ('ULPI_NXT', (74.940, 17.360))]
DIR_RIPS = [
    ('ULPI_DIR', 'F', (75.750, 16.875), (75.600, 17.300)),
    ('ULPI_DIR', 'F', (75.600, 17.300), (75.420, 17.950)),
    ('ULPI_DIR', 'F', (75.420, 17.950), (74.820, 18.100)),
    ('ULPI_DIR', 'B', (74.820, 18.100), (73.300, 18.420)),
]
SHIFTS = [  # (net, layer, a, b, dx, dy)
    ('BIST_DRV', 'In2', (74.125, 5.875), (74.375, 5.625), 0.0, -0.049),
    ('BIST_DRV', 'In2', (74.375, 5.625), (74.625, 5.375), 0.0, -0.049),
    ('BIST_DRV', 'In2', (74.625, 5.375), (74.875, 5.125), 0.0, -0.049),
    ('BIST_DRV', 'In2', (74.875, 5.125), (75.375, 5.125), 0.0, -0.049),
    ('SPI_MOSI', 'In2', (73.400, 5.200), (75.100, 4.550), 0.0, -0.014),
    ('I2C_SCL', 'B', (74.375, 6.125), (74.625, 6.375), -0.035, 0.035),
    ('I2C_SCL', 'B', (74.625, 6.375), (74.875, 6.625), -0.035, 0.035),
]


def near(p, q, tol=0.006):
    return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol


def build_pool(move_dir):
    rips = list(RIPS) + (DIR_RIPS if move_dir else [])
    rip_vias = list(RIP_VIAS) + ([('ULPI_DIR', (74.820, 18.100))] if move_dir else [])
    shift_keys = {(n, l, a, b) for n, l, a, b, dx, dy in SHIFTS}
    pool = []
    for it in BASE:
        if it.kind == 'trk':
            k = (it.net, it.layer, it.a, it.b)
            k2 = (it.net, it.layer, it.b, it.a)
            if any(it.net == n and it.layer == l and ((near(it.a, a) and near(it.b, b)) or
                   (near(it.a, b) and near(it.b, a))) for n, l, a, b in rips):
                continue
            if k in shift_keys or k2 in shift_keys:
                continue
            pool.append(it)
        elif it.kind == 'via':
            if any(it.net == n and near(it.a, at) for n, at in rip_vias):
                continue
            pool.append(it)
        else:
            pool.append(it)
    for n, l, a, b, dx, dy in SHIFTS:
        pool.append(G.Item(n, 'trk', layer=l, a=(a[0] + dx, a[1] + dy),
                           b=(b[0] + dx, b[1] + dy), hw=0.125 if n == 'BIST_DRV' else 0.10))
    return pool


def T(net, layer, a, b, w=0.2):
    return ('trk', net, layer, a, b, w / 2)


def V(net, x, y, d=0.5):
    return ('via', net, None, (x, y), None, d / 2)


NEW_COMMON = [
    # CK arrival (bh final)
    V('ULPI_CK', 75.44, 6.04, 0.5),
    T('ULPI_CK', 'F', (75.25, 5.162), (75.33, 5.62)),
    T('ULPI_CK', 'F', (75.33, 5.62), (75.44, 6.04)),
    T('ULPI_CK', 'In2', (75.44, 6.04), (75.05, 6.60), 0.25),
    T('ULPI_CK', 'In2', (75.05, 6.60), (74.70, 7.00), 0.25),
    T('ULPI_CK', 'In2', (74.70, 7.00), (74.625, 7.35), 0.25),
    T('ULPI_CK', 'In2', (74.625, 7.35), (74.625, 9.40), 0.25),
    # RST dive + journey + arrival
    T('USB_RST', 'F', (74.25, 16.878), (74.30, 17.50)),
    V('USB_RST', 74.30, 17.50, 0.5),
    T('USB_RST', 'B', (74.30, 17.50), (73.60, 16.60)),
    T('USB_RST', 'B', (73.60, 16.60), (72.20, 15.90)),
    T('USB_RST', 'B', (72.20, 15.90), (70.70, 15.90)),
    T('USB_RST', 'B', (70.70, 15.90), (70.70, 9.55)),
    V('USB_RST', 70.70, 9.55, 0.5),
    T('USB_RST', 'In2', (70.70, 9.55), (70.70, 7.75)),
    V('USB_RST', 70.70, 7.75, 0.5),
    T('USB_RST', 'B', (70.70, 7.75), (70.70, 4.50)),
    T('USB_RST', 'B', (70.70, 4.50), (74.30, 4.50)),
    T('USB_RST', 'B', (74.30, 4.50), (74.80, 5.82)),
    V('USB_RST', 74.80, 5.82, 0.40),
    T('USB_RST', 'F', (74.80, 5.82), (74.78, 5.50)),
    T('USB_RST', 'F', (74.78, 5.50), (74.78, 5.30)),
]
NEW_NXT = [
    T('ULPI_NXT', 'F', (75.25, 16.875), (74.95, 17.40)),
    V('ULPI_NXT', 74.95, 17.40, 0.5),
    T('ULPI_NXT', 'In2', (74.95, 17.40), (74.10, 17.70)),
]
NEW_DIR = [
    T('ULPI_DIR', 'F', (75.75, 16.875), (76.10, 17.50)),
    T('ULPI_DIR', 'F', (76.10, 17.50), (76.35, 18.75)),
    V('ULPI_DIR', 76.35, 18.75, 0.5),
    T('ULPI_DIR', 'B', (76.35, 18.75), (76.45, 19.30)),
    T('ULPI_DIR', 'B', (76.45, 19.30), (74.90, 19.85)),
    T('ULPI_DIR', 'B', (74.90, 19.85), (73.30, 18.42)),
]
# V3: DIR stock; RST dive SOUTH (74.55,19.05) d0.40; In2 west leg;
# B column x70.15; hop vias (70.05,9.70)/(70.15,7.35); east leg y3.90.
NEW_V3 = [
    T('ULPI_CK', 'F', (75.25, 5.162), (75.33, 5.62)),
    T('ULPI_CK', 'F', (75.33, 5.62), (75.44, 6.04)),
    V('ULPI_CK', 75.44, 6.04, 0.5),
    T('ULPI_CK', 'In2', (75.44, 6.04), (75.05, 6.60), 0.25),
    T('ULPI_CK', 'In2', (75.05, 6.60), (74.70, 7.00), 0.25),
    T('ULPI_CK', 'In2', (74.70, 7.00), (74.625, 7.35), 0.25),
    T('ULPI_CK', 'In2', (74.625, 7.35), (74.625, 9.40), 0.25),
    T('USB_RST', 'F', (74.25, 16.878), (74.62, 17.60)),
    T('USB_RST', 'F', (74.62, 17.60), (74.55, 19.05)),
    V('USB_RST', 74.55, 19.05, 0.40),
    T('USB_RST', 'In2', (74.55, 19.05), (73.95, 18.60)),
    T('USB_RST', 'In2', (73.95, 18.60), (73.80, 17.55)),
    T('USB_RST', 'In2', (73.80, 17.55), (73.85, 16.80)),
    T('USB_RST', 'In2', (73.85, 16.80), (72.60, 16.55)),
    T('USB_RST', 'In2', (72.60, 16.55), (70.15, 16.35)),
    V('USB_RST', 70.15, 16.35, 0.5),
    T('USB_RST', 'B', (70.15, 16.35), (70.15, 9.70)),
    V('USB_RST', 70.05, 9.70, 0.5),
    T('USB_RST', 'B', (70.15, 9.70), (70.05, 9.70)),
    T('USB_RST', 'In2', (70.05, 9.70), (70.15, 7.35)),
    V('USB_RST', 70.15, 7.35, 0.5),
    T('USB_RST', 'B', (70.15, 7.35), (70.15, 3.90)),
    T('USB_RST', 'B', (70.15, 3.90), (74.30, 3.90)),
    T('USB_RST', 'B', (74.30, 3.90), (74.80, 5.82)),
    V('USB_RST', 74.80, 5.82, 0.40),
    T('USB_RST', 'F', (74.80, 5.82), (74.78, 5.50)),
    T('USB_RST', 'F', (74.78, 5.50), (74.78, 5.30)),
] + NEW_NXT


def as_items(new):
    out = []
    for kind, net, layer, a, b, hw in new:
        if kind == 'via':
            out.append(G.Item(net, 'via', a=a, hw=hw))
        else:
            out.append(G.Item(net, 'trk', layer=layer, a=a, b=b, hw=hw))
    return out


def price(name, move_dir):
    pool = build_pool(move_dir)
    new = NEW_COMMON + NEW_NXT + (NEW_DIR if move_dir else [])
    pool_all = pool + as_items(new)
    print(f'--- {name}: negatives (referee rules)')
    worst = []
    for kind, net, layer, a, b, hw in new:
        if kind == 'via':
            r = m_via(a, hw, net, pool_all)
            worst += [(m, f'{net} via@{a}: {d}') for m, d in r[:2]]
        else:
            r = m_trk(a, b, layer, hw, net, pool_all)
            worst += [(m, f'{net} {layer} {a}->{b}: {d}') for m, d in r[:2]]
    worst.sort()
    neg = [w for w in worst if w[0] < 0]
    print(f'  count {len(neg)}; worst 14:')
    for m, d in worst[:14]:
        print(f'    {m:+.3f}  {d}')


def price_new(name, new, move_dir=False):
    pool = build_pool(move_dir)
    pool_all = pool + as_items(new)
    print(f'--- {name}: negatives (referee rules)')
    worst = []
    for kind, net, layer, a, b, hw in new:
        if kind == 'via':
            r = m_via(a, hw, net, pool_all)
            worst += [(m, f'{net} via@{a}: {d}') for m, d in r[:2]]
        else:
            r = m_trk(a, b, layer, hw, net, pool_all)
            worst += [(m, f'{net} {layer} {a}->{b}: {d}') for m, d in r[:2]]
    worst.sort()
    neg = [w for w in worst if w[0] < 0]
    print(f'  count {len(neg)}; worst 14:')
    for m, d in worst[:14]:
        print(f'    {m:+.3f}  {d}')


DIR_RIPS_ALL = DIR_RIPS + [
    ('ULPI_NXT', 'In2', (74.100, 17.700), (74.500, 19.250)),
]
NEW_V4 = [
    # CK arrival (bh final)
    T('ULPI_CK', 'F', (75.25, 5.162), (75.33, 5.62)),
    T('ULPI_CK', 'F', (75.33, 5.62), (75.44, 6.04)),
    V('ULPI_CK', 75.44, 6.04, 0.5),
    T('ULPI_CK', 'In2', (75.44, 6.04), (75.05, 6.60), 0.25),
    T('ULPI_CK', 'In2', (75.05, 6.60), (74.70, 7.00), 0.25),
    T('ULPI_CK', 'In2', (74.70, 7.00), (74.625, 7.35), 0.25),
    T('ULPI_CK', 'In2', (74.625, 7.35), (74.625, 9.40), 0.25),
    # DIR re-fan: via (74.20,19.55), B rejoin via (74.60,18.35)
    T('ULPI_DIR', 'F', (75.75, 16.875), (75.30, 17.90)),
    T('ULPI_DIR', 'F', (75.30, 17.90), (74.35, 18.85)),
    T('ULPI_DIR', 'F', (74.35, 18.85), (74.20, 19.55)),
    V('ULPI_DIR', 74.20, 19.55, 0.5),
    T('ULPI_DIR', 'B', (74.20, 19.55), (74.60, 18.35)),
    T('ULPI_DIR', 'B', (74.60, 18.35), (73.30, 18.42)),
    # NXT re-fan: via (74.85,19.15)
    T('ULPI_NXT', 'F', (75.25, 16.875), (74.95, 17.85)),
    T('ULPI_NXT', 'F', (74.95, 17.85), (74.70, 18.60)),
    T('ULPI_NXT', 'F', (74.70, 18.60), (74.85, 19.15)),
    V('ULPI_NXT', 74.85, 19.15, 0.5),
    T('ULPI_NXT', 'In2', (74.85, 19.15), (74.50, 19.25)),
    # RST: F stub + dive (74.85,17.45); B west with In2 hop over DIR B;
    # column x67.15; east leg; arrival stub
    T('USB_RST', 'F', (74.25, 16.878), (74.85, 17.45)),
    V('USB_RST', 74.85, 17.45, 0.5),
    T('USB_RST', 'B', (74.85, 17.45), (74.75, 17.75)),
    V('USB_RST', 74.75, 17.75, 0.5),
    T('USB_RST', 'In2', (74.75, 17.75), (73.70, 19.10)),
    V('USB_RST', 73.70, 19.10, 0.5),
    T('USB_RST', 'B', (73.70, 19.10), (72.50, 19.30)),
    T('USB_RST', 'B', (72.50, 19.30), (67.15, 19.30)),
    T('USB_RST', 'B', (67.15, 19.30), (67.15, 5.30)),
    T('USB_RST', 'B', (67.15, 5.30), (68.30, 5.30)),
    T('USB_RST', 'B', (68.30, 5.30), (69.60, 4.90)),
    T('USB_RST', 'B', (69.60, 4.90), (74.30, 4.50)),
    T('USB_RST', 'B', (74.30, 4.50), (74.80, 5.82)),
    V('USB_RST', 74.80, 5.82, 0.40),
    T('USB_RST', 'F', (74.80, 5.82), (74.78, 5.50)),
    T('USB_RST', 'F', (74.78, 5.50), (74.78, 5.30)),
]


def price_v4():
    rips = list(RIPS) + DIR_RIPS_ALL
    rip_vias = list(RIP_VIAS) + [('ULPI_DIR', (74.820, 18.100))]
    shift_keys = {(n, l, a, b) for n, l, a, b, dx, dy in SHIFTS}
    pool = []
    for it in BASE:
        if it.kind == 'trk':
            k = (it.net, it.layer, it.a, it.b)
            k2 = (it.net, it.layer, it.b, it.a)
            if any(it.net == n and it.layer == l and ((near(it.a, a) and near(it.b, b)) or
                   (near(it.a, b) and near(it.b, a))) for n, l, a, b in rips):
                continue
            if k in shift_keys or k2 in shift_keys:
                continue
            pool.append(it)
        elif it.kind == 'via':
            if any(it.net == n and near(it.a, at) for n, at in rip_vias):
                continue
            pool.append(it)
        else:
            pool.append(it)
    for n, l, a, b, dx, dy in SHIFTS:
        pool.append(G.Item(n, 'trk', layer=l, a=(a[0] + dx, a[1] + dy),
                           b=(b[0] + dx, b[1] + dy), hw=0.125 if n == 'BIST_DRV' else 0.10))
    pool_all = pool + as_items(NEW_V4)
    print('--- V4 full composite: negatives (referee rules)')
    worst = []
    for kind, net, layer, a, b, hw in NEW_V4:
        if kind == 'via':
            r = m_via(a, hw, net, pool_all)
            worst += [(m, f'{net} via@{a}: {d}') for m, d in r[:2]]
        else:
            r = m_trk(a, b, layer, hw, net, pool_all)
            worst += [(m, f'{net} {layer} {a}->{b}: {d}') for m, d in r[:2]]
    worst.sort()
    neg = [w for w in worst if w[0] < 0]
    print(f'  count {len(neg)}; worst 16:')
    for m, d in worst[:16]:
        print(f'    {m:+.3f}  {d}')


price_v4()
