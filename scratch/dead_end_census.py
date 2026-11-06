#!/usr/bin/env python3
"""Dead-end census the strict way: classify every track segment by
whether each of its endpoints is anchored to something real.

An endpoint is ANCHORED iff it coincides with:
  - a pad of the same net (on a layer the pad touches), or
  - a via of the same net spanning the segment's layer, or
  - another segment endpoint of the same net on the same layer, or
  - the interior of another segment of the same net on the same layer
    (a T-junction).
Otherwise it is FREE -- the segment just stops in space.

Classes per segment:
  FLOATER  both endpoints free (isolated island of copper)
  TOOTH    exactly one endpoint free (barb / spur off a live route)

Zones/pours are NOT considered anchors here; GND is reported
separately because the GND pour can legitimately touch a segment
along its length.

Run: xvfb-run -a python3 scratch/dead_end_census.py BOARD
"""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

MM = 1_000_000
TOL = 2000  # 2 um in nm, for point-on-segment collinearity

board = pcbnew.LoadBoard(sys.argv[1])

segs = []          # (net, layer, x0, y0, x1, y1, width)
vias = []          # (net, layers_set, x, y)
pads = []          # (net, layers_set, x, y)
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        ls = set()
        # via spans F..B through its layer pair
        vias.append((t.GetNetname(), t.GetPosition().x, t.GetPosition().y))
    elif t.Type() == pcbnew.PCB_TRACE_T:
        s, e = t.GetStart(), t.GetEnd()
        segs.append([t.GetNetname(), t.GetLayer(), s.x, s.y, e.x, e.y,
                     t.GetWidth()])
for fp in board.GetFootprints():
    for p in fp.Pads():
        pos = p.GetPosition()
        pads.append((p.GetNetname(), pos.x, pos.y))

from collections import defaultdict
pad_by_net = defaultdict(list)
for n, x, y in pads:
    pad_by_net[n].append((x, y))
via_by_net = defaultdict(list)
for n, x, y in vias:
    via_by_net[n].append((x, y))
seg_by_nl = defaultdict(list)
for i, s in enumerate(segs):
    seg_by_nl[(s[0], s[1])].append(i)

def near_pt(x, y, pts, r=1000):
    for (px, py) in pts:
        if abs(px - x) <= r and abs(py - y) <= r:
            return True
    return False

def on_segment(x, y, s):
    x0, y0, x1, y1 = s[2], s[3], s[4], s[5]
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return False
    cross = (x - x0) * dy - (y - y0) * dx
    if abs(cross) * 1.0 / math.sqrt(L2) > TOL:
        return False
    dot = (x - x0) * dx + (y - y0) * dy
    return -TOL * math.sqrt(L2) < dot < L2 + TOL * math.sqrt(L2)

def anchored(net, layer, x, y, self_idx):
    if near_pt(x, y, pad_by_net.get(net, ())):
        return True
    if near_pt(x, y, via_by_net.get(net, ())):
        return True
    for j in seg_by_nl.get((net, layer), ()):
        if j == self_idx:
            continue
        s = segs[j]
        if (abs(s[2] - x) <= 1000 and abs(s[3] - y) <= 1000) or \
           (abs(s[4] - x) <= 1000 and abs(s[5] - y) <= 1000):
            return True
        if on_segment(x, y, s):
            return True
    return False

floaters, teeth = [], []
for i, s in enumerate(segs):
    net, layer = s[0], s[1]
    a0 = anchored(net, layer, s[2], s[3], i)
    a1 = anchored(net, layer, s[4], s[5], i)
    length = math.hypot(s[4] - s[2], s[5] - s[3]) / MM
    rec = (net, pcbnew.LayerName(layer), s[2] / MM, s[3] / MM,
           s[4] / MM, s[5] / MM, round(length, 2))
    if not a0 and not a1:
        floaters.append(rec)
    elif a0 != a1:
        teeth.append(rec)

def report(name, rows):
    gnd = [r for r in rows if r[0] == 'GND']
    sig = [r for r in rows if r[0] != 'GND']
    print(f"{name}: total {len(rows)} "
          f"(non-GND {len(sig)}, GND {len(gnd)}), "
          f"dead length non-GND {sum(r[6] for r in sig):.1f} mm")
    return sig

sig_teeth = report('TOOTH (one free end)', teeth)
sig_float = report('FLOATER (both ends free)', floaters)
print('\n-- longest non-GND teeth --')
for r in sorted(sig_teeth, key=lambda r: -r[6])[:25]:
    print(f"  {r[0]:14s} {r[1]:6s} ({r[2]:.2f},{r[3]:.2f})->({r[4]:.2f},{r[5]:.2f}) len {r[6]} mm")
print('\n-- all non-GND floaters --')
for r in sorted(sig_float, key=lambda r: -r[6]):
    print(f"  {r[0]:14s} {r[1]:6s} ({r[2]:.2f},{r[3]:.2f})->({r[4]:.2f},{r[5]:.2f}) len {r[6]} mm")
