#!/usr/bin/env python3
"""Forensic: why does astar6 refuse ULPI_D2 / ULPI_DIR instantly?

Dumps repair.build_items items around the sealed pads and replays
astar6's entry tests one by one (fanout macro legs, 8-neighbour
steps from the anchor, via step at the start cell centre), naming
the blocking item and margin for every refusal. Also replays the
goal-side fanout (goal_finish) for the main group's pad.

Run: xvfb-run -a python3 scratch/work/forensic_ulpi.py BOARD NET REF.PAD
"""
import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair
import router6
from router import netclass, cell_of, CELL, W, H, OY
from router6 import seg_item_dist, pt_item_dist, _clr, via_size, _neck_hw, SAFE

MM = pcbnew.FromMM


def worst_seg(items, li, netname, my_clr, ax, ay, bx, by, hw_):
    worst, who = float('inf'), None
    for it in router6._candidates(items[li], li, ax, ay, bx, by):
        if it[1] == netname:
            continue
        need = hw_ + max(_clr(netname, my_clr, li),
                         _clr(it[1], it[3], li))
        m = seg_item_dist(it, ax, ay, bx, by) - need
        if m < worst:
            worst, who = m, (it, need)
    return worst, who


def worst_pt(items, li, netname, my_clr, x, y, vr):
    worst, who = float('inf'), None
    for it in router6._candidates(items[li], li, x, y, x, y):
        if it[1] == netname:
            continue
        need = vr + max(_clr(netname, my_clr, li),
                        _clr(it[1], it[3], li))
        m = pt_item_dist(it, x, y) - need
        if m < worst:
            worst, who = m, (it, need)
    return worst, who


def fmt_item(it):
    kind, net, data, clr = it
    if kind == 'pad':
        cx, cy, hw, hh, rot = data
        return (f"pad net={net} c=({cx:.3f},{cy:.3f}) hw={hw:.3f} "
                f"hh={hh:.3f} rot={math.degrees(rot):.0f} clr={clr}")
    if kind == 'seg':
        x1, y1, x2, y2, hw = data
        return (f"seg net={net} ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) "
                f"hw={hw:.3f} clr={clr}")
    cx, cy, r = data
    return f"via net={net} c=({cx:.3f},{cy:.3f}) r={r:.3f} clr={clr}"


def centre(node):
    return ((node[1] + 0.5) * CELL, (node[2] + 0.5) * CELL + OY)


def main():
    board_path, net, padref = sys.argv[1], sys.argv[2], sys.argv[3]
    board = pcbnew.LoadBoard(board_path)
    items, pad_cells = repair.build_items(board)
    groups = repair.compute_groups(board)[net]
    groups = sorted(groups, key=len, reverse=True)
    print(f"{net}: {len(groups)} groups, sizes "
          f"{[len(g) for g in groups]}")
    for gi, g in enumerate(groups):
        print(f"  group {gi}: {[it.desc for it in g][:8]}")

    # locate the pad
    ref, num = padref.rsplit('.', 1)
    fp = {f.GetReference(): f for f in board.GetFootprints()}[ref]
    pad = [p for p in fp.Pads() if p.GetNumber() == num][0]
    pos = pcbnew.ToMM(pad.GetPosition())
    size = pcbnew.ToMM(pad.GetSize())
    print(f"\n{padref}: centre={pos} size={size} "
          f"orient={pad.GetOrientationDegrees()} "
          f"layers={[ln for ln in ('F', 'In2', 'B') if pad.IsOnLayer(getattr(pcbnew, ln + '_Cu'))]}")
    fpl = pcbnew.ToMM(fp.GetPosition())
    print(f"footprint {ref} centre={fpl} rot={fp.GetOrientationDegrees()}")

    width, clr = netclass(net)
    neck_pts = [p[2] for p in pad_cells.get(net, [])]
    anchors = {}
    for _, cs, p in pad_cells.get(net, []):
        for c in cs:
            anchors[c] = p
    starts = [c for (pid, cs, p) in pad_cells[net]
              if pid == padref for c in cs]
    print(f"start cells for {padref}: {starts}  width={width} clr={clr}")
    li = starts[0][0]
    anchor = pos

    print(f"\n--- items within 3.5 mm of the pad centre, layer li={li} "
          f"(plus all layers for via test) ---")
    for lj in range(3):
        seen = set()
        for it in items[lj].near(lj, pos[0], pos[1]):
            if id(it) in seen:
                continue
            seen.add(id(it))
            d = pt_item_dist(it, pos[0], pos[1])
            if d < 3.5:
                print(f"  L{lj} d={d:+.3f} {fmt_item(it)}")

    print(f"\n--- entry tests from anchor {anchor} on layer {li} ---")
    # 8-neighbour steps (astar6 tests anchor->neighbour centre)
    _, scx, scy = starts[0]
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
        nb = (li, scx + dx, scy + dy)
        bx, by = centre(nb)
        hw_ = _neck_hw(width, anchor[0], anchor[1], bx, by, neck_pts)
        m, who = worst_seg(items, li, net, clr,
                           anchor[0], anchor[1], bx, by, hw_)
        tag = "OK " if m >= SAFE else "BLOCKED"
        print(f"  step ({dx:+d},{dy:+d}) -> centre ({bx:.3f},{by:.3f}) "
              f"hw={hw_:.3f} margin={m:+.4f} {tag}"
              + (f" by {fmt_item(who[0])} need={who[1]:.3f}"
                 if who else ""))
    # fanout macro legs
    print("  fanout legs (anchor->bend):")
    for ux, uy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for d in router6.BEND_DS:
            bend = (anchor[0] + ux * d, anchor[1] + uy * d)
            hw1 = _neck_hw(width, anchor[0], anchor[1],
                           bend[0], bend[1], neck_pts)
            m, who = worst_seg(items, li, net, clr,
                               anchor[0], anchor[1], bend[0], bend[1],
                               hw1)
            tag = "OK " if m >= SAFE else "BLOCKED"
            print(f"    dir ({ux:+d},{uy:+d}) d={d}: margin={m:+.4f} "
                  f"{tag}"
                  + (f" by {fmt_item(who[0])} need={who[1]:.3f}"
                     if who and m < SAFE else ""))
    # via step at start cell centre
    vx, vy = centre(starts[0])
    vr = via_size(width)[0] / 2
    print(f"  via at start cell centre ({vx:.3f},{vy:.3f}) vr={vr}:")
    for lj in range(3):
        m, who = worst_pt(items, lj, net, clr, vx, vy, vr)
        tag = "OK " if m >= SAFE else "BLOCKED"
        print(f"    layer {lj}: margin={m:+.4f} {tag}"
              + (f" by {fmt_item(who[0])} need={who[1]:.3f}"
                 if who else ""))

    # full astar6 replay with timing, both orientations
    main_cells = set()
    for it in groups[0]:
        main_cells |= it.cells
    iso = [g for g in groups[1:]
           if any(it.desc == padref for it in g)]
    import time
    for g in (iso or groups[1:]):
        st = []
        for it in g:
            st += list(it.cells)
        t0 = time.time()
        rpath, fb, lb = router6.astar6(items, st, main_cells, net,
                                       width, clr, cap=1500000,
                                       neck_pts=neck_pts,
                                       anchors=anchors)
        print(f"\nastar6 replay from {[it.desc for it in g]}: "
              f"{'path len ' + str(len(rpath)) if rpath else 'None'} "
              f"in {time.time() - t0:.2f}s")


