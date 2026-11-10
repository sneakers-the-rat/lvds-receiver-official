#!/usr/bin/env python3
"""bl build: re-place U7 +0.75 east on exp257 -> exp259.
Translates all copper of U7-touching nets (except GND) inside the
district box by +0.75x, clipping segments at the box boundary and
bridging boundary crossings. GND escape stubs ending at U7 pads are
sheared (pad-side endpoint +0.75). Zone refill, save, reload census."""
import wx
_app = wx.App(False)
import pcbnew

IU = 1e6
SRC, DST = 'hw/pdlvds_rx.exp257.kicad_pcb', 'hw/pdlvds_rx.exp259.kicad_pcb'
DX = 0.75
BOX = (68.5, 6.0, 81.0, 21.0)  # x0,y0,x1,y1
NETS = ['+3V3A', '+5V', 'DP_PHY', 'DM_PHY', 'ULPI_NXT', 'ULPI_DIR',
        'ULPI_STP', 'ULPI_CK', 'PHY_1V8', 'ULPI_D0', 'ULPI_D1', 'ULPI_D2',
        'ULPI_D3', 'ULPI_D4', 'ULPI_D5', 'ULPI_D6', 'ULPI_D7', 'XO', 'XI',
        'PHY_1V8A', 'RBIAS']

b = pcbnew.LoadBoard(SRC)
NC = {n: b.GetNetcodeFromNetname(n) for n in NETS + ['GND']}

def census(board):
    out = {}
    for t in board.GetTracks():
        k = (t.GetNetname(), 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk')
        out[k] = out.get(k, 0) + 1
    return out

base = census(b)

def inside(p):
    return BOX[0] <= p[0] <= BOX[2] and BOX[1] <= p[1] <= BOX[3]

def clip_ts(a, bb):
    """Liang-Barsky: t-interval of segment a->bb inside BOX."""
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
    t = pcbnew.PCB_TRACK(board)
    t.SetNetCode(NC[net])
    t.SetLayer(layer)
    t.SetStart(pcbnew.VECTOR2I(int(a[0] * IU), int(a[1] * IU)))
    t.SetEnd(pcbnew.VECTOR2I(int(bb[0] * IU), int(bb[1] * IU)))
    t.SetWidth(int(w * IU))
    board.Add(t)

stats = {'split': 0, 'bridge': 0, 'moved_via': 0, 'shear_gnd': 0}
# --- tracks of NETS: clip + translate + bridge
victims = []
for t in list(b.GetTracks()):
    n = t.GetNetname()
    if n not in NETS:
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        c = (p.x / IU, p.y / IU)
        if inside(c):
            t.SetPosition(pcbnew.VECTOR2I(int((c[0] + DX) * IU), int(c[1] * IU)))
            stats['moved_via'] += 1
        continue
    s, e = t.GetStart(), t.GetEnd()
    a, bb = (s.x / IU, s.y / IU), (e.x / IU, e.y / IU)
    iv = clip_ts(a, bb)
    if iv is None:
        continue
    t0, t1 = iv
    if t0 <= 1e-9 and t1 >= 1 - 1e-9:
        t.SetStart(pcbnew.VECTOR2I(int((a[0] + DX) * IU), int(a[1] * IU)))
        t.SetEnd(pcbnew.VECTOR2I(int((bb[0] + DX) * IU), int(bb[1] * IU)))
        continue
    # partial: rebuild as outside piece(s) + translated inside + bridges
    victims.append(t)
    lay, w = t.GetLayer(), t.GetWidth() / IU
    pts = [a]
    if t0 > 1e-9:
        pts.append(lerp(a, bb, t0))
    if t1 < 1 - 1e-9:
        pts.append(lerp(a, bb, t1))
    pts.append(bb)
    # pieces: [p0..pk]; inside piece is between the two boundary points
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
        if abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6:
            continue
        add_trk(b, n, lay, p, q, w)
        stats['split'] += 1
        if kind == 'bridge':
            stats['bridge'] += 1
for t in victims:
    b.Remove(t)

# --- GND stubs ending at U7 pads: shear pad-side endpoints
u7 = None
for fp in b.GetFootprints():
    if fp.GetReference() == 'U7':
        u7 = fp
oldpads = []
for pad in u7.Pads():
    if pad.GetNetname() == 'GND':
        bb2 = pad.GetBoundingBox()
        oldpads.append((bb2.GetLeft() / IU - 0.05, bb2.GetTop() / IU - 0.05,
                        bb2.GetRight() / IU + 0.05, bb2.GetBottom() / IU + 0.05))
for t in list(b.GetTracks()):
    if t.GetNetname() != 'GND' or t.Type() == pcbnew.PCB_VIA_T:
        continue
    s, e = t.GetStart(), t.GetEnd()
    for pt, setter in ((s, 's'), (e, 'e')):
        c = (pt.x / IU, pt.y / IU)
        if any(r[0] <= c[0] <= r[2] and r[1] <= c[1] <= r[3] for r in oldpads):
            np_ = pcbnew.VECTOR2I(int((c[0] + DX) * IU), int(c[1] * IU))
            if setter == 's':
                t.SetStart(np_)
            else:
                t.SetEnd(np_)
            stats['shear_gnd'] += 1

# --- move the footprint
p = u7.GetPosition()
u7.SetPosition(pcbnew.VECTOR2I(int((p.x / IU + DX) * IU), int(p.y / IU)))
print('stats:', stats)
b.BuildConnectivity()
for z in b.Zones():
    z.ClearFilledPolygonsList()
    z.SetNeedRefill(True)
try:
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
except Exception as ex:
    print('zone fill note:', ex)
b.Save(DST)
b2 = pcbnew.LoadBoard(DST)
new = census(b2)
print('census diffs (net,kind): base -> new (only changed):')
for k in sorted(set(base) | set(new)):
    if base.get(k, 0) != new.get(k, 0):
        print(f'  {k}: {base.get(k,0)} -> {new.get(k,0)}')
print('saved', DST)
