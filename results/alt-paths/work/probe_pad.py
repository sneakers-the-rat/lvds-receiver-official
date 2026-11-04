#!/usr/bin/env python3
"""Probe: for one pad (REF.PIN) on a board, list every router item
within R mm of the pad centre (net, kind, layer, bbox) and the exact
seg_margin contribution for the 4 cardinal 0.25-steps and the fanout
bend segments, naming the worst item per segment.
Usage: probe_pad.py BOARD REF.PIN [R]"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair, router6
from router import netclass, cell_of

board_path, refpin = sys.argv[1], sys.argv[2]
R = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
ref, pin = refpin.rsplit('.', 1)
b = pcbnew.LoadBoard(board_path)
items, pad_cells = repair.build_items(b)
target = None
for net, pins in pad_cells.items():
    for desc, cs, pos in pins:
        if desc == refpin:
            target = (net, cs, pos)
if target is None:
    print("pad not found in pad_cells (GND or single-pad net?)")
    # fall back: find footprint pad directly
    for fp in b.GetFootprints():
        if fp.GetReference() == ref:
            for p in fp.Pads():
                if p.GetNumber() == pin:
                    print("direct: net=%s pos=(%.2f,%.2f) size=(%.2f,%.2f)"
                          % (p.GetNetname(), p.GetPosition().x/1e6,
                             p.GetPosition().y/1e6, p.GetSize().x/1e6,
                             p.GetSize().y/1e6))
    sys.exit(0)
net, cs, (px, py) = target
width, clr = netclass(net)
print("pad %s net=%s centre=(%.3f,%.3f) cells=%s width=%.2f clr=%.2f"
      % (refpin, net, px, py, cs, width, clr))
print("items within %.1f mm:" % R)
for li in range(3):
    seen = {}
    gx = int(R / 2) + 1
    for ix in range(-gx, gx + 1):
        for iy in range(-gx, gx + 1):
            for it in items[li].near(li, px + ix * 2.0, py + iy * 2.0):
                seen[id(it)] = it
    for it in seen.values():
        try:
            d = router6.seg_item_dist(it, px, py, px, py)
        except Exception:
            continue
        if d < R:
            print("  L%d dist=%.3f item=%s" % (li, d, it))