if __name__ == "__main__":
    main()

def leg2():
    board_path, net, padref = sys.argv[1], sys.argv[2], sys.argv[3]
    board = pcbnew.LoadBoard(board_path)
    items, pad_cells = repair.build_items(board)
    ref, num = padref.rsplit('.', 1)
    fp = {f.GetReference(): f for f in board.GetFootprints()}[ref]
    pad = [p for p in fp.Pads() if p.GetNumber() == num][0]
    anchor = pcbnew.ToMM(pad.GetPosition())
    width, clr = netclass(net)
    neck_pts = [p[2] for p in pad_cells.get(net, [])]
    starts = [c for (pid, cs, p) in pad_cells[net]
              if pid == padref for c in cs]
    li = starts[0][0]
    print(f"\n--- fanout leg-2 (bend->cell) for {padref} anchor={anchor} ---")
    total_ok = 0
    for ux, uy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for d in router6.BEND_DS:
            bend = (anchor[0] + ux * d, anchor[1] + uy * d)
            hw1 = _neck_hw(width, anchor[0], anchor[1],
                           bend[0], bend[1], neck_pts)
            m1, _ = worst_seg(items, li, net, clr, anchor[0], anchor[1],
                              bend[0], bend[1], hw1)
            if m1 < SAFE:
                continue
            ccx, ccy = cell_of(bend[0], bend[1])
            oks = []
            for ddx in range(-3, 4):
                for ddy in range(-3, 4):
                    cell = (li, ccx + ddx, ccy + ddy)
                    if not (0 <= cell[1] < W and 0 <= cell[2] < H):
                        continue
                    cp = centre(cell)
                    if (cp[0] - bend[0]) ** 2 + \
                       (cp[1] - bend[1]) ** 2 > router6.BEND_REACH ** 2:
                        continue
                    hw2 = _neck_hw(width, bend[0], bend[1],
                                   cp[0], cp[1], neck_pts)
                    m2, who = worst_seg(items, li, net, clr,
                                        bend[0], bend[1], cp[0], cp[1],
                                        hw2)
                    if m2 >= SAFE:
                        oks.append((cell, cp, round(m2, 3)))
            total_ok += len(oks)
            print(f"  bend dir ({ux:+d},{uy:+d}) d={d} at {bend}: "
                  f"{len(oks)} legal cells {oks[:6]}")
    print(f"  TOTAL legal fanout cells: {total_ok}")

if len(sys.argv) > 4 and sys.argv[4] == 'leg2':
    leg2()
