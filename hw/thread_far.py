#!/usr/bin/env python3
"""Thread one net (far variant: 15 mm pair gate)'s nearest group pair with audit-exact copper.

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
from bridge import groups_of
from repair6 import netclass


def gapf(s1, l1, s2, l2):
    """bridge.gapf with the measurement ceiling raised 3.0 -> 15.0 mm
    (thread_far: the residue pairs are 4-12 mm apart; thread.py's
    3 mm gate refuses them before its lattice ever runs)."""
    shared = l1 & l2
    if not shared:
        return None
    if s1.Collide(s2, MM(0.0)):
        return 0.0
    lo, hi = 0.0, 15.0
    if not s1.Collide(s2, MM(hi)):
        return None
    for _ in range(14):
        mid = (lo + hi) / 2
        if s1.Collide(s2, MM(mid)):
            hi = mid
        else:
            lo = mid
    return hi

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

def rip_targets(board, items, rips):
    """Resolve priced item indices to live board tracks/vias.

    build_items appends track/via items in board.GetTracks()
    order. That correspondence is VERIFIED per priced item
    (net + shape BBox), never assumed: any mismatch returns
    None and the caller aborts the thread rather than ripping
    the wrong copper. (Class T: the pre-fix reconstruction
    re-tested only same-layer path segments and capped removals
    at len(rips), so via-disc-priced victims were never removed
    and the placed vias violated them — pass 76, 15 lines.)
    """
    tracks = list(board.GetTracks())
    track_items = [i for i, it in enumerate(items)
                   if it[0] in ('track', 'via')]
    if len(track_items) != len(tracks):
        return None
    pos = {idx: k for k, idx in enumerate(track_items)}
    out = []
    for idx in sorted(rips):
        it = items[idx]
        t = tracks[pos[idx]]
        if t.GetNetname() != it[1]:
            return None
        bb, tb = it[3].BBox(), t.GetEffectiveShape().BBox()
        if (bb.GetLeft() != tb.GetLeft() or bb.GetTop() != tb.GetTop()
                or bb.GetRight() != tb.GetRight()
                or bb.GetBottom() != tb.GetBottom()):
            return None
        out.append(t)
    return out

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
        return 'no pair within 15 mm'
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
    # Start nodes: the four lattice corners around p0. The anchor
    # stub p0 -> start node is real placed copper, so it is priced
    # like any other segment (Class T): a candidate whose stub
    # hits a wall (unrippable blocker) is discarded, and rippable
    # stub blockers enter the search's rip set at the start node.
    sx = [math.floor(p0[0] / STEP) * STEP,
          math.ceil(p0[0] / STEP) * STEP]
    sy = [math.floor(p0[1] / STEP) * STEP,
          math.ceil(p0[1] / STEP) * STEP]
    start_nodes = sorted({(x, y) for x in sx for y in sy})
    goal = (round(p1[0] / STEP) * STEP, round(p1[1] / STEP) * STEP)
    # node: (layer_idx, gx, gy) in STEP units
    def key(l, x, y):
        return (l, int(round(x / STEP)), int(round(y / STEP)))
    start_init = {}
    for (nx, ny) in start_nodes:
        if nx < x0 or nx > x1 or ny < y0 or ny > y1:
            continue
        for li in range(len(LAYERS)):
            if LAYERS[li] not in shared:
                continue
            bl = blockers(items, net, segm(p0[0], p0[1], nx, ny, w),
                          LAYERS[li])
            if not rippable(items, bl) or len(bl) > MAX_RIPS:
                continue
            k = key(li, nx, ny)
            c = RIP_COST * len(bl)
            if k not in start_init or c < start_init[k][0]:
                start_init[k] = (c, frozenset(bl))
    if not start_init:
        return 'anchor stub walled at start'
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
    for sk, (c0, r0) in start_init.items():
        dist[sk] = (c0, r0)
        heapq.heappush(open_heap, (c0, sk))
    found = None
    goal_rips = frozenset()
    while open_heap:
        d, node = heapq.heappop(open_heap)
        if dist.get(node, (1e18,))[0] < d:
            continue
        if node in goal_keys:
            # The goal anchor stub (node -> p1) is placed copper
            # too: price it before accepting this goal node
            # (Class T). A walled stub rejects the node; the
            # search expands through it instead.
            gl, ggx, ggy = node
            sbl = blockers(items, net,
                           segm(ggx * STEP, ggy * STEP,
                                p1[0], p1[1], w),
                           LAYERS[gl])
            if rippable(items, sbl):
                found = node
                goal_rips = frozenset(sbl)
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
    rips = set(dist[found][1]) | set(goal_rips)
    # Execute exactly the priced rips (Class T fix): segment
    # blockers, via-disc blockers and anchor-stub blockers alike
    # are resolved to their live board objects and removed BEFORE
    # any new copper is placed. Resolution failure aborts the
    # thread with nothing placed — placing copper whose priced
    # victims survive is how pass 76 got 15 violations.
    targets = rip_targets(board, items, rips)
    if targets is None:
        return ('rip resolution failed — thread aborted, '
                'nothing placed')
    for t in targets:
        board.Remove(t)
    ripped = len(targets)
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
