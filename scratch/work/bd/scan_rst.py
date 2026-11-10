"""scan_rst: the ONE bounded scan the parent approved.

Question: does any layer-sequence + corridor exist for USB_RST on
exp257 if {DM_PHY F loop, ULPI_DIR journey, GND via (73.434,17.685),
ULPI_NXT escape} may be jointly re-laid?

Design (single, declared in advance): rasterize the district
x[70.0,77.6] y[3.4,20.6] at 0.05 pitch with referee-class inflation
(hw/gridroute.py). The four partners' re-lay spans are removed;
their kept tails/pads stay as obstacles for the other nets. Route
the five nets sequentially (terminals below) under 6 declared
orders; the GND via is an outer loop over legal cells ranked by
distance from its current position (current first, cap 14). First
full success wins and is written to rst_config.json -- a
configuration to BUILD, not a verdict.
"""
import json
import math
import sys

sys.path.insert(0, 'hw')
import gridroute as GR

BOARD = 'hw/pdlvds_rx.exp257.kicad_pcb'
DIST = (70.0, 3.4, 77.6, 20.6)
POCKET = (73.9, 16.7, 75.5, 19.5)     # NXT re-lay box
DMBOX = (73.4, 16.9, 74.3, 19.3)      # DM F loop re-lay box
DIRBOX = (71.0, 16.4, 76.0, 19.6)     # DIR journey re-lay box
PARTNERS = ('DM_PHY', 'ULPI_DIR', 'ULPI_NXT')
ALL4 = PARTNERS + ('USB_RST',)
MAX_ATTEMPTS = 48
TIME_BUDGET_S = 1500
TERM = {
    'ULPI_NXT': ((75.25, 16.875, 'F'), (74.5, 19.25, 'In2'), 0.10),
    'ULPI_DIR': ((75.75, 16.875, 'F'), (71.375, 19.125, 'B'), 0.10),
    'DM_PHY': ((73.562, 17.0, 'F'), (73.625, 19.125, 'F'), 0.125),
    'USB_RST': ((74.25, 16.875, 'F'), (74.75, 5.7, 'F'), 0.10),
}
ORDERS = [
    ('ULPI_NXT', 'ULPI_DIR', 'DM_PHY', 'USB_RST'),
    ('ULPI_NXT', 'ULPI_DIR', 'USB_RST', 'DM_PHY'),
    ('ULPI_NXT', 'USB_RST', 'ULPI_DIR', 'DM_PHY'),
    ('USB_RST', 'ULPI_NXT', 'ULPI_DIR', 'DM_PHY'),
    ('ULPI_DIR', 'ULPI_NXT', 'DM_PHY', 'USB_RST'),
    ('DM_PHY', 'ULPI_NXT', 'ULPI_DIR', 'USB_RST'),
]
GND_NOW = (73.434, 17.685)


def inside(it, box):
    x0, y0, x1, y1 = box
    pts = []
    if it.kind == 'via':
        pts = [it.a]
    elif it.kind == 'trk':
        pts = [it.a, it.b]
    elif it.kind == 'pad':
        pts = [(it.rect[0], it.rect[1]), (it.rect[2], it.rect[3])]
    return all(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in pts)


def classify(items):
    """-> (fixed, kept{net: [items]}, relay_count)"""
    fixed, kept = [], {n: [] for n in ALL4}
    relay = 0
    for it in items:
        if it.net == 'USB_RST':
            kept['USB_RST'].append(it)
            continue
        if it.net == 'GND' and it.kind == 'via' and \
                math.hypot(it.a[0] - GND_NOW[0], it.a[1] - GND_NOW[1]) < 0.01:
            relay += 1
            continue  # the movable GND via: candidate-placed
        if it.net == 'DM_PHY':
            if it.kind == 'via' or not inside(it, DMBOX):
                kept['DM_PHY'].append(it)
            else:
                relay += 1
        elif it.net == 'ULPI_DIR':
            if not inside(it, DIRBOX):
                kept['ULPI_DIR'].append(it)
            else:
                relay += 1
        elif it.net == 'ULPI_NXT':
            if not inside(it, POCKET):
                kept['ULPI_NXT'].append(it)
            else:
                relay += 1
        elif it.net in PARTNERS:
            kept[it.net].append(it)
        else:
            fixed.append(it)
    return fixed, kept, relay


def near_district(it):
    x0, y0, x1, y1 = DIST
    m = 1.0
    if it.kind == 'pad':
        return not (it.rect[2] < x0 - m or it.rect[0] > x1 + m or
                    it.rect[3] < y0 - m or it.rect[1] > y1 + m)
    pts = [it.a] if it.kind == 'via' else [it.a, it.b]
    return any(x0 - m <= p[0] <= x1 + m and y0 - m <= p[1] <= y1 + m
               for p in pts) or \
        (min(p[0] for p in pts) <= x1 + m and
         max(p[0] for p in pts) >= x0 - m and
         min(p[1] for p in pts) <= y1 + m and
         max(p[1] for p in pts) >= y0 - m)


