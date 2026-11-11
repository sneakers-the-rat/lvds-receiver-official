#!/usr/bin/env python3
"""SH1 stage D4: place the last silk texts by search - a position
wins if the text block (+/-1.05 x +/-0.55) clears every pad
(mask-expanded 0.12), every via, and every other refdes block."""
import wx
wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp275.kicad_pcb'
board = pcbnew.LoadBoard(SRC)

def BB(i):
    bb = i.GetBoundingBox()
    return (bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6)

def ov(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

pads = []
for fp in board.GetFootprints():
    for p in fp.Pads():
        r = BB(p)
        pads.append((r[0]-0.12, r[1]-0.12, r[2]+0.12, r[3]+0.12))
vias = []
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        r = BB(t)
        vias.append((r[0]-0.12, r[1]-0.12, r[2]+0.12, r[3]+0.12))

fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
texts = {}
for ref, fp in fps.items():
    t = fp.Reference()
    p = t.GetPosition()
    texts[ref] = (p.x/1e6 - 0.95, p.y/1e6 - 0.50, p.x/1e6 + 0.95, p.y/1e6 + 0.50)

MOVES = {  # ref: (home x, home y) around which to spiral-search
    'U3': (37.42, 47.11), 'C2': (33.5, 47.5), 'C7': (36.9, 42.8),
    'C44': (37.6, 44.5), 'C5': (30.25, 37.75),
    'C37': (40.25, 41.5), 'C43': (43.5, 39.5),
}
import math
for ref, (hx, hy) in MOVES.items():
    fp = fps[ref]
    own = texts.pop(ref)
    placed = None
    for rad in [0.0, 0.6, 1.2, 1.8, 2.4, 3.0, 3.6, 4.2, 4.8, 5.4, 6.0, 7.0, 8.0]:
        for k in range(24):
            x = hx + rad * math.cos(k * math.pi / 12)
            y = hy + rad * math.sin(k * math.pi / 12)
            r = (x - 0.95, y - 0.50, x + 0.95, y + 0.50)
            if any(ov(r, p) for p in pads): continue
            if any(ov(r, v) for v in vias): continue
            if any(ov(r, t) for t in texts.values()): continue
            placed = (x, y)
            break
        if placed: break
    assert placed, ref
    texts[ref] = (placed[0]-0.95, placed[1]-0.50, placed[0]+0.95, placed[1]+0.50)
    t = fp.Reference()
    t.SetPosition(pcbnew.VECTOR2I(int(placed[0]*1e6), int(placed[1]*1e6)))
    t.SetVisible(True)
    print('text', ref, '->', tuple(round(v, 2) for v in placed))

board.Save(SRC)
print('saved', SRC)
