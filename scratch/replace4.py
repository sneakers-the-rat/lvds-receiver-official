#!/usr/bin/env python3
"""Re-placement round 3: retry rejected anchors at adjusted spots,
then relaxation with TOTAL-star acceptance (a move lands if the sum
of all net star lengths drops), two step sizes.

Usage: xvfb-run -a python3 scratch/replace2.py IN OUT
"""
import sys, math
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch')
import pcbnew
import check_pcb
from replace import (fp_map, pad_data, total_star, mean_partner_dist,
                     gated_pairs, collisions_of, placement_ok, set_pos,
                     FIXED, MM)

ANCHORS2 = {
    'C17': (95.75, -13.5), 'D7': (95.75, -7), 'D6': (95.75, -0.5),
    'R44': (91, 10), 'R45': (88, 10), 'C18': (91, 8.5),
}


def main():
    src, out = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard(src)
    fps = fp_map(board)
    net_pads, part_pads = pad_data(board)
    print(f'start star: {total_star(net_pads):.0f} mm', flush=True)
    for ref, (x, y) in ANCHORS2.items():
        fp = fps.get(ref)
        if fp is None:
            continue
        old = fp.GetPosition()
        set_pos(fp, x, y)
        bad = collisions_of(board, ref)
        if bad or not placement_ok(fp):
            set_pos(fp, old.x / MM, old.y / MM)
            print(f'  anchor {ref} -> ({x},{y}) REJECTED {bad}', flush=True)
        else:
            print(f'  anchor {ref} -> ({x},{y}) ok', flush=True)
    net_pads, part_pads = pad_data(board)
    print(f'after anchors star: {total_star(net_pads):.0f}', flush=True)
    board.Save(out)

    order = [r for r in fps if r not in FIXED]
    for rnd, frac in enumerate((0.5, 0.25, 0.5)):
        moved = 0
        star_now = total_star(pad_data(board)[0])
        for ref in order:
            fp = fps[ref]
            net_pads, part_pads = pad_data(board)
            pads = part_pads[ref]
            if not pads:
                continue
            tx = ty = tw = 0.0
            for net, x, y in pads:
                w = 0.1 if net == 'GND' else 1.0
                partners = [(x2, y2) for (r2, x2, y2) in net_pads[net]
                            if r2 != ref]
                if not partners:
                    continue
                tx += w * sum(p[0] for p in partners) / len(partners)
                ty += w * sum(p[1] for p in partners) / len(partners)
                tw += w
            if tw == 0:
                continue
            tx /= tw; ty /= tw
            pos = fp.GetPosition()
            cx0, cy0 = pos.x / MM, pos.y / MM
            nx = round((cx0 + frac * (tx - cx0)) * 4) / 4
            ny = round((cy0 + frac * (ty - cy0)) * 4) / 4
            if abs(nx - cx0) < 0.24 and abs(ny - cy0) < 0.24:
                continue
            set_pos(fp, nx, ny)
            star_new = total_star(pad_data(board)[0])
            if (star_new < star_now - 0.5 and not collisions_of(board, ref)
                    and placement_ok(fp)):
                star_now = star_new
                moved += 1
            else:
                set_pos(fp, cx0, cy0)
        print(f'round {rnd} (frac {frac}): moved {moved}, star '
              f'{star_now:.0f}', flush=True)
        board.Save(out)
    print('saved', out, flush=True)


if __name__ == '__main__':
    main()
