#!/usr/bin/env python3
"""Debug: why did whole nets fail instantly in router v3?
Rebuilds the router's obstacle registry from PADS ONLY (the pre-route
state) on the saved v3 board, then replays net +VA's connections with
instrumentation: visited counts, exhaustion vs cap, and the blocked
status around the first failing pin's start cells.
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import router
from router import Items, netclass, cell_of, astar, blocked, dist_to_item, LAYERS

board = pcbnew.LoadBoard('hw/pdlvds_rx.kicad_pcb')
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

# --- rebuild pad registry exactly as router.route() does ---
items = {l: Items() for l in range(3)}
pad_cells = {}
for ref, fp in fps.items():
    rot = math.radians(fp.GetOrientationDegrees())
    for pad in fp.Pads():
        net = pad.GetNetname()
        pos = pcbnew.ToMM(pad.GetPosition())
        size = pcbnew.ToMM(pad.GetSize())
        layers = []
        for li, lname in enumerate(LAYERS):
            if pad.IsOnLayer(lname):
                layers.append(li)
        clr = netclass(net)[1] if net else 0.2
        pad_hw = max(size) / 2 + 1.8
        for li in layers:
            items[li].add(li, ('pad', net, (pos[0], pos[1], size[0] / 2,
                                            size[1] / 2,
                                            rot + math.radians(pad.GetOrientationDegrees())), clr),
                          (pos[0] - pad_hw, pos[1] - pad_hw,
                           pos[0] + pad_hw, pos[1] + pad_hw))
        if net:
            cx, cy = cell_of(pos[0], pos[1])
            pad_cells.setdefault(net, []).append(
                (f"{ref}.{pad.GetNumber()}",
                 [(li, cx, cy) for li in layers], (pos[0], pos[1])))

for target in ["+VA", "+3V3A", "CDR_CLKP"]:
    print(f"\n===== {target} =====")
    width, clr = netclass(target)
    pins = pad_cells[target]
    neck_pts = [p[2] for p in pins]
    print("pin order:", [p[0] for p in pins])
    tree = set()
    for li, cx, cy in pins[0][1]:
        tree.add((li, cx, cy))
    for pin_id, cells, pos in pins[1:]:
        path = astar(items, cells, tree, target, width / 2, clr,
                     neck_pts=neck_pts)
        print(f"  {pin_id} at {pos}: {'OK len=' + str(len(path)) if path else 'FAIL'}")
        if path:
            for node in path:
                tree.add(node)
        else:
            # diagnose the start area: for each start cell, count how
            # many of its 4 neighbours + 2 via targets are blocked
            for (li, cx, cy) in cells:
                x, y = (cx + 0.5) * router.CELL, (cy + 0.5) * router.CELL
                nb = []
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    wx_, wy_ = (cx + dx + 0.5) * router.CELL, (cy + dy + 0.5) * router.CELL
                    nb.append('B' if blocked(items, li, wx_, wy_, target, 0.1, clr) else '.')
                vias = []
                for lj in range(3):
                    if lj == li:
                        continue
                    vias.append('B' if blocked(items, lj, x, y, target, 0.1, clr) else '.')
                print(f"    start cell L{li} ({cx},{cy}): neighbours {''.join(nb)} vias {''.join(vias)}")
            # and around the tree (seed) cells
            for (li, cx, cy) in list(tree)[:6]:
                x, y = (cx + 0.5) * router.CELL, (cy + 0.5) * router.CELL
                near = [(it[1], round(dist_to_item(it, x, y), 2))
                        for it in items[li].near(li, x, y) if it[1] != target][:6]
                print(f"    tree cell L{li} ({cx},{cy}) near foreign items: {near}")
            break
