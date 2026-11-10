#!/usr/bin/env python3
"""bm gate: exact-geometry DRC-class margins vs gridroute items.
KiCad binding clearance: 0.20 default, 0.25 vs power (check_pcb class).
In2-In2 uses 0.20 here (the 0.30 figure is a check_pcb census band,
not a DRC gate — proven on exp257). Pads as rects (conservative)."""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G


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
    edges = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
             ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    if (x0 <= a[0] <= x1 and y0 <= a[1] <= y1) or (x0 <= b[0] <= x1 and y0 <= b[1] <= y1):
        return 0.0
    if any(seg_seg(a, b, e0, e1) == 0.0 for e0, e1 in edges):
        return 0.0
    return min(pt_rect(a, r), pt_rect(b, r),
               min(pt_seg(c, a, b) for c in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))


def clr(net):
    return 0.25 if G.is_power(net) else 0.20


def margin_trk(a, b, layer, net, items, hw=0.10, skip=None):
    out = []
    for it in items:
        if it.net == net:
            continue
        if skip and skip(it):
            continue
        if it.kind == 'via':
            m = pt_seg(it.a, a, b) - hw - it.hw - clr(it.net)
            out.append((m, f'via {it.net}@{tuple(round(v,2) for v in it.a)}'))
        elif it.kind == 'trk' and it.layer == layer:
            m = seg_seg(a, b, it.a, it.b) - hw - it.hw - clr(it.net)
            out.append((m, f'trk {it.net} {it.a}->{it.b}'))
        elif it.kind == 'pad' and it.layer == layer:
            m = seg_rect(a, b, it.rect) - hw - clr(it.net)
            out.append((m, f'pad {it.net} rect{it.rect}'))
    return sorted(out)


def margin_via(c, net, items, r=0.25, skip=None):
    out = []
    for it in items:
        if it.net == net:
            continue
        if skip and skip(it):
            continue
        if it.kind == 'via':
            d = math.hypot(c[0] - it.a[0], c[1] - it.a[1])
            out.append((d - r - it.hw - clr(it.net), f'via {it.net}@{tuple(round(v,2) for v in it.a)}'))
        elif it.kind == 'trk':
            d = pt_seg(c, it.a, it.b)
            out.append((d - r - it.hw - clr(it.net), f'trk[{it.layer}] {it.net} {it.a}->{it.b}'))
        elif it.kind == 'pad':
            d = pt_rect(c, it.rect)
            out.append((d - r - clr(it.net), f'pad[{it.layer}] {it.net} rect{it.rect}'))
    return sorted(out)


def report(label, margins, n=4):
    neg = [m for m in margins if m[0] < 0]
    print(f'{label}: negatives={len(neg)} worst={[(round(m,3), d) for m, d in margins[:n]]}')
    return neg
