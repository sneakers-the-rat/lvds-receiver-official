#!/usr/bin/env python3
"""Exact-geometry pricer for the USER'S USB_RST design on exp257:
dive at U7.9 -> In2 near-straight vertical -> surface beside U6.40 -> F hop.
Uses gridroute.load_items (exact items) + its pair/via clearance rules.
Prices hand-set path variants; reports worst margins per variant.
NO raster, NO search: the topology is the user's; this only prices it."""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
items = G.load_items(BOARD)
RST = 'USB_RST'
TRK_HW = 0.10   # w0.2 signal
VIA_HW = 0.25   # d0.5 via


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
    if max(min(a[0], b[0]), x0) <= min(max(a[0], b[0]), x1) and \
       max(min(a[1], b[1]), y0) <= min(max(a[1], b[1]), y1):
        # bbox overlap: check real intersection with rect edges / containment
        if (x0 <= a[0] <= x1 and y0 <= a[1] <= y1) or (x0 <= b[0] <= x1 and y0 <= b[1] <= y1):
            return 0.0
        edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                 ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
        if any(seg_seg(a, b, e0, e1) == 0.0 for e0, e1 in edges):
            return 0.0
    return min(pt_rect(a, r), pt_rect(b, r),
               min(pt_seg(c, a, b) for c in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))


def margin_trk(a, b, layer, pool):
    """worst margins of my track a->b on `layer` vs pool items."""
    out = []
    for it in pool:
        if it.net == RST:
            continue
        if it.kind == 'via':
            d = min(pt_seg(it.a, a, b), 1e9)
            m = d - TRK_HW - it.hw - G.via_clr(it.net)
            out.append((m, f'via {it.net}@{it.a}'))
        elif it.kind == 'trk' and it.layer == layer:
            m = seg_seg(a, b, it.a, it.b) - TRK_HW - it.hw - G.pair_clr(it.net, layer, it.layer)
            out.append((m, f'trk {it.net} {it.a}->{it.b}'))
        elif it.kind == 'pad' and it.layer == layer:
            m = seg_rect(a, b, it.rect) - TRK_HW - G.pair_clr(it.net, layer, layer)
            out.append((m, f'pad {it.net} rect{it.rect}'))
    return sorted(out)


def margin_via(c, pool):
    out = []
    for it in pool:
        if it.net == RST:
            continue
        if it.kind == 'via':
            d = math.hypot(c[0] - it.a[0], c[1] - it.a[1])
            out.append((d - VIA_HW - it.hw - G.via_clr(it.net), f'via {it.net}@{it.a}'))
        elif it.kind == 'trk':
            d = pt_seg(c, it.a, it.b)
            out.append((d - VIA_HW - it.hw - G.via_clr(it.net), f'trk[{it.layer}] {it.net} {it.a}->{it.b}'))
        elif it.kind == 'pad':
            d = pt_rect(c, it.rect)
            out.append((d - VIA_HW - G.via_clr(it.net), f'pad[{it.layer}] {it.net} rect{it.rect}'))
    return sorted(out)


def price(name, in2_pts, surf_via, extra_pool_skip=None):
    pool = items
    print(f'--- {name}')
    worst = []
    # dive via at U7.9 pad centre (74.25,16.438)
    for label, fn in [('dive via', lambda: margin_via((74.25, 16.438), pool)),
                      ('surface via', lambda: margin_via(surf_via, pool))]:
        r = fn()
        worst += [(m, f'{label}: {d}') for m, d in r[:2]]
    for i in range(len(in2_pts) - 1):
        r = margin_trk(in2_pts[i], in2_pts[i + 1], 'In2', pool)
        worst += [(m, f'In2 leg{i}: {d}') for m, d in r[:2]]
    # F hop: surface via -> west edge of U6.40 pad (74.60,4.662)
    r = margin_trk(surf_via, (74.60, 4.662), 'F', pool)
    worst += [(m, f'F hop: {d}') for m, d in r[:2]]
    worst.sort()
    neg = [w for w in worst if w[0] < 0]
    print(f'  negatives: {len(neg)}; worst 8:')
    for m, d in worst[:8]:
        print(f'    {m:+.3f}  {d}')


