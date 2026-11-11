#!/usr/bin/env python3
"""Full census of the HV district as it now stands on exp274:
footprints + pads, track endpoints per net, zone fills."""
import wx
_app = wx.App(False)
import pcbnew

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp274.kicad_pcb')
X0, X1, Y0, Y1 = -2.0, 60.0, -46.0, 4.0

def inb(x, y):
    return X0 <= x <= X1 and Y0 <= y <= Y1

print('=== footprints (centre in box) ===')
for fp in board.GetFootprints():
    c = fp.GetPosition()
    x, y = c.x / 1e6, c.y / 1e6
    if not inb(x, y):
        continue
    pads = []
    for p in fp.Pads():
        pc = p.GetPosition()
        pads.append('%s:%s@(%.2f,%.2f)' % (p.GetNumber(), p.GetNetname(),
                                           pc.x / 1e6, pc.y / 1e6))
    print('%s @ (%.2f,%.2f) rot %.0f  %s' % (fp.GetReference(), x, y,
          fp.GetOrientationDegrees(), ' '.join(pads)))

print('=== track endpoints per net (segments touching box) ===')
from collections import defaultdict
ends = defaultdict(set)
segs = defaultdict(int)
for t in board.GetTracks():
    a, b = t.GetStart(), t.GetEnd()
    pa, pb = (a.x / 1e6, a.y / 1e6), (b.x / 1e6, b.y / 1e6)
    if inb(*pa) or inb(*pb):
        n = t.GetNetname()
        segs[n] += 1
        for p in (pa, pb):
            if inb(*p):
                ends[n].add((round(p[0], 2), round(p[1], 2)))
for n in sorted(ends):
    print(n, 'segs', segs[n], 'ends', sorted(ends[n]))

print('=== zones ===')
for z in board.Zones():
    bb = z.GetBoundingBox()
    print(z.GetNetname(), z.GetLayerName(),
          'bbox (%.1f,%.1f)-(%.1f,%.1f)' % (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                                            bb.GetRight() / 1e6, bb.GetBottom() / 1e6))
