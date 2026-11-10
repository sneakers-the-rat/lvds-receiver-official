#!/usr/bin/env python3
"""bl build v2: re-place U7 +0.75 east on exp257 -> exp259.
Only the pad neighbourhood moves: clip zone = U7 pad bbox + 2.0mm.
U7-net copper inside the zone translates +0.75x with boundary
clip+bridge; endpoints lying on FIXED pads or fixed via centres are
anchors and never move (segment shears instead). GND included with
the same rules; GND vias never move. Refill, save, reload census."""
import wx
_app = wx.App(False)
import pcbnew

IU = 1e6
SRC, DST = 'hw/pdlvds_rx.exp257.kicad_pcb', 'hw/pdlvds_rx.exp259.kicad_pcb'
DX = 0.75
NETS = ['+3V3A', '+5V', 'DP_PHY', 'DM_PHY', 'ULPI_NXT', 'ULPI_DIR',
        'ULPI_STP', 'ULPI_CK', 'PHY_1V8', 'ULPI_D0', 'ULPI_D1', 'ULPI_D2',
        'ULPI_D3', 'ULPI_D4', 'ULPI_D5', 'ULPI_D6', 'ULPI_D7', 'XO', 'XI',
        'PHY_1V8A', 'RBIAS', 'GND']

b = pcbnew.LoadBoard(SRC)
NC = {n: b.GetNetcodeFromNetname(n) for n in NETS}

def census(board):
    out = {}
    for t in board.GetTracks():
        k = (t.GetNetname(), 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk')
        out[k] = out.get(k, 0) + 1
    return out

base = census(b)

u7 = None
for fp in b.GetFootprints():
    if fp.GetReference() == 'U7':
        u7 = fp
# zone from U7 pad bbox + 2mm
xs, ys = [], []
for pad in u7.Pads():
    bb = pad.GetBoundingBox()
    xs += [bb.GetLeft() / IU, bb.GetRight() / IU]
    ys += [bb.GetTop() / IU, bb.GetBottom() / IU]
BOX = (min(xs) - 2.0, min(ys) - 2.0, max(xs) + 2.0, max(ys) + 2.0)
print('zone:', [round(v, 2) for v in BOX])
# anchors: fixed pad rects (all footprints except U7) + fixed via centres
pad_rects = []
for fp in b.GetFootprints():
    if fp.GetReference() == 'U7':
        continue
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        pad_rects.append((bb.GetLeft() / IU - 0.02, bb.GetTop() / IU - 0.02,
                          bb.GetRight() / IU + 0.02, bb.GetBottom() / IU + 0.02))

def inside(p):
    return BOX[0] <= p[0] <= BOX[2] and BOX[1] <= p[1] <= BOX[3]

def anchored(p):
    return any(r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3] for r in pad_rects)

# vias: decide movement first (NETS except GND, centre in zone)
via_moves = {}  # id(track) -> new centre
fixed_via_pts = []
for t in b.GetTracks():
    if t.Type() != pcbnew.PCB_VIA_T:
        continue
    p = t.GetPosition()
    c = (p.x / IU, p.y / IU)
    if t.GetNetname() in NETS and t.GetNetname() != 'GND' and inside(c):
        via_moves[id(t)] = (c[0] + DX, c[1])
    else:
        fixed_via_pts.append(c)

def anchored2(p):
    if anchored(p):
        return True
    return any(abs(p[0] - v[0]) < 0.03 and abs(p[1] - v[1]) < 0.03
               for v in fixed_via_pts)

def clip_ts(a, bb):
    t0, t1 = 0.0, 1.0
    dx, dy = bb[0] - a[0], bb[1] - a[1]
    for p, q in ((-dx, a[0] - BOX[0]), (dx, BOX[2] - a[0]),
                 (-dy, a[1] - BOX[1]), (dy, BOX[3] - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return None
        else:
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return None
    return t0, t1

def lerp(a, bb, t):
    return (a[0] + (bb[0] - a[0]) * t, a[1] + (bb[1] - a[1]) * t)

def add_trk(board, net, layer, a, bb, w):
    if abs(a[0] - bb[0]) < 1e-6 and abs(a[1] - bb[1]) < 1e-6:
        return
    t = pcbnew.PCB_TRACK(board)
    t.SetNetCode(NC[net])
    t.SetLayer(layer)
    t.SetStart(pcbnew.VECTOR2I(int(round(a[0] * IU)), int(round(a[1] * IU))))
    t.SetEnd(pcbnew.VECTOR2I(int(round(bb[0] * IU)), int(round(bb[1] * IU))))
    t.SetWidth(int(round(w * IU)))
    board.Add(t)

stats = {'split': 0, 'bridge': 0, 'moved_via': 0, 'shear': 0}
victims = []
for t in list(b.GetTracks()):
    n = t.GetNetname()
    if n not in NETS:
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        if id(t) in via_moves:
            c = via_moves[id(t)]
            t.SetPosition(pcbnew.VECTOR2I(int(round(c[0] * IU)), int(round(c[1] * IU))))
            stats['moved_via'] += 1
        continue
    s, e = t.GetStart(), t.GetEnd()
    a, bb = (s.x / IU, s.y / IU), (e.x / IU, e.y / IU)
    iv = clip_ts(a, bb)
    if iv is None:
        continue
    aa, ab = anchored2(a), anchored2(bb)
    if aa and ab:
        continue
    if aa or ab:
        # shear: anchored end fixed, other end follows clip rule
        free = bb if aa else a
        fixed = a if aa else bb
        nfree = (free[0] + DX, free[1]) if inside(free) else free
        if nfree != free:
            victims.append(t)
            add_trk(b, n, t.GetLayer(), fixed, nfree, t.GetWidth() / IU)
            stats['shear'] += 1
        continue
    t0, t1 = iv
    if t0 <= 1e-9 and t1 >= 1 - 1e-9:
        t.SetStart(pcbnew.VECTOR2I(int(round((a[0] + DX) * IU)), int(round(a[1] * IU))))
        t.SetEnd(pcbnew.VECTOR2I(int(round((bb[0] + DX) * IU)), int(round(bb[1] * IU))))
        continue
    victims.append(t)
    lay, w = t.GetLayer(), t.GetWidth() / IU
    pts = [a]
    if t0 > 1e-9:
        pts.append(lerp(a, bb, t0))
    if t1 < 1 - 1e-9:
        pts.append(lerp(a, bb, t1))
    pts.append(bb)
    pieces = []
    if t0 > 1e-9:
        pieces.append(('out', pts[0], pts[1]))
        pieces.append(('bridge', pts[1], (pts[1][0] + DX, pts[1][1])))
        mid_a = (pts[1][0] + DX, pts[1][1])
    else:
        mid_a = (pts[0][0] + DX, pts[0][1])
    if t1 < 1 - 1e-9:
        mid_b = (pts[-2][0] + DX, pts[-2][1])
        pieces.append(('in', mid_a, mid_b))
        pieces.append(('bridge', mid_b, pts[-2]))
        pieces.append(('out', pts[-2], pts[-1]))
    else:
        pieces.append(('in', mid_a, (pts[-1][0] + DX, pts[-1][1])))
    for kind, p, q in pieces:
        add_trk(b, n, lay, p, q, w)
        stats['split'] += 1
        if kind == 'bridge':
            stats['bridge'] += 1
for t in victims:
    b.Remove(t)

p = u7.GetPosition()
u7.SetPosition(pcbnew.VECTOR2I(p.x + int(DX * IU), p.y))
print('stats:', stats)
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
