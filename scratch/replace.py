#!/usr/bin/env python3
"""Connectivity-driven re-placement experiment.

Loads IN, applies hand-set anchor positions, then runs relaxation
rounds: every movable part is pulled toward the weighted centroid of
its partner pads (non-GND nets weight 1, GND 0.1). A move is accepted
only if (a) the part's own mean partner distance decreases, (b) it
gains no gated courtyard pair, (c) its courtyard bbox stays on-board
and clear of the HV creepage slot. Locality is measured with
scratch/locality.py's method after each round; the best board wins.

Usage: xvfb-run -a python3 scratch/replace.py IN OUT
"""
import sys, math
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch')
import pcbnew
import check_pcb

MM = 1_000_000
SLOT = (12.0, 23.6, 46.0, 25.1)      # x0, y0, x1, y1 — no parts
BOARD = (0.0, -45.0, 100.0, 80.0)

FIXED = {'MH1', 'MH2', 'MH3', 'MH4', 'MH5', 'MH6', 'J1', 'J2', 'SH1',
         'D1', 'D2', 'U1', 'U2', 'U3', 'J3'}

ANCHORS = {   # ref: (x, y) — cluster anchors, hand-set
    'U4': (66, 43), 'C12': (60, 50), 'C13': (60, 36), 'C14': (73, 36),
    'C15': (73, 50), 'R12': (59, 43), 'X2': (66, 33), 'FB1': (54, 43),
    'C50': (56, 50), 'C51': (56, 37),
    'R13': (74, 40), 'R14': (74, 47), 'U5': (81, 43.5),
    'C8': (50, 40.5), 'C9': (50, 45.5),
    'J5': (48, -20),
    'U8': (62, 16), 'C26': (56, 20), 'C27': (56, 12), 'R33': (42, -4),
    'U9': (68, -18), 'R20': (69, -12), 'R21': (69, -9), 'R22': (64, -14),
    'U11': (74, 64), 'L1': (86, 64), 'R35': (67, 59), 'R36': (63, 59),
    'C36': (68, 69), 'R37': (63, 69), 'C28': (70, 57),
    'U13': (30, 57),
    'J4': (93, 26),
    'R17': (70, 21), 'C22': (66, 24), 'C23': (63, 21),
    'C19': (95, -13), 'R15': (95, -17), 'R16': (95, -21), 'TP3': (92, -25),
    'D6': (90, 4), 'D7': (90, 10), 'R44': (90, 13.5), 'R45': (84, 16),
    'C47': (66, -2), 'C49': (88, -12),
}


def fp_map(board):
    return {fp.GetReference(): fp for fp in board.GetFootprints()}


def pad_data(board):
    from collections import defaultdict
    net_pads = defaultdict(list)
    part_pads = defaultdict(list)
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            p = pad.GetPosition()
            x, y = p.x / MM, p.y / MM
            net_pads[net].append((ref, x, y))
            part_pads[ref].append((net, x, y))
    return net_pads, part_pads


def total_star(net_pads):
    tot = 0.0
    for net, pads in net_pads.items():
        refs = set(p[0] for p in pads)
        if len(pads) < 2 or len(refs) < 2 or len(pads) > 40:
            continue
        cx = sum(p[1] for p in pads) / len(pads)
        cy = sum(p[2] for p in pads) / len(pads)
        tot += sum(math.hypot(p[1] - cx, p[2] - cy) for p in pads)
    return tot


def mean_partner_dist(ref, part_pads, net_pads):
    ds = []
    for net, x, y in part_pads[ref]:
        best = None
        for (r2, x2, y2) in net_pads[net]:
            if r2 == ref:
                continue
            d = math.hypot(x - x2, y - y2)
            if best is None or d < best:
                best = d
        if best is not None:
            ds.append(best)
    return sum(ds) / len(ds) if ds else 0.0


def _cy_poly(fp):
    layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    try:
        poly = fp.GetCourtyard(layer)
    except Exception:
        poly = None
    if poly is None or poly.OutlineCount() == 0:
        return check_pcb._fallback_courtyard(fp, fp.IsFlipped()), True
    return poly, False


def gated_pairs(board):
    pairs, _blind = check_pcb.courtyard_pairs(board)
    return {(min(p[0], p[1]), max(p[0], p[1]))
            for p in pairs if not p[4]}


def collisions_of(board, ref):
    """Gated courtyard collisions involving one footprint."""
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    fp = fps[ref]
    poly, fb = _cy_poly(fp)
    if fb:
        return set()
    bb = poly.BBox()
    side = fp.IsFlipped()
    out = set()
    for ref2, fp2 in fps.items():
        if ref2 == ref or fp2.IsFlipped() != side:
            continue
        poly2, fb2 = _cy_poly(fp2)
        if fb2 or not bb.Intersects(poly2.BBox()):
            continue
        inter = pcbnew.SHAPE_POLY_SET(poly)
        inter.BooleanIntersection(poly2, pcbnew.SHAPE_POLY_SET.PM_FAST)
        area = 0.0
        for k in range(inter.OutlineCount()):
            area += inter.Outline(k).Area()
        if area / 1e12 > 0.001:
            out.add(ref2)
    return out


