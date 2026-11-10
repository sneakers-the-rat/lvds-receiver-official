#!/usr/bin/env python3
"""bl build v3: re-place U7 +0.75 east (C19 +0.35) on exp257 -> exp259.
Per net: flood the copper component touching the part's pads; rip the
flood's tracks lying inside the escape zone (pads bbox + 1.15mm);
re-emit them sheared: endpoints on the part's pads or on interior
joints move by DX, endpoints on kept vias / fixed pads / kept tracks
stay. Vias never move. Refill, save, reload census (expect ~no count
change: a change means a save-rename = crossing foreign copper)."""
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
NC = {n: b.GetNetcodeFromNetname(n) for n in NETS if b.GetNetcodeFromNetname(n) >= 0}

def census(board):
    out = {}
    for t in board.GetTracks():
        k = (t.GetNetname(), 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk')
        out[k] = out.get(k, 0) + 1
    return out

base = census(b)

def pt(t):
    return (t[0], t[1])

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

all_tracks = list(b.GetTracks())
by_net = {}
for t in all_tracks:
    by_net.setdefault(t.GetNetname(), []).append(t)
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
# fixed pad rects per net (pads of parts NOT being moved)
fixed_pads = {}
for fp in b.GetFootprints():
    if fp.GetReference() in dict(MOVES):
        continue
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        fixed_pads.setdefault(pad.GetNetname(), []).append(
            (bb.GetLeft() / IU, bb.GetTop() / IU, bb.GetRight() / IU, bb.GetBottom() / IU))

def refan(ref, DX):
    fp = fps[ref]
    pads = []
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        pads.append((pad.GetNetname(), (bb.GetLeft() / IU, bb.GetTop() / IU,
                                        bb.GetRight() / IU, bb.GetBottom() / IU),
                     pad.GetPosition()))
    xs = [r[0] for _, r, _ in pads] + [r[2] for _, r, _ in pads]
    ys = [r[1] for _, r, _ in pads] + [r[3] for _, r, _ in pads]
    E = (min(xs) - 1.15, min(ys) - 1.15, max(xs) + 1.15, max(ys) + 1.15)
    ripped = {}   # net -> list of tracks
    rejoins = {}  # net -> set of fixed endpoint keys
    for net in {n for n, _, _ in pads if n}:
        items = by_net.get(net, [])
        trks = [t for t in items if t.Type() != pcbnew.PCB_VIA_T]
        vias = [t for t in items if t.Type() == pcbnew.PCB_VIA_T]
        # flood from this part's pads of this net
        seed_rects = [r for n, r, _ in pads if n == net]
        comp = set()
        frontier = []
        for t in trks:
            a, bb = seg_pts(t)
            if any(in_rect(a, r, 0.05) or in_rect(bb, r, 0.05) for r in seed_rects):
                comp.add(id(t))
                frontier.append(t)
        via_pts = []
        for v in vias:
            p = v.GetPosition()
            via_pts.append((p.x / IU, p.y / IU, v.GetWidth() / IU / 2))
        while frontier:
            cur = frontier.pop()
            ca, cb = seg_pts(cur)
            for t in trks:
                if id(t) in comp:
                    continue
                a, bb = seg_pts(t)
                joined = False
                for p in (a, bb):
                    if near(p, ca, 0.045) or near(p, cb, 0.045) or \
                       pt_seg(p, ca, cb) <= 0.045:
                        joined = True
                for p in (ca, cb):
                    if pt_seg(p, a, bb) <= 0.045:
                        joined = True
                if joined:
                    comp.add(id(t))
                    frontier.append(t)
        # rip component tracks fully inside E
        rip = []
        for t in trks:
            if id(t) not in comp:
                continue
            a, bb = seg_pts(t)
            if in_rect(a, E) and in_rect(bb, E):
                rip.append(t)
        if rip:
            ripped[net] = (rip, E, seed_rects, via_pts)
    # endpoint classification + re-emit
    n_rip = n_emit = 0
    for net, (rip, E, seed_rects, via_pts) in ripped.items():
        rip_ids = {id(t) for t in rip}
        # endpoint sharing among ripped set
        def classify(p, self_t):
            if any(in_rect(p, r, 0.05) for r in seed_rects):
                return 'move'
            # on a kept via?
            for (vx, vy, vr) in via_pts:
                if math.hypot(p[0] - vx, p[1] - vy) <= vr + 0.045:
                    return 'fix'
            # on fixed pad of another part?
            for r in fixed_pads.get(net, []):
                if in_rect(p, r, 0.03):
                    return 'fix'
            # shared with a kept track (endpoint or on-segment)?
            for t in by_net.get(net, []):
                if id(t) in rip_ids or t.Type() == pcbnew.PCB_VIA_T:
                    continue
                a, bb = seg_pts(t)
                if near(p, a, 0.045) or near(p, bb, 0.045) or pt_seg(p, a, bb) <= 0.045:
                    return 'fix'
            return 'move'
        for t in rip:
            a, bb = seg_pts(t)
            na = (a[0] + DX, a[1]) if classify(a, t) == 'move' else a
            nb = (bb[0] + DX, bb[1]) if classify(bb, t) == 'move' else bb
            b.Remove(t)
            n_rip += 1
            if abs(na[0] - nb[0]) < 1e-6 and abs(na[1] - nb[1]) < 1e-6:
                continue
            nt = pcbnew.PCB_TRACK(b)
            nt.SetNetCode(NC[net])
            nt.SetLayer(t.GetLayer())
            nt.SetStart(pcbnew.VECTOR2I(int(round(na[0] * IU)), int(round(na[1] * IU))))
            nt.SetEnd(pcbnew.VECTOR2I(int(round(nb[0] * IU)), int(round(nb[1] * IU))))
            nt.SetWidth(t.GetWidth())
            b.Add(nt)
            n_emit += 1
    # move the footprint itself
    p = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(p.x + int(round(DX * IU)), p.y))
    print(f'{ref}: ripped {n_rip}, emitted {n_emit}')
    # refresh track cache for the next part
    return

for ref, DX in MOVES:
    refan(ref, DX)
    all_tracks = list(b.GetTracks())
    by_net = {}
    for t in all_tracks:
        by_net.setdefault(t.GetNetname(), []).append(t)

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
