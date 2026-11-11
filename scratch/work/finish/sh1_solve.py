#!/usr/bin/env python3
"""SH1 placement solver (read-only).

20x20 can (Harwin S02-20200300): walls on centrelines at
centre +/-10.0 (x) and +/-10.0 (y), wall 0.20 thick.
Hard rules for a candidate centre (cx, cy):
  R1 U1 and U2 bodies (Fab drawings) fully inside the interior
     (walls' inner faces at +/-9.9).
  R2 D1 body + pads fully outside the outer rect (+/-10.1).
  R3 No pad or via of a non-GND net intersects any wall band
     (centreline +/- 0.15) -- the metal wall must never touch
     exposed live copper. GND pads/vias allowed (can is GND).
  R4 No footprint Fab body intersects any wall band (the wall
     must not stand on a part).
  R5 Six clip pad rects (4.70 x 0.83 on the wall centrelines;
     N/S at cx-/+4.8, W at cy-5, E at cy+5) touch no non-GND
     pad/via/F.Cu track. (GND copper is fine: clips are GND.)
  R6 Clip courtyard rects (5.20 x 1.34) intersect no pad of
     any other footprint.
Reports every passing centre, finest first.
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

def inside(inner, outer):
    return (inner[0] >= outer[0] and inner[1] >= outer[1]
            and inner[2] <= outer[2] and inner[3] <= outer[3])

fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
fab_body = {}
for ref, fp in fps.items():
    boxes = [BB(d) for d in fp.GraphicalItems()
             if d.GetLayer() == pcbnew.F_Fab
             and not isinstance(d, pcbnew.PCB_TEXT)]
    if boxes:
        fab_body[ref] = (min(b[0] for b in boxes), min(b[1] for b in boxes),
                         max(b[2] for b in boxes), max(b[3] for b in boxes))

pads = []   # (ref, num, net, bbox)
for ref, fp in fps.items():
    for p in fp.Pads():
        pads.append((ref, p.GetNumber(), p.GetNetname(), BB(p)))
vias = [(t.GetNetname(), BB(t)) for t in board.GetTracks()
        if t.Type() == pcbnew.PCB_VIA_T]
ftracks = [(t.GetNetname(), BB(t)) for t in board.GetTracks()
           if t.Type() != pcbnew.PCB_VIA_T and t.GetLayer() == pcbnew.F_Cu]

D1_ALL = [b for (r, n, net, b) in pads if r == 'D1'] + [fab_body['D1']]

def clips(cx, cy):
    return [(cx - 4.8, cy - 10.0, 0), (cx + 4.8, cy - 10.0, 0),
            (cx - 4.8, cy + 10.0, 0), (cx + 4.8, cy + 10.0, 0),
            (cx - 10.0, cy - 5.0, 90), (cx + 10.0, cy + 5.0, 90)]

def clip_rects(x, y, rot):
    if rot == 0:
        return ((x - 2.35, y - 0.415, x + 2.35, y + 0.415),
                (x - 2.6, y - 0.67, x + 2.6, y + 0.67))
    return ((x - 0.415, y - 2.35, x + 0.415, y + 2.35),
            (x - 0.67, y - 2.6, x + 0.67, y + 2.6))

found = []
cx = 20.6
while cx <= 22.21:
    cy = 38.2
    while cy <= 40.61:
        interior = (cx - 9.9, cy - 9.9, cx + 9.9, cy + 9.9)
        outer = (cx - 10.1, cy - 10.1, cx + 10.1, cy + 10.1)
        ok = inside(fab_body['U1'], interior) and inside(fab_body['U2'], interior)
        why = 'R1' if not ok else None
        if ok and any(ov(b, outer) for b in D1_ALL):
            ok, why = False, 'R2-D1'
        walls = [(cx - 10.15, cy - 10.15, cx - 9.85, cy + 10.15),
                 (cx + 9.85, cy - 10.15, cx + 10.15, cy + 10.15),
                 (cx - 10.15, cy - 10.15, cx + 10.15, cy - 9.85),
                 (cx - 10.15, cy + 9.85, cx + 10.15, cy + 10.15)]
        if ok:
            for (ref, num, net, b) in pads:
                if net != 'GND' and any(ov(b, w) for w in walls):
                    ok, why = False, 'R3-pad %s.%s %s' % (ref, num, net)
                    break
        if ok:
            for (net, b) in vias:
                if net != 'GND' and any(ov(b, w) for w in walls):
                    ok, why = False, 'R3-via %s' % net
                    break
        if ok:
            for ref, b in fab_body.items():
                if ref in ('SH1',):
                    continue
                if any(ov(b, w) for w in walls):
                    ok, why = False, 'R4-body %s' % ref
                    break
        if ok:
            for (x, y, rot) in clips(cx, cy):
                pr, cr = clip_rects(x, y, rot)
                for (ref, num, net, b) in pads:
                    if net != 'GND' and ov(b, pr):
                        ok, why = False, 'R5-clip-pad %s.%s %s' % (ref, num, net)
                    if ov(b, cr):
                        ok, why = False, 'R6-clip-crt %s.%s %s' % (ref, num, net)
                for (net, b) in vias:
                    if net != 'GND' and ov(b, pr):
                        ok, why = False, 'R5-clip-via %s' % net
                for (net, b) in ftracks:
                    if net != 'GND' and ov(b, pr):
                        ok, why = False, 'R5-clip-trk %s' % net
                if not ok:
                    break
        if ok:
            found.append((round(cx, 2), round(cy, 2)))
        elif abs(cx - round(cx*2)/2) < 0.01 and abs(cy - round(cy*2)/2) < 0.01:
            print('  (%.1f,%.1f) fails %s' % (cx, cy, why))
        cy += 0.1
    cx += 0.1

print('passing centres:', len(found))
for f in found:
    print('  centre (%.2f, %.2f)  walls x[%.2f, %.2f] y[%.2f, %.2f]' % (
        f[0], f[1], f[0] - 10, f[0] + 10, f[1] - 10, f[1] + 10))