def shifted_pool(shifts):
    """items with trk items of `net` inside box translated by (dx,dy).
    shifts: list of (net, (x0,y0,x1,y1), dx, dy). Returns new pool."""
    out = []
    for it in items:
        done = False
        if it.kind == 'trk':
            for net, (x0, y0, x1, y1), dx, dy in shifts:
                if it.net == net and x0 <= it.a[0] <= x1 and y0 <= it.a[1] <= y1 and \
                   x0 <= it.b[0] <= x1 and y0 <= it.b[1] <= y1:
                    out.append(G.Item(it.net, 'trk', layer=it.layer,
                                      a=(it.a[0] + dx, it.a[1] + dy),
                                      b=(it.b[0] + dx, it.b[1] + dy), hw=it.hw))
                    done = True
                    break
        if not done:
            out.append(it)
    return out


def price2(name, legs, surf_via, hop_to, pool):
    """legs: list of (layer, pts). surf_via priced; F hop surf_via->hop_to."""
    print(f'--- {name}')
    worst = []
    r = margin_via((74.25, 16.438), pool)
    worst += [(m, f'dive via: {d}') for m, d in r[:2]]
    r = margin_via(surf_via, pool)
    worst += [(m, f'surface via: {d}') for m, d in r[:3]]
    for layer, pts in legs:
        for i in range(len(pts) - 1):
            r = margin_trk(pts[i], pts[i + 1], layer, pool)
            worst += [(m, f'{layer} leg{i}: {d}') for m, d in r[:2]]
    r = margin_trk(surf_via, hop_to, 'F', pool)
    worst += [(m, f'F hop: {d}') for m, d in r[:3]]
    worst.sort()
    neg = [w for w in worst if w[0] < 0]
    print(f'  negatives: {len(neg)}; worst 8:')
    for m, d in worst[:8]:
        print(f'    {m:+.3f}  {d}')


PAD_S = (74.75, 5.45)   # just outside U6.40 pad south end (edge y5.402)
# F: all-B ride, surface via SW of pad at (74.55,6.45), hop NE into pad south end
price2('F all-B, surface (74.55,6.45)',
       [('B', [(74.25, 16.438), (74.50, 15.70), (74.50, 6.90), (74.55, 6.45)])],
       (74.55, 6.45), PAD_S, items)
# F2: all-B, surface via further SW (74.35,6.60)
price2('F2 all-B, surface (74.35,6.60)',
       [('B', [(74.25, 16.438), (74.45, 15.70), (74.45, 7.10), (74.35, 6.60)])],
       (74.35, 6.60), PAD_S, items)
# D: In2 centre column, east dodge around CK jog, east surface via (75.32,4.66), hop W into pad east edge
price2('D In2 + east dodge + east surface (75.32,4.66)',
       [('In2', [(74.25, 16.438), (74.55, 15.70), (74.55, 11.45), (75.18, 10.90),
                 (75.18, 9.30), (74.90, 8.80), (74.90, 6.20), (75.05, 5.30), (75.32, 4.66)])],
       (75.32, 4.66), (74.90, 4.662), items)
# D2: D with +3V3A staircase shifted +0.35E and SPI_MOSI crossing seg shifted +0.50S (user-approved purple moves)
pool_d2 = shifted_pool([('+3V3A', (75.2, 6.4, 76.0, 9.3), 0.35, 0.0),
                        ('SPI_MOSI', (73.0, 4.2, 75.4, 5.5), 0.0, 0.50)])
price2('D2 = D + staircase E + SPI_MOSI S shifts',
       [('In2', [(74.25, 16.438), (74.55, 15.70), (74.55, 11.45), (75.18, 10.90),
                 (75.18, 9.30), (74.90, 8.80), (74.90, 6.20), (75.05, 5.30), (75.32, 4.66)])],
       (75.32, 4.66), (74.90, 4.662), pool_d2)
# H2: west around EVERYTHING: north over RBIAS's top end, column x72.30,
# under the district, surface via (74.25,5.85), F hop NE into pad west face south part.
price2('H2 west column x72.30, surface (74.25,5.85)',
       [('In2', [(74.25, 16.438), (74.10, 17.05), (72.90, 17.15), (72.30, 16.40),
                 (72.30, 6.30), (73.30, 5.90), (74.25, 5.85)]),
        ('F', [(74.25, 5.85), (74.45, 5.55)])],
       (74.25, 5.85), (74.60, 5.30), items)
# H3: same west column, surface via further south (74.25,6.15), hop longer
price2('H3 west column x72.30, surface (74.25,6.15)',
       [('In2', [(74.25, 16.438), (74.10, 17.05), (72.90, 17.15), (72.30, 16.40),
                 (72.30, 6.55), (73.30, 6.20), (74.25, 6.15)]),
        ('F', [(74.25, 6.15), (74.48, 5.60)])],
       (74.25, 6.15), (74.60, 5.30), items)
