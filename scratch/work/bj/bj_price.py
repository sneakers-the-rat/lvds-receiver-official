#!/usr/bin/env python3
"""bj composite pricer: USB_RST full composite on exp257, exact geometry,
REFEREE margins (0.20 / 0.25 power; gridroute pair_clr minus the 0.30
In2-In2 census band, per bh's finding). Sections:
 1. rip verification (each rip pattern must match the board exactly)
 2. fixed adds priced (DM re-lay, RST stub/journey/arrival, CK, PHY
    notch, RBIAS via+shift, BIST/MOSI/SCL nudges)
 3. DIR/NXT south-fanout grid search (vias + 2-seg stubs)
Full report -> bj_price_out.txt; console gets verdict lines only."""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
OUT = open('/home/hatch/workspace/pdlvds-route/scratch/work/bj/bj_price_out.txt', 'w')
P = lambda *a: print(*a, file=OUT)
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
    dx = max(x0 - p[0], 0.0, p[0] - x1)
    dy = max(y0 - p[1], 0.0, p[1] - y1)
    return math.hypot(dx, dy)


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
    """worst margin of a new track vs pool (same-net skipped)."""
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
    hits = [it for it in items if it.net == net and it.kind == 'trk' and it.layer == layer
            and ((near(it.a, a) and near(it.b, b)) or (near(it.a, b) and near(it.b, a)))]
    return hits


def find_via(net, c):
    return [it for it in items if it.net == net and it.kind == 'via' and near(it.a, c)]


# ---------------- rip list ----------------
RIPS = []  # (kind, net, layer, a, b) trk | (kind, net, None, c, None) via
def rip_trk(net, layer, a, b):
    RIPS.append(('trk', net, layer, a, b))
def rip_via(net, c):
    RIPS.append(('via', net, None, c, None))

# DM F loop (keep via (73.625,19.125) + north vertical)
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
# CK arrival (bh)
rip_via('ULPI_CK', (75.125, 5.875))
rip_trk('ULPI_CK', 'F', (75.125, 5.875), (75.250, 5.162))
rip_trk('ULPI_CK', 'In2', (74.625, 6.375), (74.875, 6.125))
rip_trk('ULPI_CK', 'In2', (74.875, 6.125), (75.125, 5.875))
rip_trk('ULPI_CK', 'In2', (74.625, 6.375), (74.625, 9.400))
rip_trk('ULPI_CK', 'In2', (74.625, 9.400), (74.320, 10.200))
rip_trk('ULPI_CK', 'In2', (74.320, 10.200), (74.625, 11.000))
# PHY notch via + B head (F stub found below)
rip_via('PHY_1V8A', (74.990, 10.280))
rip_trk('PHY_1V8A', 'B', (74.990, 10.280), (75.000, 11.500))
# RBIAS via + F stub
rip_via('RBIAS', (73.875, 11.625))
rip_trk('RBIAS', 'F', (74.000, 11.562), (73.875, 11.625))
# RBIAS In2 column window y[11.4,16.7] x[73.7,74.2] — all segs fully inside
rbias_col = [it for it in items if it.net == 'RBIAS' and it.kind == 'trk' and it.layer == 'In2'
             and 73.7 <= it.a[0] <= 74.2 and 73.7 <= it.b[0] <= 74.2
             and 11.4 <= it.a[1] <= 16.7 and 11.4 <= it.b[1] <= 16.7]
for it in rbias_col:
    RIPS.append(('trk', 'RBIAS', 'In2', it.a, it.b))
# boundary segs: exactly one endpoint in the window box -> rip + reconnect
def in_win(p):
    return 73.7 <= p[0] <= 74.2 and 11.4 <= p[1] <= 16.7
rbias_bnd = [it for it in items if it.net == 'RBIAS' and it.kind == 'trk' and it.layer == 'In2'
             and in_win(it.a) != in_win(it.b)]
for it in rbias_bnd:
    RIPS.append(('trk', 'RBIAS', 'In2', it.a, it.b))
