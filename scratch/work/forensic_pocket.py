#!/usr/bin/env python3
"""Forensic part 2: every expansion test from the two fanout cells
(0,316,172)/(0,316,173) that astar6's search died on, with the
blocking item + margin for each. Also a continuous-geometry probe:
sampled centrelines threading the slot east of the cells, tested
with the same exact seg_margin, to decide whether the seal is the
board's geometry or the 0.25 mm lattice's.

Run: xvfb-run -a python3 scratch/work/forensic_pocket.py BOARD
"""
import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair
import router6
from router import netclass, cell_of, CELL, OY
from router6 import seg_item_dist, pt_item_dist, _clr, via_size, \
    _neck_hw, SAFE
from forensic_ulpi import worst_seg, worst_pt, fmt_item, centre

NET = 'ULPI_D2'


def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    items, pad_cells = repair.build_items(board)
    width, clr = netclass(NET)
    neck_pts = [p[2] for p in pad_cells.get(NET, [])]
    vr = via_size(width)[0] / 2
    for cell in ((0, 316, 172), (0, 316, 173)):
        li, cx, cy = cell
        ax, ay = centre(cell)
        print(f"\n=== from cell {cell} centre ({ax:.3f},{ay:.3f}) ===")
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                       (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nb = (li, cx + dx, cy + dy)
            bx, by = centre(nb)
            hw_ = _neck_hw(width, ax, ay, bx, by, neck_pts)
            m, who = worst_seg(items, li, NET, clr, ax, ay, bx, by,
                               hw_)
            tag = "OK " if m >= SAFE else "BLOCKED"
            print(f"  step ({dx:+d},{dy:+d}) hw={hw_:.3f} "
                  f"margin={m:+.4f} {tag}"
                  + (f" by {fmt_item(who[0])} need={who[1]:.3f}"
                     if who and m < SAFE else ""))
        for lj in range(3):
            if lj == li:
                continue
            m_all = []
            worst = (float('inf'), None, None)
            for l2 in range(3):
                m, who = worst_pt(items, l2, NET, clr, ax, ay, vr)
                if m < worst[0]:
                    worst = (m, who, l2)
            m, who, l2 = worst
            tag = "OK " if m >= SAFE else "BLOCKED"
            print(f"  via to L{lj}: worst layer L{l2} margin={m:+.4f} "
                  f"{tag}"
                  + (f" by {fmt_item(who[0])} need={who[1]:.3f}"
                     if who and m < SAFE else ""))

    print("\n=== continuous probe: polyline centrelines from the "
          "pad anchor east through the slot (neck hw=0.1, then "
          "full hw=0.125) ===")
    anchor = (78.4375, 13.25)
    probes = [
        [(78.4375, 13.25), (79.05, 13.25), (79.35, 12.92),
         (80.30, 12.92)],
        [(78.4375, 13.25), (79.05, 13.25), (79.30, 12.95),
         (80.30, 12.95)],
        [(78.4375, 13.25), (79.05, 13.25), (79.40, 12.90),
         (80.30, 12.90)],
        [(78.4375, 13.25), (79.10, 13.22), (79.45, 12.98),
         (80.30, 12.98)],
    ]
    for pi, pts in enumerate(probes):
        print(f"  probe {pi}: {pts}")
        for (a, b) in zip(pts, pts[1:]):
            for hw_ in (0.1, 0.125):
                m, who = worst_seg(items, 0, NET, clr, a[0], a[1],
                                   b[0], b[1], hw_)
                tag = "OK " if m >= SAFE else "BLOCKED"
                print(f"    {a}->{b} hw={hw_}: margin={m:+4f} {tag}"
                      .replace('+4f', '+.4f')
                      + (f" by {fmt_item(who[0])} "
                         f"need={who[1]:.3f}"
                         if who and m < SAFE else ""))


if __name__ == "__main__":
    main()
