#!/usr/bin/env python3
"""Thread one net's nearest group pair with audit-exact copper.

A* over a 0.5 mm lattice in the corridor between the two closest
groups of NET. Every candidate segment is tested with the audit's
own shape math (check_pcb.need_for); foreign items blocking a
segment are priced as rips (tracks/vias cost 1, pads are walls).
Layer changes are vias (0.6 mm disc, audit-tested on all layers).
The winning polyline is placed as real tracks/vias and the priced
items ripped. Victims are repaid by the next repairg heal.

Run: xvfb-run -a python3 hw/thread.py IN OUT NET [NET ...]
"""
import sys, math, heapq
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb, repair6
from hand_stub import build_items
from bridge import groups_of, gapf
from repair6 import netclass

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
MM, TM = pcbnew.FromMM, pcbnew.ToMM
LAYERS = (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
STEP = 0.5
RIP_COST = 6.0
MAX_RIPS = 6

def segm(x1, y1, x2, y2, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x1), MM(y1)),
                                pcbnew.VECTOR2I(MM(x2), MM(y2)), MM(w))

def blockers(items, net, shape, layer):
    # returns ITEM INDICES so rip pricing counts tracks individually
    out = []
    for idx, (kind, n2, l2, s2, d2) in enumerate(items):
        if n2 == net or layer not in l2:
            continue
        need = check_pcb.need_for(net, n2, {layer})
        if shape.Collide(s2, MM(need - 0.001)):
            out.append(idx)
    return out

def via_blockers(items, net, x, y):
    out = []
    shape = segm(x, y, x, y, 0.6)
    for idx, (kind, n2, l2, s2, d2) in enumerate(items):
        if n2 == net:
            continue
        need = check_pcb.need_for(net, n2, l2)
        if shape.Collide(s2, MM(need - 0.001)):
            out.append(idx)
    return out

def rippable(items, bl):
    return all(items[i][4].startswith(('track@', 'via@')) for i in bl)

