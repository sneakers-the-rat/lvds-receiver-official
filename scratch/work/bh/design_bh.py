#!/usr/bin/env python3
"""bh design pricer: USB_RST arrival composite on exp257, exact geometry.
Family: ULPI_CK via move x CK In2 escape shape x BIST/MOSI nudges x
USB_RST surface-via grid + F hop into U6.40 south end.
Rules: hw/gridroute pair_clr/via_clr. Output: top combos to file."""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
import gridroute as G

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
OUT = '/home/hatch/workspace/pdlvds-route/scratch/work/bh/design_bh_out.txt'
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


def near(pool, x0, y0, x1, y1, pad=1.3):
    out = []
    for it in pool:
        if it.kind == 'via':
            pts = [it.a]
        elif it.kind == 'trk':
            pts = [it.a, it.b]
        else:
            pts = [(it.rect[0], it.rect[1]), (it.rect[2], it.rect[3])]
        if any(x0 - pad <= p[0] <= x1 + pad and y0 - pad <= p[1] <= y1 + pad for p in pts):
            out.append(it)
    return out


def m_trk(a, b, layer, hw, pool, skip):
    loc = near(pool, min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
    worst = (9.9, '')
    for it in loc:
        if it.net == skip:
            continue
        if it.kind == 'via':
            m = pt_seg(it.a, a, b) - hw - it.hw - G.via_clr(it.net)
            d = f'via {it.net}@{it.a}'
        elif it.kind == 'trk' and it.layer == layer:
            m = seg_seg(a, b, it.a, it.b) - hw - it.hw - G.pair_clr(it.net, layer, it.layer)
            d = f'trk {it.net} {it.a}->{it.b}'
        elif it.kind == 'pad' and it.layer == layer:
            m = seg_rect(a, b, it.rect) - hw - G.pair_clr(it.net, layer, layer)
            d = f'pad {it.net} {it.rect}'
        else:
            continue
        if m < worst[0]:
            worst = (m, d)
    return worst


def m_via(c, r, pool, skip):
    loc = near(pool, c[0], c[1], c[0], c[1])
    worst = (9.9, '')
    for it in loc:
        if it.net == skip:
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


def is_ck_old(it):
    if it.net != 'ULPI_CK':
        return False
    if it.kind == 'via':
        return close(it.a, (75.125, 5.875))
    if it.kind == 'trk' and it.layer == 'F':
        return close(it.a, (75.125, 5.875)) or close(it.b, (75.125, 5.875))
    if it.kind == 'trk' and it.layer == 'In2':
        return (close(it.a, (75.125, 5.875)) or close(it.b, (75.125, 5.875)) or
                (close(it.a, (74.875, 6.125)) and close(it.b, (74.625, 6.375))) or
                (close(it.b, (74.875, 6.125)) and close(it.a, (74.625, 6.375))))
    return False


BIST_WIN = [(73.875, 6.125), (74.125, 5.875), (74.375, 5.625),
            (74.625, 5.375), (74.875, 5.125), (75.375, 5.125), (75.625, 4.875)]


def is_bist_win(it):
    if it.net != 'BIST_DRV' or it.kind != 'trk' or it.layer != 'In2':
        return False
    return any(close(it.a, p) for p in BIST_WIN) and any(close(it.b, p) for p in BIST_WIN)


def is_mosi_seg(it):
    return it.net == 'SPI_MOSI' and it.kind == 'trk' and it.layer == 'In2' and \
        ((close(it.a, (73.4, 5.2)) and close(it.b, (75.1, 4.55))) or
         (close(it.b, (73.4, 5.2)) and close(it.a, (75.1, 4.55))))


def trk(net, layer, a, b, w):
    return G.Item(net, 'trk', layer=layer, a=a, b=b, hw=w / 2)


def via(net, c, d):
    return G.Item(net, 'via', a=c, hw=d / 2)


CK_VIAS = [(75.45, 5.9), (75.55, 5.85), (75.75, 5.75), (75.9, 5.7)]
CK_ESCAPES = {
    'E1': lambda v: [v, (75.0, 6.45), (74.625, 6.375)],
    'E2': lambda v: [v, (75.35, 6.55), (74.95, 6.75), (74.625, 6.375)],
    'E3': lambda v: [v, (74.95, 6.30), (74.625, 6.375)],
}
results = []
for cv in CK_VIAS:
    for ename, efn in CK_ESCAPES.items():
        esc = efn(cv)
        for bdy in (0.0, -0.145):
            for mdy in (0.0, -0.10):
                pool = [it for it in BASE if not is_ck_old(it)]
                if bdy:
                    pool = [it for it in pool if not is_bist_win(it)]
                    pts = [(x, y + bdy) if 0 < i < len(BIST_WIN) - 1 else (x, y)
                           for i, (x, y) in enumerate(BIST_WIN)]
                    for a, b in zip(pts, pts[1:]):
                        pool.append(trk('BIST_DRV', 'In2', a, b, 0.25))
                if mdy:
                    pool = [it for it in pool if not is_mosi_seg(it)]
                    pool.append(trk('SPI_MOSI', 'In2', (71.9, 7.25), (73.4, 5.2 + mdy), 0.20))
                    pool.append(trk('SPI_MOSI', 'In2', (73.4, 5.2 + mdy), (75.1, 4.55 + mdy), 0.20))
                    pool.append(trk('SPI_MOSI', 'In2', (75.1, 4.55 + mdy), (76.4, 3.35), 0.20))
                ck_new = [via('ULPI_CK', cv, 0.6),
                          trk('ULPI_CK', 'F', (75.25, 5.162), cv, 0.20)]
                for a, b in zip(esc, esc[1:]):
                    ck_new.append(trk('ULPI_CK', 'In2', a, b, 0.25))
                pool += ck_new
                # price CK new + nudged neighbours
                pre = []
                m, d = m_via(cv, 0.30, pool, 'ULPI_CK')
                pre.append((m, f'CKvia {d}'))
                m, d = m_trk((75.25, 5.162), cv, 'F', 0.10, pool, 'ULPI_CK')
                pre.append((m, f'CKF {d}'))
                for a, b in zip(esc, esc[1:]):
                    m, d = m_trk(a, b, 'In2', 0.125, pool, 'ULPI_CK')
                    pre.append((m, f'CKesc {d}'))
                if bdy:
                    pts = [(x, y + bdy) if 0 < i < len(BIST_WIN) - 1 else (x, y)
                           for i, (x, y) in enumerate(BIST_WIN)]
                    for a, b in zip(pts, pts[1:]):
                        m, d = m_trk(a, b, 'In2', 0.125, pool, 'BIST_DRV')
                        pre.append((m, f'BIST {d}'))
                if mdy:
                    for a, b in [((73.4, 5.2 + mdy), (75.1, 4.55 + mdy))]:
                        m, d = m_trk(a, b, 'In2', 0.10, pool, 'SPI_MOSI')
                        pre.append((m, f'MOSI {d}'))
                pre_min = min(pre)
                if pre_min[0] < -0.02:
                    results.append((pre_min[0], cv, ename, bdy, mdy, None,
                                    f'pre: {pre_min[1]} {pre_min[0]:+.3f}'))
                    continue
                # RST surface via grid
                best = None
                sx = 74.62
                while sx <= 75.05:
                    sy = 5.55
                    while sy <= 6.32:
                        s = (round(sx, 2), round(sy, 2))
                        cand = list(pre)
                        m, d = m_via(s, 0.25, pool, 'USB_RST')
                        cand.append((m, f'RSTvia {d}'))
                        hop = [s, (74.78, 5.50), (74.78, 5.30)]
                        for a, b in zip(hop, hop[1:]):
                            m, d = m_trk(a, b, 'F', 0.10, pool, 'USB_RST')
                            cand.append((m, f'hop {d}'))
                        stubs = []
                        for frm in [(s[0] - 0.85, s[1] + 0.25), (s[0], s[1] + 0.9),
                                    (s[0] - 0.6, s[1] + 0.55), (s[0] + 0.7, s[1] + 0.5)]:
                            m, d = m_trk(frm, s, 'In2', 0.10, pool, 'USB_RST')
                            stubs.append((m, frm, d))
                        stubs.sort()
                        cand.append((stubs[-1][0], f'stubW {stubs[-1][2]}'))
                        sc = min(cand)
                        if best is None or sc[0] > best[0][0]:
                            best = (sc, s, stubs[-1][1])
                        sy += 0.077
                    sx += 0.07
                results.append((best[0][0], cv, ename, bdy, mdy, best[1],
                                f'{best[0][1]} stubfrom {best[2]}'))
results.sort(key=lambda r: -r[0])
with open(OUT, 'w') as f:
    for r in results:
        f.write(f'{r[0]:+.3f} CKvia={r[1]} esc={r[2]} bist_dy={r[3]} mosi_dy={r[4]} '
                f'RSTvia={r[5]} bind: {r[6]}\n')
print('combos:', len(results))
for r in results[:10]:
    print(f'{r[0]:+.3f} CKvia={r[1]} esc={r[2]} bist={r[3]} mosi={r[4]} RSTvia={r[5]} :: {r[6]}')
