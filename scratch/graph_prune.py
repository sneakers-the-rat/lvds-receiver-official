#!/usr/bin/env python3
"""Prune dead copper on the true copper-contact graph.

Third instrument for this job, written 2026-11-05 after two failures
that define its design:

- prune_dead.py redraws copper into its own fused-centreline graph;
  its tolerances absorbed real barbs into junctions (363 teeth + 71
  floaters survived it on exp147).
- Deleting whatever KiCad DRC flags as track_dangling is UNSOUND:
  dangling certifies only that an END is free. A track can overshoot
  at one end while bridging two pad groups along its body; deleting
  58 DRC-flagged items split groups (unconnected 50 -> 52).

The sound rule, implemented here on plain data with copper-overlap
contact tolerances (real track widths, via radii, pad bounding
boxes):

- Build the contact graph: segments/vias/pads of a net, edges where
  copper physically touches -- endpoint-to-endpoint, endpoint-to-body
  (T-junctions), body-to-body crossings, pad and via contact.
- A segment is a CANDIDATE when at least one of its endpoints touches
  nothing (the census's tooth/floater condition, with true geometry).
- A candidate is DELETABLE iff all the pad groups it touches (through
  every contact, body crossings included) number at most one --
  removing it then provably cannot split any pad group.
- Peel deletable candidates and repeat: chains of dead segments peel
  leaf by leaf; bridging overshoot tracks are kept, correctly --
  they are live routes, not dead copper.

Zone (pour) nets are excluded entirely: zone contact is not modelled,
so pour-net segments are never candidates here.

KiCad DRC is the referee afterwards: unconnected_items must be
unchanged (same count, same pad partition); track_dangling falls by
the number of dead segments removed (minus bridging tracks DRC flags
but this graph proves live).

Usage: python3 scratch/graph_prune.py IN.kicad_pcb OUT.kicad_pcb
"""
import sys, math
from collections import defaultdict
import pcbnew

CU = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
src, dst = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)

zone_nets = {z.GetNetname() for z in board.Zones()}

segs = []   # dict per segment
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_TRACE_T:
        a, b = t.GetStart(), t.GetEnd()
        segs.append({'net': t.GetNetname(), 'layer': t.GetLayer(),
                     'x0': a.x, 'y0': a.y, 'x1': b.x, 'y1': b.y,
                     'w': t.GetWidth(), 'dead': False})
