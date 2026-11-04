#!/usr/bin/env python3
"""Debug v6 connectivity: for one net on a board, list its audit
groups; for every non-main group, report each pad's first-step
margins under the exact model WITH the identity of the item that
sets the worst margin in each direction, and the via margin with
its worst item per layer. This separates the three ways a pin can
be stuck: boxed by a foreign pad (placement), boxed by routed
copper (ordering), or free but unable to reach the tree (corridor).

Run: xvfb-run -a python3 hw/debug_pocket.py BOARD NET
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
import router6
from router import netclass

def worst_seg(items, li, net, clr, ax, ay, bx, by, hw_):
    worst, witem = float('inf'), None
    for it in router6._candidates(items[li], li, ax, ay, bx, by):
        if it[1] == net:
            continue
        need = hw_ + max(router6._clr(net, clr, li),
                         router6._clr(it[1], it[3], li))
        m = router6.seg_item_dist(it, ax, ay, bx, by) - need
        if m < worst:
            worst, witem = m, it
    return worst, witem

def worst_via(items, net, clr, x, y, vr):
    out = []
    for li in range(3):
        worst, witem = float('inf'), None
        for it in router6._candidates(items[li], li, x, y, x, y):
            if it[1] == net:
                continue
            need = vr + max(router6._clr(net, clr, li),
                            router6._clr(it[1], it[3], li))
            m = router6.pt_item_dist(it, x, y) - need
            if m < worst:
                worst, witem = m, it
        out.append((li, worst, witem))
    return out

def desc(it):
    if it is None:
        return "-"
    k = it[0]
    if k == 'pad':
        return f"pad[{it[1]}]"
    if k == 'via':
        return f"via[{it[1]}]@({it[2][0]:.2f},{it[2][1]:.2f})"
    return f"seg[{it[1]}]"

def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    net = sys.argv[2]
    items, pad_cells = repair.build_items(board)
    groups = repair.compute_groups(board)[net]
    groups.sort(key=len, reverse=True)
    width, clr = netclass(net)
    neck_pts = [p[2] for p in pad_cells.get(net, [])]
    anchors = {}
    for _, cs, pos in pad_cells.get(net, []):
        for c in cs:
            anchors[c] = pos
    def centre(n):
        return ((n[1] + 0.5) * router6.CELL, (n[2] + 0.5) * router6.CELL)
    print(f"{net}: {len(groups)} groups, sizes "
          f"{[len(g) for g in groups]}")
    for g in groups[1:]:
        for it in g:
            if it.kind != "pad":
                continue
            print(f"  {it.desc} (net {net}):")
            for node in sorted(it.cells):
                li, cx, cy = node
                a = anchors.get(node, centre(node))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nb = (li, cx + dx, cy + dy)
                    b = centre(nb)
                    hw_ = router6._neck_hw(width, a[0], a[1], b[0],
                                           b[1], neck_pts)
                    m, wit = worst_seg(items, li, net, clr,
                                       a[0], a[1], b[0], b[1], hw_)
                    print(f"    step ->{nb}: {m:+.3f} vs {desc(wit)}")
                vr = router6.via_size(width)[0] / 2
                vx, vy = centre(node)
                for li2, m, wit in worst_via(items, net, clr,
                                             vx, vy, vr):
                    print(f"    via L{li2}: {m:+.3f} vs {desc(wit)}")

if __name__ == "__main__":
    main()