def thread_one(board, items, net):
    gs = groups_of(items, net)
    if len(gs) < 2:
        return 'single-group'
    # nearest pair of groups + their facing anchor points
    best = (9.9, None, None)
    for i1 in range(len(gs)):
        for i2 in range(i1 + 1, len(gs)):
            for a in gs[i1]:
                for b in gs[i2]:
                    v = gapf(a[3], a[2], b[3], b[2])
                    if v is not None and v < best[0]:
                        best = (v, a, b)
    gap, a, b = best
    if a is None:
        return 'no pair within 3 mm'
    def ctr(s):
        bb = s.BBox()
        return (TM(bb.GetLeft() + bb.GetWidth() / 2),
                TM(bb.GetTop() + bb.GetHeight() / 2))
    def facing(s, oc):
        bb = s.BBox()
        return (min(max(oc[0], TM(bb.GetLeft())), TM(bb.GetRight())),
                min(max(oc[1], TM(bb.GetTop())), TM(bb.GetBottom())))
    ca, cb = ctr(a[3]), ctr(b[3])
    p0, p1 = facing(a[3], cb), facing(b[3], ca)
    shared = [l for l in LAYERS if l in a[2] and l in b[2]]
    if not shared:
        shared = [pcbnew.F_Cu]
    w_net, _ = netclass(net)
    w = max(0.2, min(w_net, 0.3))
    # lattice over the corridor bbox, expanded
    x0 = math.floor((min(p0[0], p1[0]) - 5.0) / STEP) * STEP
    x1 = math.ceil((max(p0[0], p1[0]) + 5.0) / STEP) * STEP
    y0 = math.floor((min(p0[1], p1[1]) - 5.0) / STEP) * STEP
    y1 = math.ceil((max(p0[1], p1[1]) + 5.0) / STEP) * STEP
    starts = [(round(p0[0] / STEP) * STEP, round(p0[1] / STEP) * STEP)]
    goal = (round(p1[0] / STEP) * STEP, round(p1[1] / STEP) * STEP)
    # node: (layer_idx, gx, gy) in STEP units
    def key(l, x, y):
        return (l, int(round(x / STEP)), int(round(y / STEP)))
    start_keys = [key(li, starts[0][0], starts[0][1])
                  for li in range(len(LAYERS)) if LAYERS[li] in shared]
    goal_keys = {key(li, goal[0], goal[1])
                 for li in range(len(LAYERS)) if LAYERS[li] in shared}
    seg_cache = {}
    def edge_cost(l, xa, ya, xb, yb):
        k = (l, xa, ya, xb, yb)
        if k in seg_cache:
            return seg_cache[k]
        shape = segm(xa, ya, xb, yb, w)
        bl = blockers(items, net, shape, LAYERS[l])
        if not rippable(items, bl):
            c = None
        else:
            c = (math.hypot(xb - xa, yb - ya)
                 + RIP_COST * len(bl))
            seg_cache[k] = (c, frozenset(bl))
            return seg_cache[k]
        seg_cache[k] = None
        return None
    via_cache = {}
    def via_cost(x, y):
        k = (x, y)
        if k in via_cache:
            return via_cache[k]
        bl = via_blockers(items, net, x, y)
        if not rippable(items, bl):
            via_cache[k] = None
        else:
            via_cache[k] = (2.0 + RIP_COST * len(bl), frozenset(bl))
        return via_cache[k]
    DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
            (2, 0), (-2, 0), (0, 2), (0, -2),
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)]
    open_heap = []
    dist = {}
    prev = {}
    for sk in start_keys:
        dist[sk] = (0.0, frozenset())
        heapq.heappush(open_heap, (0.0, sk))
    found = None
    while open_heap:
        d, node = heapq.heappop(open_heap)
        if dist.get(node, (1e18,))[0] < d:
            continue
        if node in goal_keys:
            found = node
            break
        l, gx, gy = node
        x, y = gx * STEP, gy * STEP
        cur_rips = dist[node][1]
        for dx, dy in DIRS:
            nx, ny = x + dx * STEP, y + dy * STEP
            if nx < x0 or nx > x1 or ny < y0 or ny > y1:
                continue
            ec = edge_cost(l, x, y, nx, ny)
            if ec is None:
                continue
            c, bl = ec
            nr = cur_rips | bl
            if len(nr) > MAX_RIPS:
                continue
            nk = key(l, nx, ny)
            nd = d + c + RIP_COST * len(bl - cur_rips)
            if nd < dist.get(nk, (1e18,))[0]:
                dist[nk] = (nd, nr)
                prev[nk] = node
                heapq.heappush(open_heap, (nd, nk))
        # via to other layers at this point
        vc = via_cost(x, y)
        if vc is not None:
            c, bl = vc
            nr = cur_rips | bl
            if len(nr) <= MAX_RIPS:
                for l2 in range(len(LAYERS)):
                    if l2 == l:
                        continue
                    nk = key(l2, x, y)
                    nd = d + c + RIP_COST * len(bl - cur_rips)
                    if nd < dist.get(nk, (1e18,))[0]:
                        dist[nk] = (nd, nr)
                        prev[nk] = node
                        heapq.heappush(open_heap, (nd, nk))
    if found is None:
        return f'no thread (gap {gap:.2f})'
    # reconstruct
    path = [found]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    path.reverse()
    rips = dist[found][1]
    # rip exactly the priced items: re-test live tracks against
    # the path; remove only collisions whose (net) matches a priced
    # item AND stop once the priced count is reached per net is
    # impossible (descs are not unique) — instead bound the total:
    # remove collisions in path order until len(rips) reached.
    ripped = 0
    if rips:
        cand = []
        for t in list(board.GetTracks()):
            n2 = t.GetNetname()
            if n2 == net:
                continue
            for i in range(len(path) - 1):
                l1, gx1, gy1 = path[i]
                l2, gx2, gy2 = path[i + 1]
                if l1 != l2 or not t.IsOnLayer(LAYERS[l1]):
                    continue
                s = segm(gx1 * STEP, gy1 * STEP,
                         gx2 * STEP, gy2 * STEP, w)
                need = check_pcb.need_for(net, n2, {LAYERS[l1]})
                if s.Collide(t.GetEffectiveShape(), MM(need - 0.001)):
                    cand.append(t)
                    break
        for t in cand[:len(rips)]:
            board.Remove(t)
            ripped += 1
    netobj = board.FindNet(net)
    segs = vias = 0
    # anchor stubs: from the exact facing points to the nearest
    # lattice nodes on the chosen layers
    def add_track(xa, ya, xb, yb, layer):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(xa), MM(ya)))
        t.SetEnd(pcbnew.VECTOR2I(MM(xb), MM(yb)))
        t.SetWidth(MM(w))
        t.SetLayer(layer)
        t.SetNet(netobj)
        board.Add(t)
    first = path[0]
    add_track(p0[0], p0[1], first[1] * STEP, first[2] * STEP,
              LAYERS[first[0]])
    segs += 1
    for i in range(len(path) - 1):
        l1, gx1, gy1 = path[i]
        l2, gx2, gy2 = path[i + 1]
        if l1 == l2:
            add_track(gx1 * STEP, gy1 * STEP, gx2 * STEP, gy2 * STEP,
                      LAYERS[l1])
            segs += 1
        else:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(MM(gx1 * STEP),
                                          MM(gy1 * STEP)))
            v.SetWidth(MM(0.6))
            v.SetDrill(MM(0.3))
            v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNet(netobj)
            board.Add(v)
            vias += 1
    last = path[-1]
    add_track(last[1] * STEP, last[2] * STEP, p1[0], p1[1],
              LAYERS[last[0]])
    segs += 1
    return (f'threaded gap {gap:.2f}: {segs} segs, {vias} vias, '
            f'ripped {ripped}')

def main():
    src, out, nets = sys.argv[1], sys.argv[2], sys.argv[3:]
    board = pcbnew.LoadBoard(src)
    for net in nets:
        items = build_items(board)
        print(f'{net}: {thread_one(board, items, net)}', flush=True)
    repair6.save_checkpoint(board, out)
    print('saved', out, flush=True)

if __name__ == '__main__':
    main()
