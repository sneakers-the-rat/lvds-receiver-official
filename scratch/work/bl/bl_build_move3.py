#!/usr/bin/env python3
"""bl build v3.2: re-place U7 +0.75 east (C19 +0.35) on exp257 -> exp259.
Escape shear: per net, BFS from the part's pads over track segments,
including a segment iff both endpoints are within 1.45mm of a seed pad
rect; expansion does not cross via centres or fixed pads (terminals).
A node moves by DX iff it is an endpoint of an included segment and is
not on a via, a fixed pad, or a non-included track. Footprints move
first (fresh objects); track surgery after. Vias never move."""
import math
import wx
_app = wx.App(False)
import pcbnew

IU = 1e6
SRC, DST = 'hw/pdlvds_rx.exp257.kicad_pcb', 'hw/pdlvds_rx.exp259.kicad_pcb'
MOVES = [('U7', 0.75), ('C19', 0.35)]
NETS = ['+3V3A', '+5V', 'DP_PHY', 'DM_PHY', 'ULPI_NXT', 'ULPI_DIR',
        'ULPI_STP', 'ULPI_CK', 'PHY_1V8', 'ULPI_D0', 'ULPI_D1', 'ULPI_D2',
        'ULPI_D3', 'ULPI_D4', 'ULPI_D5', 'ULPI_D6', 'ULPI_D7', 'XO', 'XI',
        'PHY_1V8A', 'RBIAS', 'GND', 'NRST']

b = pcbnew.LoadBoard(SRC)
NC = {n: b.GetNetcodeFromNetname(n) for n in NETS
      if b.GetNetcodeFromNetname(n) >= 0}

def census(board):
    out = {}
    for t in board.GetTracks():
        k = (t.GetNetname(), 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk')
        out[k] = out.get(k, 0) + 1
    return out

base = census(b)

def seg_pts(t):
    s, e = t.GetStart(), t.GetEnd()
    return (s.x / IU, s.y / IU), (e.x / IU, e.y / IU)

def pt_seg(p, a, bb):
    dx, dy = bb[0] - a[0], bb[1] - a[1]
    L2 = dx * dx + dy * dy
    tt = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - (a[0] + tt * dx), p[1] - (a[1] + tt * dy))

def near(p, q, tol):
    return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol

def in_rect(p, r, pad=0.0):
    return r[0] - pad <= p[0] <= r[2] + pad and r[1] - pad <= p[1] <= r[3] + pad

def rect_dist(p, r):
    dx = max(r[0] - p[0], 0.0, p[0] - r[2])
    dy = max(r[1] - p[1], 0.0, p[1] - r[3])
    return math.hypot(dx, dy)

# capture pad data for moving parts, then move footprints (fresh objs)
part_pads = {}
for ref, DX in MOVES:
    for fp in b.GetFootprints():
        if fp.GetReference() == ref:
            pads = []
            for pad in fp.Pads():
                bb = pad.GetBoundingBox()
                pads.append((pad.GetNetname(), (bb.GetLeft() / IU, bb.GetTop() / IU,
                                                bb.GetRight() / IU, bb.GetBottom() / IU)))
            part_pads[ref] = pads
            p = fp.GetPosition()
            fp.SetPosition(pcbnew.VECTOR2I(p.x + int(round(DX * IU)), p.y))
            print(f'{ref} footprint moved +{DX}')
            break
# fixed pad rects per net (parts not moving)
fixed_pads = {}
for fp in b.GetFootprints():
    if fp.GetReference() in dict(MOVES):
        continue
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        fixed_pads.setdefault(pad.GetNetname(), []).append(
            (bb.GetLeft() / IU, bb.GetTop() / IU, bb.GetRight() / IU, bb.GetBottom() / IU))

