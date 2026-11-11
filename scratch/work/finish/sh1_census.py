#!/usr/bin/env python3
"""SH1 relocation census (read-only, bbox based).

Candidate: Harwin S02-25200300 can centred (23,40) -- walls on
centrelines x=10.5/35.5, y=30/50; interior x[10.6,35.4]
y[30.1,49.9]. Six S1001-46R clips: two per long wall at
+/-6.25 from centre, one centred on each short wall.

A) footprints whose Fab/pad bbox intersects the can interior
   (what ends up under the can) or the wall ring;
B) tracks/vias/pads whose bbox intersects each clip's pad rect
   (4.70 x 0.83) or courtyard rect (5.20 x 1.34).
"""
import wx
_app = wx.App(False)
import pcbnew

board = pcbnew.LoadBoard('hw/pdlvds_rx.kicad_pcb')

def BB(item):
    b = item.GetBoundingBox()
    return (b.GetLeft() / 1e6, b.GetTop() / 1e6,
            b.GetRight() / 1e6, b.GetBottom() / 1e6)

def ov(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

INTERIOR = (10.6, 30.1, 35.4, 49.9)
RING = (9.9, 29.4, 36.1, 50.6)

print('=== A) footprints touching the can interior / wall ring ===')
for fp in board.GetFootprints():
    pos = fp.GetPosition()
    cx, cy = pos.x / 1e6, pos.y / 1e6
    if not (2 < cx < 44 and 24 < cy < 56):
        continue
    boxes = [BB(d) for d in fp.GraphicalItems()
             if d.GetLayer() == pcbnew.F_Fab]
    boxes += [BB(p) for p in fp.Pads()]
    tag = []
    if any(ov(b, INTERIOR) for b in boxes):
        tag.append('UNDER-CAN')
    if any(ov(b, RING) for b in boxes):
        tag.append('ring')
    print('  %-6s centre (%6.2f,%6.2f) rot %3d  %s' % (
        fp.GetReference(), cx, cy, int(fp.GetOrientationDegrees()),
        ','.join(tag) if tag else '-'))

CLIPS = [
    ('CL-N1', 16.75, 30.0, 0), ('CL-N2', 29.25, 30.0, 0),
    ('CL-S1', 16.75, 50.0, 0), ('CL-S2', 29.25, 50.0, 0),
    ('CL-W', 10.5, 40.0, 90), ('CL-E', 35.5, 40.0, 90),
]
tracks = list(board.GetTracks())
allpads = [(fp.GetReference(), p) for fp in board.GetFootprints()
           for p in fp.Pads()]

print('=== B) copper under each clip (bbox over-approx) ===')
for (name, cx, cy, rot) in CLIPS:
    if rot == 0:
        pads = (cx - 2.35, cy - 0.415, cx + 2.35, cy + 0.415)
        crt = (cx - 2.6, cy - 0.67, cx + 2.6, cy + 0.67)
    else:
        pads = (cx - 0.415, cy - 2.35, cx + 0.415, cy + 2.35)
        crt = (cx - 0.67, cy - 2.6, cx + 0.67, cy + 2.6)
    found = []
    for t in tracks:
        b = BB(t)
        kind = 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk'
        if ov(b, pads):
            found.append('PADHIT %s %s' % (kind, t.GetNetname()))
        elif ov(b, crt):
            found.append('crt %s %s' % (kind, t.GetNetname()))
    for (ref, p) in allpads:
        b = BB(p)
        if ov(b, pads):
            found.append('PADHIT pad %s.%s %s' % (ref, p.GetNumber(),
                                                  p.GetNetname()))
        elif ov(b, crt):
            found.append('crt pad %s.%s %s' % (ref, p.GetNumber(),
                                               p.GetNetname()))
    print('  %s @ (%.2f,%.2f) r%d: %s' % (
        name, cx, cy, rot, '; '.join(sorted(set(found))) or 'clear'))
print('done')
