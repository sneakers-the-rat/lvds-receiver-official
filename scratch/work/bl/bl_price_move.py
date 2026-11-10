#!/usr/bin/env python3
"""bl price: move U7 alone east by delta; report U7 courtyard polygon
(extents) and pad-rect collisions of moved U7 pads vs fixed pads."""
import wx
_app = wx.App(False)
import pcbnew

IU = 1e6
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp257.kicad_pcb')
u7 = None
fixed_pads = []   # (net, ref, rect)
for fp in b.GetFootprints():
    if fp.GetReference() == 'U7':
        u7 = fp
        continue
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        fixed_pads.append((pad.GetNetname(), fp.GetReference(),
                           (bb.GetLeft() / IU, bb.GetTop() / IU,
                            bb.GetRight() / IU, bb.GetBottom() / IU)))
u7pads = []
for pad in u7.Pads():
    bb = pad.GetBoundingBox()
    u7pads.append((pad.GetNumber(), pad.GetNetname(),
                   (bb.GetLeft() / IU, bb.GetTop() / IU,
                    bb.GetRight() / IU, bb.GetBottom() / IU)))
# courtyard polygon extents from the footprint's courtyard layer items
print('U7 courtyard shapes:')
for item in u7.GraphicalItems():
    try:
        lay = item.GetLayer()
    except Exception:
        continue
    if lay in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        bb = item.GetBoundingBox()
        print(f'  shape bbox x[{bb.GetLeft()/IU:.3f},{bb.GetRight()/IU:.3f}] y[{bb.GetTop()/IU:.3f},{bb.GetBottom()/IU:.3f}]')

def overlap(a, c):
    return a[0] < c[2] and c[0] < a[2] and a[1] < c[3] and c[1] < a[3]

for d in (0.75, 1.0, 1.25):
    hits = []
    for num, net, r in u7pads:
        r2 = (r[0] + d, r[1], r[2] + d, r[3])
        for fn, fref, fr in fixed_pads:
            if fn == net:
                continue
            if overlap(r2, fr):
                hits.append(f'U7.{num}/{net} vs {fref}/{fn}')
    print(f'delta +{d}: pad-rect collisions: {len(hits)}')
    for h in hits[:12]:
        print(f'    {h}')
