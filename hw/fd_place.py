#!/usr/bin/env python3
"""Force-directed placement (repo tooling).

Footprints are nodes; every net contributes springs between its pads
(star-to-centroid per net, so power nets stay linear; GND is
down-weighted 0.1 because the pour carries it). Hard separation:
a move is rejected if it creates a gated courtyard pair, takes a
courtyard off-board, or puts a courtyard into the HV creepage slot.
Optimization: cluster-seeded start (the input board's positions),
then simulated-annealing sweeps (spring steps + jitter + same-
padcount swaps), then a rotation stage that tries 90-degree flips
of two-pad passives. Score = pad-census star total (sum over nets
of pad distances to the net centroid), printed before/after.

Anchored (never moved): mounting holes, edge connectors J1/J2,
shield can SH1 with the APD D1 and TIA U1 under it, alt-APD D2,
test header J3.

Usage: xvfb-run -a python3 hw/fd_place.py IN OUT [SWEEPS]
"""
import sys, math, random
sys.path.insert(0, 'hw')
import pcbnew
import check_pcb

MM = 1_000_000
SLOT = (12.0, 23.6, 46.0, 25.1)
BOARD = (0.0, -45.0, 100.0, 80.0)
FIXED = {'MH1', 'MH2', 'MH3', 'MH4', 'MH5', 'MH6', 'J1', 'J2', 'SH1',
         'D1', 'D2', 'U1', 'J3'}


def pad_data(board):
    from collections import defaultdict
    net_pads, part_pads = defaultdict(list), defaultdict(list)
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


def net_star(pads):
    if len(pads) < 2 or len(set(p[0] for p in pads)) < 2:
        return 0.0
    cx = sum(p[1] for p in pads) / len(pads)
    cy = sum(p[2] for p in pads) / len(pads)
    return sum(math.hypot(p[1] - cx, p[2] - cy) for p in pads)


def total_star(net_pads):
    return sum(net_star(p) for p in net_pads.values() if len(p) <= 40)


def _cy_poly(fp):
    layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    try:
        poly = fp.GetCourtyard(layer)
    except Exception:
        poly = None
    if poly is None or poly.OutlineCount() == 0:
        return check_pcb._fallback_courtyard(fp, fp.IsFlipped()), True
    return poly, False


def collisions_of(board, ref):
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    fp = fps[ref]
    poly, fb = _cy_poly(fp)
    if fb:
        return set()
    bb = poly.BBox()
    out = set()
    for ref2, fp2 in fps.items():
        if ref2 == ref or fp2.IsFlipped() != fp.IsFlipped():
            continue
        poly2, fb2 = _cy_poly(fp2)
        if fb2 or not bb.Intersects(poly2.BBox()):
            continue
        inter = pcbnew.SHAPE_POLY_SET(poly)
        inter.BooleanIntersection(poly2, pcbnew.SHAPE_POLY_SET.PM_FAST)
        area = sum(inter.Outline(k).Area()
                   for k in range(inter.OutlineCount()))
        if area / 1e12 > 0.001:
            out.add(ref2)
    return out


def cy_bbox(fp):
    poly, _ = _cy_poly(fp)
    bb = poly.BBox()
    return (bb.GetLeft() / MM, bb.GetTop() / MM,
            bb.GetRight() / MM, bb.GetBottom() / MM)


def placement_ok(fp):
    x0, y0, x1, y1 = cy_bbox(fp)
    if x0 < BOARD[0] or y0 < BOARD[1] or x1 > BOARD[2] or y1 > BOARD[3]:
        return False
    if not (x1 < SLOT[0] or x0 > SLOT[2] or y1 < SLOT[1]
            or y0 > SLOT[3]):
        return False
    return True


def set_pos(fp, x, y):
    fp.SetPosition(pcbnew.VECTOR2I(int(x * MM), int(y * MM)))


class State:
    def __init__(self, board):
        self.board = board
        self.fps = {fp.GetReference(): fp
                    for fp in board.GetFootprints()}
        self.refresh()

    def refresh(self):
        self.net_pads, self.part_pads = pad_data(self.board)
        self.stars = {n: (net_star(p) if len(p) <= 40 else 0.0)
                      for n, p in self.net_pads.items()}
        self.total = sum(self.stars.values())
        self.nets_of = {r: set(n for n, _, _ in pads)
                        for r, pads in self.part_pads.items()}

    def star_of(self, nets):
        np_, _ = pad_data(self.board)
        return sum(net_star(np_[n]) if len(np_[n]) <= 40 else 0.0
                   for n in nets if n in np_)