# BIST window (bh nudge)
rip_trk('BIST_DRV', 'In2', (73.875, 6.125), (74.125, 5.875))
rip_trk('BIST_DRV', 'In2', (74.125, 5.875), (74.375, 5.625))
rip_trk('BIST_DRV', 'In2', (74.375, 5.625), (74.625, 5.375))
rip_trk('BIST_DRV', 'In2', (74.625, 5.375), (74.875, 5.125))
# SPI_MOSI window (bh nudge)
rip_trk('SPI_MOSI', 'In2', (71.900, 7.250), (73.400, 5.200))
rip_trk('SPI_MOSI', 'In2', (73.400, 5.200), (75.100, 4.550))
rip_trk('SPI_MOSI', 'In2', (75.100, 4.550), (76.400, 3.350))
# I2C_SCL B corner (bh nudge)
rip_trk('I2C_SCL', 'B', (74.125, 5.875), (74.375, 6.125))
rip_trk('I2C_SCL', 'B', (74.375, 6.125), (74.625, 6.375))
rip_trk('I2C_SCL', 'B', (74.625, 6.375), (74.875, 6.625))
rip_trk('I2C_SCL', 'B', (74.875, 6.625), (75.125, 6.875))

P('==== RIP VERIFICATION')
bad = 0
for kind, net, layer, a, b in RIPS:
    hits = find_via(net, a) if kind == 'via' else find_trk(net, layer, a, b)
    if len(hits) != 1:
        P(f'  !! {kind} {net} {layer} {a} {b}: {len(hits)} hits')
        bad += 1
P(f'  rips total {len(RIPS)}, unmatched {bad}')
# PHY F stub: whatever F track touches the notch via
phy_stub = [it for it in items if it.net == 'PHY_1V8A' and it.kind == 'trk' and it.layer == 'F'
            and (near(it.a, (74.990, 10.280)) or near(it.b, (74.990, 10.280)))]
for it in phy_stub:
    P(f'  PHY F stub: {it.a}->{it.b} hw{it.hw}')
    RIPS.append(('trk', 'PHY_1V8A', 'F', it.a, it.b))

rip_ids = set()
for kind, net, layer, a, b in RIPS:
    hits = find_via(net, a) if kind == 'via' else find_trk(net, layer, a, b)
    for h in hits:
        rip_ids.add(id(h))
pool = [it for it in items if id(it) not in rip_ids]

# ---------------- new geometry (fixed adds) ----------------
ADDS = []  # (label, Item)
def add_trk(label, net, layer, a, b, w):
    ADDS.append((label, G.Item(net, 'trk', layer=layer, a=a, b=b, hw=w / 2)))
def add_poly(label, net, layer, pts, w):
    for a, b in zip(pts, pts[1:]):
        add_trk(label, net, layer, a, b, w)
def add_via(label, net, c, dia):
    ADDS.append((label, G.Item(net, 'via', a=c, hw=dia / 2)))

# DM re-lay west (w0.25)
add_poly('DM-west', 'DM_PHY', 'F',
         [(73.562, 17.000), (72.950, 17.350), (72.820, 17.950), (72.950, 18.620),
          (73.625, 19.125)], 0.25)
# RST F stub + dive via
add_poly('RST-stub', 'USB_RST', 'F', [(74.250, 16.878), (74.320, 17.550), (74.450, 18.250)], 0.20)
add_via('RST-dive', 'USB_RST', (74.450, 18.250), 0.50)
# RST In2 journey: dive -> west channel -> diagonal stub into surface via
add_poly('RST-journey', 'USB_RST', 'In2',
         [(74.450, 18.250), (74.300, 17.350), (74.160, 16.550), (74.160, 12.000),
          (74.140, 10.900), (74.140, 7.050), (74.800, 5.820)], 0.20)
# arrival (bh status values)
add_via('CK-via', 'ULPI_CK', (75.440, 6.040), 0.50)
add_poly('CK-F', 'ULPI_CK', 'F', [(75.250, 5.162), (75.330, 5.620), (75.440, 6.040)], 0.20)
add_poly('CK-bow', 'ULPI_CK', 'In2',
         [(75.440, 6.040), (75.050, 6.600), (74.700, 7.000), (74.625, 7.350)], 0.25)
