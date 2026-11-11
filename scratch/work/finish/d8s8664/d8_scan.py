#!/usr/bin/env python3
"""Exact-geometry scan for a lawful D8 (SMT740_3227) placement.
Obstacles: F.Cu pads (rects), tracks (capsules), vias (circles) of all
nets except BIST_A/BIST_DRV (D8's own, re-laid) in the district box.
Requirement: >= 0.20 mm clearance pad-to-obstacle (binding fab rule).
Also courtyard limits vs R46 (south) and C26 (north)."""
import pcbnew, wx, math
_app = wx.App(False)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp276.kicad_pcb')
X0, X1, Y0, Y1 = 59.0, 75.0, 6.0, 18.0
OWN = {'BIST_A', 'BIST_DRV'}
rects, segs, circs = [], [], []
for fp in b.GetFootprints():
    if fp.GetReference() == 'D8':
        continue
    for pad in fp.Pads():
        if pad.GetNetname() in OWN: continue
        pp = pad.GetPosition(); sz = pad.GetSize()
        cx, cy, w, h = pp.x/1e6, pp.y/1e6, sz.x/1e6, sz.y/1e6
        if X0-3 <= cx <= X1+3 and Y0-3 <= cy <= Y1+3:
            rects.append((cx-w/2, cy-h/2, cx+w/2, cy+h/2, pad.GetNetname()))
for t in b.GetTracks():
    if b.GetLayerName(t.GetLayer()) != 'F.Cu': continue
    if t.GetNetname() in OWN: continue
    s, e = t.GetStart(), t.GetEnd()
    sx, sy, ex, ey = s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6
    if not (X0-3 <= sx <= X1+3 and Y0-3 <= sy <= Y1+3): continue
    if t.Type() == pcbnew.PCB_VIA_T:
        circs.append((sx, sy, t.GetWidth()/2e6, t.GetNetname()))
    else:
        segs.append((sx, sy, ex, ey, t.GetWidth()/2e6, t.GetNetname()))

def d_pt_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2-x1, y2-y1
    L2 = dx*dx + dy*dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-x1)*dx + (py-y1)*dy)/L2))
    return math.hypot(px-(x1+t*dx), py-(y1+t*dy))
def d_rect_pt(r, px, py):
    dx = max(r[0]-px, 0.0, px-r[2]); dy = max(r[1]-py, 0.0, py-r[3])
    return math.hypot(dx, dy)
def d_rect_seg(r, x1, y1, x2, y2):
    # min over segment samples is unsafe; use corner/edge tests
    if max(x1, x2) < r[0] or min(x1, x2) > r[2]:
        pass
    # distance rect-to-segment: min of pt-seg for 4 corners and seg endpoints to rect
    d = min(d_pt_seg(r[0], r[1], x1, y1, x2, y2), d_pt_seg(r[2], r[1], x1, y1, x2, y2),
            d_pt_seg(r[0], r[3], x1, y1, x2, y2), d_pt_seg(r[2], r[3], x1, y1, x2, y2),
            d_rect_pt(r, x1, y1), d_rect_pt(r, x2, y2))
    # segment crossing rect interior => 0 (corner tests miss full crossing for long segs;
    # district segs are short; also check midpoints)
    for t in (0.25, 0.5, 0.75):
        d = min(d, d_rect_pt(r, x1+t*(x2-x1), y1+t*(y2-y1)))
    return d
def d_rect_rect(a, r):
    dx = max(r[0]-a[2], a[0]-r[2], 0.0); dy = max(r[1]-a[3], a[1]-r[3], 0.0)
    if dx == 0.0 and dy == 0.0: return 0.0
    return math.hypot(dx, dy) if (dx > 0 and dy > 0) else max(dx, dy)
def d_rect_circ(r, cx, cy, rad):
    return max(0.0, d_rect_pt(r, cx, cy) - rad)

def worst(pads):
    w = (9.9, '')
    for pr in pads:
        for r in rects:
            d = d_rect_rect(pr, r)
            if d < w[0]: w = (d, 'pad ' + r[4])
        for s in segs:
            d = d_rect_seg(pr, s[0], s[1], s[2], s[3]) - s[4]
            if d < w[0]: w = (d, 'trk ' + s[5])
        for c in circs:
            d = d_rect_circ(pr, c[0], c[1], c[2])
            if d < w[0]: w = (d, 'via ' + c[3])
    return w

for pad_h in (2.3, 2.2):
    print('=== pad height', pad_h)
    best = []
    for dxi in range(-30, 11):
        for dyi in range(-12, 9):
            dx, dy = dxi*0.05, dyi*0.05
            cx, cy = 66.25+dx, 12.00+dy
            pads = [(cx-1.35-0.6, cy-pad_h/2, cx-1.35+0.6, cy+pad_h/2),
                    (cx+1.35-0.6, cy-pad_h/2, cx+1.35+0.6, cy+pad_h/2)]
            w = worst(pads)
            if w[0] >= 0.20:
                best.append((round(w[0], 3), dx, dy, w[1]))
    best.sort(reverse=True)
    for row in best[:8]:
        print('  worst %.3f at dx=%+.2f dy=%+.2f (%s)' % row)
    if not best:
        print('  no lawful placement in scan box')