def refan(ref, DX):
    pads = part_pads[ref]
    tracks = list(b.GetTracks())
    by_net = {}
    for t in tracks:
        by_net.setdefault(t.GetNetname(), []).append(t)
    n_re = n_col = 0
    for net in {n for n, _ in pads if n and n in NC}:
        items = by_net.get(net, [])
        trks = [t for t in items if t.Type() != pcbnew.PCB_VIA_T]
        vias = [(t.GetPosition().x / IU, t.GetPosition().y / IU,
                 t.GetWidth() / IU / 2)
                for t in items if t.Type() == pcbnew.PCB_VIA_T]
        seed_rects = [r for n, r in pads if n == net]

        def on_via(p):
            return any(math.hypot(p[0] - vx, p[1] - vy) <= vr + 0.045
                       for (vx, vy, vr) in vias)

        def on_fixed_pad(p):
            return any(in_rect(p, r, 0.03) for r in fixed_pads.get(net, []))

        def terminal(p):
            return on_via(p) or on_fixed_pad(p)

        # BFS include: seg endpoints within 1.45 of a seed rect; do not
        # expand through terminal nodes (segment touching terminal is
        # included, its other side is not crossed).
        included = set()
        frontier = []
        for t in trks:
            a, bb = seg_pts(t)
            if any(in_rect(a, r, 0.05) or in_rect(bb, r, 0.05) for r in seed_rects):
                included.add(id(t))
                frontier.append(t)
        while frontier:
            cur = frontier.pop()
            ca, cb = seg_pts(cur)
            for t in trks:
                if id(t) in included:
                    continue
                a, bb = seg_pts(t)
                if min(rect_dist(a, r) for r in seed_rects) > 1.45 or \
                   min(rect_dist(bb, r) for r in seed_rects) > 1.45:
                    continue
                for p, q in ((a, ca), (a, cb), (bb, ca), (bb, cb)):
                    if near(p, q, 0.045) and not terminal(q):
                        included.add(id(t))
                        frontier.append(t)
                        break
                else:
                    # T-joint: endpoint of t on cur, cur's endpoint not terminal
                    if (pt_seg(a, ca, cb) <= 0.045 and not terminal(a)) or \
                       (pt_seg(bb, ca, cb) <= 0.045 and not terminal(bb)):
                        included.add(id(t))
                        frontier.append(t)
        inc_trks = [t for t in trks if id(t) in included]
        kept_trks = [t for t in trks if id(t) not in included]

        def node_moves(p):
            if terminal(p):
                return False
            for t in kept_trks:
                a, bb = seg_pts(t)
                if near(p, a, 0.045) or near(p, bb, 0.045) or pt_seg(p, a, bb) <= 0.045:
                    return False
            return True

        for t in inc_trks:
            a, bb = seg_pts(t)
            ma, mb = node_moves(a), node_moves(bb)
            if not (ma or mb):
                continue
            na = (a[0] + DX, a[1]) if ma else a
            nb = (bb[0] + DX, bb[1]) if mb else bb
            lay, w = t.GetLayer(), t.GetWidth()
            b.Remove(t)
            if abs(na[0] - nb[0]) < 1e-6 and abs(na[1] - nb[1]) < 1e-6:
                n_col += 1
                continue
            nt = pcbnew.PCB_TRACK(b)
            nt.SetNetCode(NC[net])
            nt.SetLayer(lay)
            nt.SetStart(pcbnew.VECTOR2I(int(round(na[0] * IU)), int(round(na[1] * IU))))
            nt.SetEnd(pcbnew.VECTOR2I(int(round(nb[0] * IU)), int(round(nb[1] * IU))))
            nt.SetWidth(w)
            b.Add(nt)
            n_re += 1
    print(f'{ref}: re-emitted {n_re}, collapsed {n_col}')

for ref, DX in MOVES:
    refan(ref, DX)

b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(DST)
b2 = pcbnew.LoadBoard(DST)
new = census(b2)
print('census diffs (only changed):')
for k in sorted(set(base) | set(new)):
    if base.get(k, 0) != new.get(k, 0):
        print(f'  {k}: {base.get(k,0)} -> {new.get(k,0)}')
print('saved', DST)