add_poly('CK-col', 'ULPI_CK', 'In2', [(74.625, 7.350), (74.625, 11.000)], 0.25)
add_via('RST-surf', 'USB_RST', (74.800, 5.820), 0.40)
add_poly('RST-hop', 'USB_RST', 'F', [(74.800, 5.820), (74.780, 5.500), (74.780, 5.300)], 0.20)
# PHY notch via east
add_via('PHY-notch', 'PHY_1V8A', (75.350, 10.850), 0.50)
if phy_stub:
    s = phy_stub[0]
    src = s.b if near(s.a, (74.990, 10.280)) else s.a
    add_poly('PHY-stub', 'PHY_1V8A', 'F', [src, (75.350, 10.850)], s.hw * 2)
add_poly('PHY-B', 'PHY_1V8A', 'B', [(75.350, 10.850), (75.000, 11.500)], 0.20)
# RBIAS via west+north, F stub, In2 connector, shifted column + S connector
add_via('RBIAS-via', 'RBIAS', (73.500, 10.850), 0.60)
add_poly('RBIAS-F', 'RBIAS', 'F', [(74.000, 11.562), (73.500, 10.850)], 0.20)
shifted = []
for it in rbias_col:
    a = (it.a[0] - 0.30, it.a[1]); b = (it.b[0] - 0.30, it.b[1])
    shifted.append((a, b, it.hw))
    ADDS.append(('RBIAS-col', G.Item('RBIAS', 'trk', layer='In2', a=a, b=b, hw=it.hw)))
# north connector: via -> northernmost shifted endpoint
all_shift_pts = {p for a, b, _ in shifted for p in (a, b)}
north_pt = min(all_shift_pts, key=lambda p: p[1])
add_poly('RBIAS-conn', 'RBIAS', 'In2', [(73.500, 10.850), north_pt], 0.25)
# boundary connectors: shifted in-window end -> original out-window end
for it in rbias_bnd:
    inside, outside = (it.a, it.b) if in_win(it.a) else (it.b, it.a)
    add_trk('RBIAS-bnd', 'RBIAS', 'In2', (inside[0] - 0.30, inside[1]), outside, it.hw * 2)
P(f'  RBIAS shifted segs {len(shifted)}; north pt {north_pt}; boundary segs {len(rbias_bnd)}')
# BIST re-add (interior joints dy -0.049)
add_poly('BIST', 'BIST_DRV', 'In2',
         [(73.875, 6.125), (74.125, 5.826), (74.375, 5.576), (74.625, 5.326), (74.875, 5.125)], 0.25)
# MOSI re-add (bh3 polyline)
add_poly('MOSI', 'SPI_MOSI', 'In2',
         [(71.900, 7.250), (73.400, 5.186), (75.100, 4.536), (76.400, 3.350)], 0.20)
# SCL re-add (shifted + connectors)
add_poly('SCL', 'I2C_SCL', 'B',
         [(74.125, 5.875), (74.340, 6.160), (74.590, 6.410), (74.840, 6.660), (75.125, 6.875)], 0.25)

full = pool + [it for _, it in ADDS]
P('==== FIXED ADDS — worst referee margins')
rows = []
for label, it in ADDS:
    if it.kind == 'via':
        m, d = m_via(it.a, it.hw, it.net, full)
    else:
        m, d = m_trk(it.a, it.b, it.layer, it.hw, it.net, full)
    rows.append((m, label, it, d))
rows.sort(key=lambda r: r[0])
for m, label, it, d in rows[:22]:
    loc = it.a if it.kind == 'via' else f'{it.a}->{it.b}'
    P(f'  {m:+.3f}  {label} {it.net}[{it.layer or "via"}] {loc} :: {d}')
neg = [r for r in rows if r[0] < 0]
P(f'  fixed adds: {len(rows)} items, {len(neg)} negative')
OUT.close()
print(f'rips unmatched: see file; fixed-add negatives: {len(neg)}')
for m, label, it, d in rows[:8]:
    loc = it.a if it.kind == 'via' else f'{it.a}->{it.b}'
    print(f'  {m:+.3f} {label} {loc} :: {d}')