def build_base(fixed, hw):
    r = GR.Raster(DIST[0], DIST[1], DIST[2], DIST[3],
                  pitch=0.05, eps=0.02, routed_hw=hw)
    for it in fixed:
        r.add_item(it)
    return r


def free_cell(raster, x, y, layer, maxr=2):
    i0, j0 = raster.cell(x, y)
    grid = raster.track[layer]
    for rad in range(0, maxr + 1):
        for dj in range(-rad, rad + 1):
            for di in range(-rad, rad + 1):
                if max(abs(di), abs(dj)) != rad:
                    continue
                i, j = i0 + di, j0 + dj
                if 0 <= i < raster.nx and 0 <= j < raster.ny and \
                        not grid[j, i]:
                    return raster.centre(i, j)
    return None


def attempt(base10, base125, kept, gnd_xy, order):
    routed = {}
    for net in order:
        base = base125 if TERM[net][2] > 0.11 else base10
        r = base.copy()
        r.add_item(GR.Item('GND', 'via', a=gnd_xy, hw=0.25))
        for other in ALL4:
            if other != net:
                for it in kept[other]:
                    r.add_item(it, routed_hw=TERM[net][2])
        for pnet, rd in routed.items():
            r.add_routed(pnet, rd['flat'], rd['vias'], hw=rd['hw'])
        (s, g, hw) = TERM[net]
        sc = free_cell(r, s[0], s[1], s[2])
        gc = free_cell(r, g[0], g[1], g[2])
        if sc is None or gc is None:
            return None, f'{net}: terminal blocked'
        path = GR.astar(r, (sc[0], sc[1], s[2]), (gc[0], gc[1], g[2]))
        if path is None:
            return None, f'{net}: no path'
        segs, vias = GR.path_to_geometry(path)
        flat = [(L, a, b) for (L, pts) in segs
                for a, b in zip(pts, pts[1:])]
        routed[net] = {'segs': segs, 'flat': flat, 'vias': vias,
                       'hw': hw}
    return routed, 'ok'


def main():
    items = GR.load_items(BOARD, keep=near_district)
    fixed, kept, relay = classify(items)
    print(f'items near district: {len(items)}; fixed {len(fixed)}; '
          f're-lay spans removed {relay}; kept: ' +
          ', '.join(f'{n}={len(v)}' for n, v in kept.items()))
    base10 = build_base(fixed, 0.10)
    base125 = build_base(fixed, 0.125)
    # GND via candidates: current first, then legal cells by distance
    cands = [GND_NOW]
    cells = []
    for j in range(base10.ny):
        for i in range(base10.nx):
            if not base10.via[j, i]:
                cx, cy = base10.centre(i, j)
                if 72.6 <= cx <= 75.4 and 16.95 <= cy <= 19.3:
                    cells.append((math.hypot(cx - GND_NOW[0],
                                             cy - GND_NOW[1]), cx, cy))
    cells.sort()
    seen = {GND_NOW}
    for (_, cx, cy) in cells:
        key = (round(cx, 1), round(cy, 1))
        if key in seen:
            continue
        seen.add(key)
        cands.append((cx, cy))
        if len(cands) >= 14:
            break
    print(f'GND via candidates: {len(cands)}')
    import time
    t0 = time.time()
    fails = []
    n_try = 0
    for gnd in cands:
        for order in ORDERS:
            if n_try >= MAX_ATTEMPTS or time.time() - t0 > TIME_BUDGET_S:
                print(f'budget stop after {n_try} attempts')
                break
            n_try += 1
            routed, why = attempt(base10, base125, kept, gnd, order)
            if routed is None:
                fails.append((gnd, order, why))
                continue
            print(f'SUCCESS gnd={gnd} order={order}')
            out = {'gnd_via': gnd, 'order': list(order), 'nets': {}}
            for net, rd in routed.items():
                segs, vias, hw = rd['segs'], rd['vias'], rd['hw']
                out['nets'][net] = {
                    'hw': hw,
                    'segs': [[L, [[round(x, 3), round(y, 3)]
                                  for (x, y) in pts]]
                             for (L, pts) in segs if len(pts) > 1],
                    'vias': [[round(x, 3), round(y, 3)] for (x, y) in vias],
                }
                nseg = sum(len(p) - 1 for (_, p) in segs if len(p) > 1)
                print(f'  {net}: {nseg} segs, {len(vias)} vias')
            with open('scratch/work/bd/rst_config.json', 'w') as f:
                json.dump(out, f, indent=1)
            print('wrote scratch/work/bd/rst_config.json')
            return
        if n_try >= MAX_ATTEMPTS or time.time() - t0 > TIME_BUDGET_S:
            break
    print(f'NO CONFIGURATION in {len(fails)} attempts')
    from collections import Counter
    print(Counter(w for (_, _, w) in fails))


if __name__ == '__main__':
    main()
