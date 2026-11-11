#!/usr/bin/env python3
"""SH1 mechanical acceptance: every part the can's fallback bbox
touches must be (a) fully inside the can interior (then height is
the only question, all < 3.0 mm by package), (b) fully outside, or
(c) a clip, whose pads sit on the wall line by design. A body
straddling a wall band is a mechanical clash."""
import wx
wx.App(False)
import pcbnew

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp275.kicad_pcb')
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

# can centre (21.05, 37.25); walls (centre-of-material) x 11.05 /
# 31.05, y 29.75 / 44.75; wall thickness 0.20 -> band +/-0.10.
WALLS = [('W', 11.05 - 0.10, 11.05 + 0.10), ('E', 31.05 - 0.10, 31.05 + 0.10)]
WALLSY = [('N', 29.75 - 0.10, 29.75 + 0.10), ('S', 44.75 - 0.10, 44.75 + 0.10)]
INNER = (11.05 + 0.10, 29.75 + 0.10, 31.05 - 0.10, 44.75 - 0.10)
OUTER = (11.05 - 0.10, 29.75 - 0.10, 31.05 + 0.10, 44.75 + 0.10)

def fab_bbox(fp):
    bb = None
    for d in fp.GraphicalItems():
        if d.GetLayer() == pcbnew.F_Fab:
            b = d.GetBoundingBox()
            r = (b.GetLeft()/1e6, b.GetTop()/1e6, b.GetRight()/1e6, b.GetBottom()/1e6)
            bb = r if bb is None else (min(bb[0], r[0]), min(bb[1], r[1]),
                                       max(bb[2], r[2]), max(bb[3], r[3]))
    return bb

refs = ['C1', 'C3', 'C5', 'C33', 'R1', 'R2', 'R3', 'R4', 'R7', 'R8',
        'RJ2', 'U1', 'U2', 'CL1', 'CL2', 'CL3', 'CL4', 'CL5']
for ref in refs:
    bb = fab_bbox(fps[ref])
    if bb is None:
        print(ref, 'no Fab drawings')
        continue
    straddle = []
    for name, lo, hi in WALLS:
        if bb[0] < hi and bb[2] > lo and bb[1] < OUTER[3] and bb[3] > OUTER[1]:
            # x-band crossed; only a clash if the body also spans the
            # wall's y-extent (it does if it reaches into the can rows)
            if bb[3] > INNER[1] and bb[1] < INNER[3]:
                straddle.append(name)
    for name, lo, hi in WALLSY:
        if bb[1] < hi and bb[3] > lo and bb[0] < OUTER[2] and bb[2] > OUTER[0]:
            if bb[2] > INNER[0] and bb[0] < INNER[2]:
                straddle.append(name)
    inside = bb[0] >= INNER[0] and bb[1] >= INNER[1] and bb[2] <= INNER[2] and bb[3] <= INNER[3]
    print('%-4s fab x[%.2f,%.2f] y[%.2f,%.2f]  %s%s' % (
        ref, bb[0], bb[2], bb[1], bb[3],
        'INSIDE' if inside else 'outside/partial',
        '  STRADDLES WALL ' + ','.join(straddle) if straddle else ''))