vias = []
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        vias.append({'net': t.GetNetname(), 'x': p.x, 'y': p.y,
                     'r': t.GetWidth() // 2})
pads = []
for fp in board.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        pads.append({'net': p.GetNetname(),
                     'layers': {l for l in CU if p.IsOnLayer(l)},
                     'bb': (bb.GetLeft(), bb.GetTop(),
                            bb.GetRight(), bb.GetBottom())})

via_by_net = defaultdict(list)
for i, v in enumerate(vias):
    via_by_net[v['net']].append(i)
pad_by_net = defaultdict(list)
for i, p in enumerate(pads):
    pad_by_net[p['net']].append(i)
seg_by_nl = defaultdict(list)
for i, s in enumerate(segs):
    seg_by_nl[(s['net'], s['layer'])].append(i)

def seg_seg_contact(s, o):
    """Return (contact?, endmask_s, endmask_o): which endpoints of s
    and o participate in the contact (bit0 = start, bit1 = end);
    contact with both masks 0 = pure body crossing."""
    reach = s['w'] // 2 + o['w'] // 2 + 1000
    ms = mo = 0
    contact = False
    pts_s = ((s['x0'], s['y0']), (s['x1'], s['y1']))
    pts_o = ((o['x0'], o['y0']), (o['x1'], o['y1']))
    for i, (x, y) in enumerate(pts_s):
        for j, (px, py) in enumerate(pts_o):
            if math.hypot(px - x, py - y) <= reach:
                contact = True
                ms |= 1 << i
                mo |= 1 << j
    def pt_seg(x, y, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        if L2 == 0:
            return math.hypot(x - a[0], y - a[1])
        t = ((x - a[0]) * dx + (y - a[1]) * dy) / L2
        t = max(0.0, min(1.0, t))
        return math.hypot(x - (a[0] + t * dx), y - (a[1] + t * dy))
    for i, (x, y) in enumerate(pts_s):
        if pt_seg(x, y, pts_o[0], pts_o[1]) <= reach:
            # near o's body: endpoint of s touches o; touches o at an
            # endpoint only if that endpoint is the near point
            contact = True
            ms |= 1 << i
            for j, (px, py) in enumerate(pts_o):
                if math.hypot(px - x, py - y) <= reach:
                    mo |= 1 << j
    for j, (x, y) in enumerate(pts_o):
        if pt_seg(x, y, pts_s[0], pts_s[1]) <= reach:
            contact = True
            mo |= 1 << j
            for i, (px, py) in enumerate(pts_s):
                if math.hypot(px - x, py - y) <= reach:
                    ms |= 1 << i
    if not contact:
        # pure body crossing: segment intersection test
        def orient(ax, ay, bx, by, cx, cy):
            return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        (ax, ay), (bx, by) = pts_s
        (cx, cy), (dx, dy) = pts_o
        d1 = orient(cx, cy, dx, dy, ax, ay)
        d2 = orient(cx, cy, dx, dy, bx, by)
        d3 = orient(ax, ay, bx, by, cx, cy)
        d4 = orient(ax, ay, bx, by, dx, dy)
        if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
            contact = True
    return contact, ms, mo

# contacts: for each seg, set of ('s', idx) / ('v', idx) / ('p', idx)
contacts = [set() for _ in segs]
end_segs = [[set(), set()] for _ in segs]     # segs touching each end
end_fixed = [[False, False] for _ in segs]    # pad/via touch at an end
for (net, layer), idxs in seg_by_nl.items():
    if net in zone_nets:
        continue
    for a in range(len(idxs)):
        for b in range(a + 1, len(idxs)):
            i, j = idxs[a], idxs[b]
            c, mi, mj = seg_seg_contact(segs[i], segs[j])
            if c:
                contacts[i].add(('s', j))
                contacts[j].add(('s', i))
                for k in (0, 1):
                    if mi & (1 << k):
                        end_segs[i][k].add(j)
                    if mj & (1 << k):
                        end_segs[j][k].add(i)
for i, s in enumerate(segs):
    if s['net'] in zone_nets:
        continue
    hw = s['w'] // 2
    for vi in via_by_net.get(s['net'], ()):
        v = vias[vi]
        rr = v['r'] + hw + 1000
        d = min(math.hypot(s['x0'] - v['x'], s['y0'] - v['y']) ,
                math.hypot(s['x1'] - v['x'], s['y1'] - v['y']))
        # body-to-via: distance from via centre to segment
        dx, dy = s['x1'] - s['x0'], s['y1'] - s['y0']
        L2 = dx * dx + dy * dy
        if L2:
            t = max(0.0, min(1.0, ((v['x'] - s['x0']) * dx +
                                   (v['y'] - s['y0']) * dy) / L2))
            d = min(d, math.hypot(v['x'] - (s['x0'] + t * dx),
                                  v['y'] - (s['y0'] + t * dy)))
        if d <= rr:
            contacts[i].add(('v', vi))
            if math.hypot(s['x0'] - v['x'], s['y0'] - v['y']) <= rr:
                end_fixed[i][0] = True
            if math.hypot(s['x1'] - v['x'], s['y1'] - v['y']) <= rr:
                end_fixed[i][1] = True
    for pi in pad_by_net.get(s['net'], ()):
        p = pads[pi]
        if s['layer'] not in p['layers']:
            continue
        l, t, r, b = p['bb']

        def pt_rect(x, y):
            dx = max(l - x, 0, x - r)
            dy = max(t - y, 0, y - b)
            return math.hypot(dx, dy)

        def pt_seg(x, y):
            dx, dy = s['x1'] - s['x0'], s['y1'] - s['y0']
            L2 = dx * dx + dy * dy
            if L2 == 0:
                return math.hypot(x - s['x0'], y - s['y0'])
            u = max(0.0, min(1.0, ((x - s['x0']) * dx +
                                   (y - s['y0']) * dy) / L2))
            return math.hypot(x - (s['x0'] + u * dx),
                              y - (s['y0'] + u * dy))

        def seg_rect_intersects():
            # Liang-Barsky: does the segment clip into the rect?
            dx, dy = s['x1'] - s['x0'], s['y1'] - s['y0']
            u0, u1 = 0.0, 1.0
            for p_, q_ in ((-dx, s['x0'] - l), (dx, r - s['x0']),
                           (-dy, s['y0'] - t), (dy, b - s['y0'])):
                if p_ == 0:
                    if q_ < 0:
                        return False
                    continue
                u = q_ / p_
                if p_ < 0:
                    u0 = max(u0, u)
                else:
                    u1 = min(u1, u)
                if u0 > u1:
                    return False
            return True

        if seg_rect_intersects():
            d = 0
        else:
            d = min(pt_rect(s['x0'], s['y0']), pt_rect(s['x1'], s['y1']),
                    pt_seg(l, t), pt_seg(r, t), pt_seg(l, b),
                    pt_seg(r, b))
        if d <= hw + 1000:
            contacts[i].add(('p', pi))
            for k, (x, y) in enumerate(((s['x0'], s['y0']),
                                        (s['x1'], s['y1']))):
                if l - hw <= x <= r + hw and t - hw <= y <= b + hw:
                    end_fixed[i][k] = True

# ---- peel: exact per-candidate bridge test, per net ---------------
# A candidate (segment with a free end) is deletable iff, in the graph
# WITHOUT it, its contact-neighbours lie in at most one PAD-BEARING
# component. (A spur off a through-route has one neighbour component
# -> deletable; an overshoot track bridging two pad groups has two
# -> kept.) Kills apply immediately and the test recomputes, so two
# candidates that only jointly bridge are still caught.
seg_by_net = defaultdict(list)
for i, s in enumerate(segs):
    seg_by_net[s['net']].append(i)

def deletable(i):
    net = segs[i]['net']
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for j in seg_by_net[net]:
        if j == i or segs[j]['dead']:
            continue
        for kind, k in contacts[j]:
            if kind == 's' and (k == i or segs[k]['dead']):
                continue
            union(('s', j), (kind, k))
    padcomp = set()
    for pi in pad_by_net.get(net, ()):
        padcomp.add(find(('p', pi)))
    neighbour_padcomps = set()
    for kind, k in contacts[i]:
        if kind == 's' and segs[k]['dead']:
            continue
        r = find((kind, k))
        if r in padcomp:
            neighbour_padcomps.add(r)
    return len(neighbour_padcomps) <= 1

def end_free(i, k):
    if end_fixed[i][k]:
        return False
    return all(segs[j]['dead'] for j in end_segs[i][k])

total_dead = 0
for rnd in range(200):
    killed = 0
    for i, s in enumerate(segs):
        if s['dead'] or s['net'] in zone_nets:
            continue
        if not (end_free(i, 0) or end_free(i, 1)):
            continue                      # no free end: not a candidate
        if deletable(i):
            s['dead'] = True
            killed += 1
    print(f'peel round {rnd}: killed {killed}', flush=True)
    total_dead += killed
    if not killed:
        break
print(f'TOTAL dead: {total_dead}')

alive_keys = {(s['net'], s['layer'], s['x0'], s['y0'], s['x1'], s['y1'])
              for s in segs if not s['dead']}
to_remove = []
for t in board.GetTracks():
    if t.Type() != pcbnew.PCB_TRACE_T:
        continue
    a, b = t.GetStart(), t.GetEnd()
    if (t.GetNetname(), t.GetLayer(), a.x, a.y, b.x, b.y) not in alive_keys:
        to_remove.append(t)
for t in to_remove:
    board.Remove(t)
print(f'removed from board: {len(to_remove)}')
board.Save(dst)
print(f'saved {dst}')
