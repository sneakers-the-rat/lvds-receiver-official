#!/usr/bin/env python3
"""Force-directed placement, whole board: connection springs
(per-net pad star) + hard separation (gated courtyard pairs), with
simulated-annealing acceptance and same-padcount swaps. Anchored:
mounting holes, edge connectors J1/J2, shield can SH1 + the APD/TIA
under it, alt-APD D2, test header J3. Slot + board bounds are hard.

Usage: xvfb-run -a python3 scratch/fdplace.py IN OUT [SWEEPS]
"""
import sys, math, random
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch')
import pcbnew
from replace import (fp_map, pad_data, collisions_of, placement_ok,
                     set_pos, MM)

random.seed(20261106)
FIXED = {'MH1', 'MH2', 'MH3', 'MH4', 'MH5', 'MH6', 'J1', 'J2', 'SH1',
         'D1', 'D2', 'U1', 'J3'}


def net_star(pads):
    if len(pads) < 2 or len(set(p[0] for p in pads)) < 2:
        return 0.0
    cx = sum(p[1] for p in pads) / len(pads)
    cy = sum(p[2] for p in pads) / len(pads)
    return sum(math.hypot(p[1] - cx, p[2] - cy) for p in pads)


class State:
    def __init__(self, board):
        self.board = board
        self.fps = fp_map(board)
        self.refresh()

    def refresh(self):
        self.net_pads, self.part_pads = pad_data(self.board)
        self.stars = {}
        self.total = 0.0
        for net, pads in self.net_pads.items():
            s = net_star(pads) if len(pads) <= 40 else 0.0
            self.stars[net] = s
            self.total += s
        self.nets_of = {}
        for ref, pads in self.part_pads.items():
            self.nets_of[ref] = set(n for n, _, _ in pads)

    def delta_for(self, refs):
        nets = set()
        for r in refs:
            nets |= self.nets_of.get(r, set())
        return nets

    def star_of_nets(self, nets):
        np_, _ = pad_data(self.board)
        return sum(net_star(np_[n]) if len(np_[n]) <= 40 else 0.0
                   for n in nets if n in np_)


def main():
    src, out = sys.argv[1], sys.argv[2]
    sweeps = int(sys.argv[3]) if len(sys.argv) > 3 else 42
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
            nets = st.delta_for([ref])
            before = sum(st.stars.get(n, 0.0) for n in nets)
            pos = fp.GetPosition()
            x0, y0 = pos.x / MM, pos.y / MM
            # spring target: partner-pad centroid (GND downweighted)
            pads = st.part_pads[ref]
            tx = ty = tw = 0.0
            for net, x, y in pads:
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
            after = st.star_of_nets(nets)
            d = after - before
            if d <= 0 or random.random() < math.exp(-d / max(T, 0.05)):
                st.refresh()
                acc += 1
            else:
                set_pos(fp, x0, y0)
        # swaps of same-padcount parts
        sw = 0
        for _ in range(18):
            n = random.choice(list(by_padcount))
            group = by_padcount[n]
            if len(group) < 2:
                continue
            a, b = random.sample(group, 2)
            nets = st.delta_for([a, b])
            before = sum(st.stars.get(n_, 0.0) for n_ in nets)
            pa, pb = st.fps[a].GetPosition(), st.fps[b].GetPosition()
            set_pos(st.fps[a], pb.x / MM, pb.y / MM)
            set_pos(st.fps[b], pa.x / MM, pa.y / MM)
            if (collisions_of(board, a) or collisions_of(board, b)
                    or not placement_ok(st.fps[a])
                    or not placement_ok(st.fps[b])):
                set_pos(st.fps[a], pa.x / MM, pa.y / MM)
                set_pos(st.fps[b], pb.x / MM, pb.y / MM)
                continue
            after = st.star_of_nets(nets)
            d = after - before
            if d <= 0 or random.random() < math.exp(-d / max(T, 0.05)):
                st.refresh()
                sw += 1
            else:
                set_pos(st.fps[a], pa.x / MM, pa.y / MM)
                set_pos(st.fps[b], pb.x / MM, pb.y / MM)
        print(f'sweep {sweep}: T {T:.1f}, accepted {acc} moves, '
              f'{sw} swaps, star {st.total:.0f}', flush=True)
        board.Save(out)
    print('saved', out, flush=True)


if __name__ == '__main__':
    main()