def cy_bbox(fp):
    """Courtyard bbox in mm via pad/body fallback-safe route: use the
    drawn courtyard if present, else the footprint bounding box."""
    poly = fp.GetCourtyard(pcbnew.F_CrtYd)
    if poly.OutlineCount() > 0:
        bb = poly.BBox()
        return (bb.GetLeft() / MM, bb.GetTop() / MM,
                bb.GetRight() / MM, bb.GetBottom() / MM)
    bb = fp.GetBoundingBox()
    return (bb.GetLeft() / MM, bb.GetTop() / MM,
            bb.GetRight() / MM, bb.GetBottom() / MM)


def placement_ok(fp):
    x0, y0, x1, y1 = cy_bbox(fp)
    if x0 < BOARD[0] or y0 < BOARD[1] or x1 > BOARD[2] or y1 > BOARD[3]:
        return False
    # slot: bbox must not intersect the slot rect
    if not (x1 < SLOT[0] or x0 > SLOT[2] or y1 < SLOT[1] or y0 > SLOT[3]):
        return False
    return True


def set_pos(fp, x, y):
    fp.SetPosition(pcbnew.VECTOR2I(int(x * MM), int(y * MM)))


def main():
    src, out = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard(src)
    fps = fp_map(board)
    base_pairs = gated_pairs(board)
    print(f'baseline gated courtyard pairs: {len(base_pairs)}', flush=True)
    net_pads, part_pads = pad_data(board)
    print(f'baseline star total: {total_star(net_pads):.0f} mm', flush=True)

    # ---- anchors ----
    for ref, (x, y) in ANCHORS.items():
        fp = fps.get(ref)
        if fp is None:
            print(f'  anchor {ref}: NOT FOUND', flush=True)
            continue
        old = fp.GetPosition()
        set_pos(fp, x, y)
        bad = collisions_of(board, ref)
        if bad or not placement_ok(fp):
            set_pos(fp, old.x / MM, old.y / MM)
            print(f'  anchor {ref} -> ({x},{y}) REJECTED pairs={bad} '
                  f'ok={placement_ok(fp)}', flush=True)
        else:
            print(f'  anchor {ref} -> ({x},{y}) ok', flush=True)
    net_pads, part_pads = pad_data(board)
    print(f'after anchors star: {total_star(net_pads):.0f} mm, '
          f'gated pairs {len(gated_pairs(board))}', flush=True)
    board.Save(out)

    # ---- relaxation rounds ----
    order = sorted((r for r in fps if r not in FIXED),
                   key=lambda r: -mean_partner_dist(r, part_pads, net_pads))
    for rnd in range(5):
        moved = 0
        net_pads, part_pads = pad_data(board)
        for ref in order:
            fp = fps[ref]
            pads = part_pads[ref]
            if not pads:
                continue
            # weighted partner centroid over this part's pads
            tx = ty = tw = 0.0
            for net, x, y in pads:
                w = 0.1 if net == 'GND' else 1.0
                partners = [(x2, y2) for (r2, x2, y2) in net_pads[net]
                            if r2 != ref]
                if not partners:
                    continue
                cx = sum(p[0] for p in partners) / len(partners)
                cy = sum(p[1] for p in partners) / len(partners)
                tx += w * cx; ty += w * cy; tw += w
            if tw == 0:
                continue
            tx /= tw; ty /= tw
            pos = fp.GetPosition()
            cx0, cy0 = pos.x / MM, pos.y / MM
            d_before = mean_partner_dist(ref, part_pads, net_pads)
            nx = round((cx0 + 0.65 * (tx - cx0)) * 4) / 4
            ny = round((cy0 + 0.65 * (ty - cy0)) * 4) / 4
            if abs(nx - cx0) < 0.24 and abs(ny - cy0) < 0.24:
                continue
            set_pos(fp, nx, ny)
            net_pads2, part_pads2 = pad_data(board)
            d_after = mean_partner_dist(ref, part_pads2, net_pads2)
            gained = collisions_of(board, ref)
            if d_after < d_before - 0.05 and not gained and placement_ok(fp):
                net_pads, part_pads = net_pads2, part_pads2
                moved += 1
            else:
                set_pos(fp, cx0, cy0)
        net_pads, part_pads = pad_data(board)
        print(f'round {rnd}: moved {moved}, star '
              f'{total_star(net_pads):.0f} mm, gated pairs '
              f'{len(gated_pairs(board))}', flush=True)
        board.Save(out)
    print('saved', out, flush=True)


if __name__ == '__main__':
    main()