def main():
    src, out = sys.argv[1], sys.argv[2]
    sweeps = int(sys.argv[3]) if len(sys.argv) > 3 else 42
    random.seed(20261106)
    board = pcbnew.LoadBoard(src)
    st = State(board)
    movable = [r for r in st.fps if r not in FIXED]
    by_padcount = {}
    for r in movable:
        by_padcount.setdefault(len(st.part_pads.get(r, [])), []).append(r)
    print(f'start star {st.total:.0f} mm, movable {len(movable)}',
          flush=True)
    T0, T1 = 26.0, 0.4
    for sweep in range(sweeps):
        T = T0 * (T1 / T0) ** (sweep / max(1, sweeps - 1))
        order = movable[:]
        random.shuffle(order)
        acc = 0
        for ref in order:
            fp = st.fps[ref]
            nets = st.nets_of.get(ref, set())
            before = sum(st.stars.get(n, 0.0) for n in nets)
            pos = fp.GetPosition()
            x0, y0 = pos.x / MM, pos.y / MM
            tx = ty = tw = 0.0
            for net, x, y in st.part_pads[ref]:
                w = 0.1 if net == 'GND' else 1.0
                partners = [(a, b) for (r2, a, b) in st.net_pads[net]
                            if r2 != ref]
                if not partners:
                    continue
                tx += w * sum(p[0] for p in partners) / len(partners)
                ty += w * sum(p[1] for p in partners) / len(partners)
                tw += w
            if tw == 0:
                continue
            tx /= tw; ty /= tw
            frac = random.uniform(0.35, 1.05)
            jit = T * 0.14
            nx = round((x0 + frac * (tx - x0)
                        + random.uniform(-jit, jit)) * 4) / 4
            ny = round((y0 + frac * (ty - y0)
                        + random.uniform(-jit, jit)) * 4) / 4
            if abs(nx - x0) < 0.24 and abs(ny - y0) < 0.24:
                continue
            set_pos(fp, nx, ny)
            if collisions_of(board, ref) or not placement_ok(fp):
                set_pos(fp, x0, y0)
                continue
            d = st.star_of(nets) - before
            if d <= 0 or random.random() < math.exp(-d / max(T, 0.05)):
                st.refresh()
                acc += 1
            else:
                set_pos(fp, x0, y0)
        sw = 0
        for _ in range(18):
            group = random.choice(list(by_padcount.values()))
            if len(group) < 2:
                continue
            a, b = random.sample(group, 2)
            nets = st.nets_of.get(a, set()) | st.nets_of.get(b, set())
            before = sum(st.stars.get(n, 0.0) for n in nets)
            pa, pb = st.fps[a].GetPosition(), st.fps[b].GetPosition()
            set_pos(st.fps[a], pb.x / MM, pb.y / MM)
            set_pos(st.fps[b], pa.x / MM, pa.y / MM)
            if (collisions_of(board, a) or collisions_of(board, b)
                    or not placement_ok(st.fps[a])
                    or not placement_ok(st.fps[b])):
                set_pos(st.fps[a], pa.x / MM, pa.y / MM)
                set_pos(st.fps[b], pb.x / MM, pb.y / MM)
                continue
            d = st.star_of(nets) - before
            if d <= 0 or random.random() < math.exp(-d / max(T, 0.05)):
                st.refresh()
                sw += 1
            else:
                set_pos(st.fps[a], pa.x / MM, pa.y / MM)
                set_pos(st.fps[b], pb.x / MM, pb.y / MM)
        print(f'sweep {sweep}: T {T:.1f}, {acc} moves, {sw} swaps, '
              f'star {st.total:.0f}', flush=True)
        board.Save(out)

    # ---- rotation stage: 90-degree flips of two-pad passives ----
    st.refresh()
    rotated = 0
    for ref in movable:
        fp = st.fps[ref]
        if len(st.part_pads.get(ref, [])) != 2:
            continue
        nets = st.nets_of.get(ref, set())
        before = sum(st.stars.get(n, 0.0) for n in nets)
        old = fp.GetOrientationDegrees()
        fp.SetOrientationDegrees(old + 90)
        if collisions_of(board, ref) or not placement_ok(fp):
            fp.SetOrientationDegrees(old)
            continue
        if st.star_of(nets) < before - 0.3:
            st.refresh()
            rotated += 1
        else:
            fp.SetOrientationDegrees(old)
    print(f'rotation stage: {rotated} passives rotated, star '
          f'{st.total:.0f}', flush=True)
    board.Save(out)
    pairs, _blind = check_pcb.courtyard_pairs(board)
    gated = [p for p in pairs if not p[4]]
    print(f'final: star {st.total:.0f} mm, gated courtyard pairs '
          f'{len(gated)}', flush=True)
    print('saved', out, flush=True)


if __name__ == '__main__':
    main()
