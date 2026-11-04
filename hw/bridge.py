#!/usr/bin/env python3
"""Bridge the nearest pair of groups of one net with hand copper.

For nets whose groups pass within ~2 mm of each other behind a
thin fence: find the nearest cross-group shape pair (audit-exact
gaps), try direct and single-bend segments between the pair's
closest points on their shared layer, rip up to 3 foreign items
blocking the best candidate, and place it. Victims are healed by
the next repairg round.

Run: xvfb-run -a python3 hw/bridge.py IN OUT NET [NET ...]
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb, repair6
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
MM = pcbnew.FromMM
LAYERS = (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)

def seg(x1, y1, x2, y2, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x1), MM(y1)),
                                pcbnew.VECTOR2I(MM(x2), MM(y2)),
                                MM(w))

def gapf(s1, l1, s2, l2):
    shared = l1 & l2
    if not shared:
        return None
    if s1.Collide(s2, MM(0.0)):
        return 0.0
    lo, hi = 0.0, 3.0
    if not s1.Collide(s2, MM(hi)):
        return None
    for _ in range(12):
        mid = (lo + hi) / 2
        if s1.Collide(s2, MM(mid)):
            hi = mid
        else:
            lo = mid
    return hi

def groups_of(items, net):
    its = [it for it in items if it[1] == net]
    n = len(its)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i in range(n):
        for j in range(i + 1, n):
            if gapf(its[i][3], its[i][2], its[j][3], its[j][2]) == 0.0:
                parent[find(i)] = find(j)
    from collections import defaultdict
    g = defaultdict(list)
    for i in range(n):
        g[find(i)].append(its[i])
    return list(g.values())

def blockers(items, net, shape, layer):
    out = []
    for kind, n2, l2, s2, d2 in items:
        if n2 == net:
            continue
        shared = {layer} & l2
        if not shared:
            continue
        need = check_pcb.need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001)):
            out.append((kind, n2, d2))
    return out

def main():
    src, out = sys.argv[1], sys.argv[2]
    nets = sys.argv[3:]
    board = pcbnew.LoadBoard(src)
    width_for = {}
    sys.path.insert(0, 'hw')
    from repair6 import netclass
    for net in nets:
        items = build_items(board)
        gs = groups_of(items, net)
        if len(gs) < 2:
            print(f'{net}: already single-group', flush=True)
            continue
        gs.sort(key=len, reverse=True)
        # nearest cross-group pair
        best = (9.9, None, None)
        for gi in gs[1:]:
            for a in gs[0]:
                for b in gi:
                    v = gapf(a[3], a[2], b[3], b[2])
                    if v is not None and v < best[0]:
                        best = (v, a, b)
        gap, a, b = best
        if a is None or gap > 2.0:
            print(f'{net}: nearest gap {gap} — too far', flush=True)
            continue
        # anchor points: bbox centres of the two shapes, clipped
        # segment between shape bboxes' closest corners is complex;
        # use shape bbox centres pulled to the bbox edges facing
        # each other along the centre line.
        def centre(s):
            bb = s.BBox()
            return (pcbnew.ToMM(bb.GetLeft() + bb.GetWidth() / 2),
                    pcbnew.ToMM(bb.GetTop() + bb.GetHeight() / 2))
        def facing(s, other_centre):
            # point on s's bbox nearest the other shape's centre:
            # the segment then starts at the facing edge, not deep
            # inside a long track's span
            bb = s.BBox()
            ox, oy = other_centre
            x = min(max(ox, pcbnew.ToMM(bb.GetLeft())),
                    pcbnew.ToMM(bb.GetRight()))
            y = min(max(oy, pcbnew.ToMM(bb.GetTop())),
                    pcbnew.ToMM(bb.GetBottom()))
            return (x, y)
        ca, cb = centre(a[3]), centre(b[3])
        (x1, y1), (x2, y2) = facing(a[3], cb), facing(b[3], ca)
        layer = [l for l in LAYERS if l in a[2] and l in b[2]]
        if not layer:
            print(f'{net}: no shared routing layer', flush=True)
            continue
        layer = layer[0]
        w, clr = netclass(net)
        w = max(0.2, min(w, 0.3))
        cands = [
            [(x1, y1, x2, y2)],
            [(x1, y1, x2, y1), (x2, y1, x2, y2)],
            [(x1, y1, x1, y2), (x1, y2, x2, y2)],
        ]
        placed = False
        for cand in cands:
            shapes = [seg(*c, w) for c in cand]
            bl = set()
            for s in shapes:
                bl |= set(blockers(items, net, s, layer))
            rippable = {(n, d) for _, n, d in bl
                        if d in ('track@stubcheck', 'via@stubcheck')}
            if len(bl) - len(rippable) > 0 or len(rippable) > 3:
                continue
            # rip the blockers (re-test board tracks against shapes)
            if rippable:
                for t in list(board.GetTracks()):
                    if t.GetNetname() == net:
                        continue
                    if not t.IsOnLayer(layer):
                        continue
                    ts = t.GetEffectiveShape()
                    for s in shapes:
                        need = check_pcb.need_for(
                            net, t.GetNetname(), {layer})
                        if s.Collide(ts, MM(need - 0.001)):
                            board.Remove(t)
                            break
                items = build_items(board)
                if any(blockers(items, net, s, layer)
                       for s in shapes):
                    continue
            netobj = board.FindNet(net)
            for (px, py, qx, qy) in cand:
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(MM(px), MM(py)))
                t.SetEnd(pcbnew.VECTOR2I(MM(qx), MM(qy)))
                t.SetWidth(MM(w))
                t.SetLayer(layer)
                t.SetNet(netobj)
                board.Add(t)
            print(f'{net}: bridged gap {gap:.2f} on layer {layer} '
                  f'via {len(cand)} seg(s), ripped '
                  f'{len(rippable)}', flush=True)
            placed = True
            break
        if not placed:
            print(f'{net}: no bridge placed (gap {gap:.2f})',
                  flush=True)
    repair6.save_checkpoint(board, out)
    print('saved', out, flush=True)

if __name__ == "__main__":
    main()
