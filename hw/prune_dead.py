#!/usr/bin/env python3
"""Prune zombie copper (owner-directed cleanup, 2026-11-05).

Dead copper = a maximal branch whose free end is NOT a pad and NOT
a zone/pour connection point, plus whole pad-less floating
components (the classic case: a part moved and its old fanout
stayed behind). Through-paths and pad stubs stay; a spur off a
live path is trimmed back to the branch point.

Method, per net, on a geometric graph:
  vertices = track endpoints, T/crossing junctions (split points),
             via centres (one vertex joining all layers), pad
             centres (terminals), and pour-contact points (a track
             point inside a same-net filled zone polygon = pour
             terminal);
  edges    = track sub-segments between consecutive split points.
Leaf-trim to fixpoint: drop edges at non-terminal degree-1
vertices; drop whole components holding no terminal. Map back to
KiCad items: a segment with no live sub-edge is deleted; a segment
whose live part is one strict sub-interval is shortened to it;
anything more complex is left untouched and counted.

PROOF (non-negotiable): the per-net pad-group partition under the
audit's own connectivity model (check_pcb's item set: pads +
tracks + vias + zone fills, Collide-0 union) must be IDENTICAL
before and after. A net whose partition moves has ALL its trims
reverted (fresh reload, re-apply the rest) and is named.

Usage:
  prune_dead.py BOARD --dry-run
  prune_dead.py BOARD OUT [--exclude NET,NET]
Reports removed/shortened counts per net and the longest dead
branches found.
"""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair6

MM = pcbnew.FromMM
ALL_LAYERS = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
MERGE_TOL = 0.05      # split points closer than this are one vertex
REACH_TOL = 0.03      # centreline reach slack for junction detection


# ------------------------------------------------------------------
# audit-model partition (mirrors check_pcb.py exactly)
# ------------------------------------------------------------------
def partition(board):
    items = []   # (kind, net, layers, shape, bbox, desc)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            layers = {l for l in ALL_LAYERS if pad.IsOnLayer(l)}
            items.append(("pad", net, layers, pad.GetEffectiveShape(),
                          pad.GetBoundingBox(),
                          f"{fp.GetReference()}.{pad.GetNumber()}"))
    for t in board.GetTracks():
        net = t.GetNetname()
        if isinstance(t, pcbnew.PCB_VIA):
            layers = set(ALL_LAYERS)
            kind = "via"
        else:
            layers = {t.GetLayer()}
            kind = "track"
        items.append((kind, net, layers, t.GetEffectiveShape(),
                      t.GetBoundingBox(),
                      f"{kind}@{pcbnew.ToMM(t.GetPosition())}"))
    for z in board.Zones():
        net = z.GetNetname()
        layer = z.GetLayer()
        poly = z.GetFilledPolysList(layer)
        if poly.OutlineCount() == 0:
            continue
        items.append(("zone", net, {layer}, poly, z.GetBoundingBox(),
                      f"zone L{layer}"))
    parent = list(range(len(items)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    bynet = {}
    for i, it in enumerate(items):
        bynet.setdefault(it[1], []).append(i)
    for net, idxs in bynet.items():
        for ai in range(len(idxs)):
            for bi in range(ai + 1, len(idxs)):
                a, b = items[idxs[ai]], items[idxs[bi]]
                if not (a[2] & b[2]):
                    continue
                if not a[4].Intersects(b[4]):
                    continue
                try:
                    hit = a[3].Collide(b[3], 0)
                except Exception:
                    hit = True
                if hit:
                    ra, rb = find(idxs[ai]), find(idxs[bi])
                    if ra != rb:
                        parent[ra] = rb
    out = {}
    for net, idxs in bynet.items():
        groups = {}
        for i in idxs:
            if items[i][0] == "pad":
                groups.setdefault(find(i), set()).add(items[i][5])
        out[net] = frozenset(frozenset(g) for g in groups.values())
    return out


# ------------------------------------------------------------------
# geometric graph per net
# ------------------------------------------------------------------
def proj(a, b, p):
    """(s along ab, perpendicular distance) of point p."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return 0.0, math.hypot(p[0] - a[0], p[1] - a[1])
    s = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / math.sqrt(L2)
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2
    qx, qy = a[0] + t * dx, a[1] + t * dy
    return s, math.hypot(p[0] - qx, p[1] - qy)


def seg_intersect(a, b, c, d):
    """centreline crossing point of ab and cd, or None."""
    def cr(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    d1, d2 = cr(c, d, a), cr(c, d, b)
    d3, d4 = cr(a, b, c), cr(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        t = d1 / (d1 - d2) if d1 != d2 else 0.5
        return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    return None


class Seg:
    __slots__ = ('obj', 'layer', 'a', 'b', 'w', 'splits')

    def __init__(self, obj, layer, a, b, w):
        self.obj, self.layer, self.a, self.b, self.w = obj, layer, a, b, w
        self.splits = {0.0: 'end', 1.0: 'end'}  # param t -> kind


def build_graph(board, net, zone_polys):
    """Returns (subedges, segmap, viamap).
    subedges: list of dicts {seg, t0, t1, v0, v1} where v* are
    vertex keys (layer, x, y) except via/pad vertices which are
    ('X', kind, x, y) shared across layers.
    Terminal vertices: pads and pour-contact split points."""
    segs, vias, pads = [], [], []
    for t in board.GetTracks():
        if t.GetNetname() != net:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            vias.append((t, pcbnew.ToMM(t.GetPosition()),
                         pcbnew.ToMM(t.GetWidth())))
        else:
            segs.append(Seg(t, t.GetLayer(), pcbnew.ToMM(t.GetStart()),
                            pcbnew.ToMM(t.GetEnd()),
                            pcbnew.ToMM(t.GetWidth())))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != net:
                continue
            layers = {l for l in ALL_LAYERS if pad.IsOnLayer(l)}
            pads.append((pad, pcbnew.ToMM(pad.GetPosition()),
                         pcbnew.ToMM(pad.GetSize()), layers,
                         f"{fp.GetReference()}.{pad.GetNumber()}"))
    # split points from vias and pads (contact intervals)
    for s in segs:
        L = math.hypot(s.b[0] - s.a[0], s.b[1] - s.a[1])
        if L == 0:
            continue
        for _, c, d in vias:
            dist, perp = proj(s.a, s.b, c)
            if 0 <= dist <= L and perp <= s.w / 2 + d / 2 + REACH_TOL:
                t = dist / L
                for tt in (t - (d / 2) / L, t, t + (d / 2) / L):
                    if 0.0 < tt < 1.0:
                        s.splits[tt] = 'via'
        for _, c, sz, layers, _desc in pads:
            if s.layer not in layers:
                continue
            dist, perp = proj(s.a, s.b, c)
            r = max(sz) / 2
            if 0 <= dist <= L and perp <= s.w / 2 + r + REACH_TOL:
                t = dist / L
                for tt in (t - r / L, t, t + r / L):
                    if 0.0 < tt < 1.0:
                        s.splits[tt] = 'pad'
    # split points from other segments' endpoints + crossings
    for i, s in enumerate(segs):
        L = math.hypot(s.b[0] - s.a[0], s.b[1] - s.a[1])
        if L == 0:
            continue
        for j, o in enumerate(segs):
            if i == j or o.layer != s.layer:
                continue
            for p in (o.a, o.b):
                dist, perp = proj(s.a, s.b, p)
                if 0 < dist < L and perp <= s.w / 2 + o.w / 2 + REACH_TOL:
                    s.splits[dist / L] = 'junction'
            x = seg_intersect(s.a, s.b, o.a, o.b)
            if x is not None:
                dist, _ = proj(s.a, s.b, x)
                if 0 < dist < L:
                    s.splits[dist / L] = 'junction'
    # pour contact: sample segments on zone layers
    if net in zone_polys:
        for s in segs:
            polys = [p for (lay, p) in zone_polys[net] if lay == s.layer]
            if not polys:
                continue
            L = math.hypot(s.b[0] - s.a[0], s.b[1] - s.a[1])
            if L == 0:
                continue
            n = max(2, int(L / 0.05))
            for k in range(n + 1):
                t = k / n
                x = s.a[0] + t * (s.b[0] - s.a[0])
                y = s.a[1] + t * (s.b[1] - s.a[1])
                pt = pcbnew.SHAPE_CIRCLE(
                    pcbnew.VECTOR2I(MM(x), MM(y)), MM(0.005))
                for p in polys:
                    try:
                        if p.Collide(pt, 0):
                            s.splits[t] = 'pour'
                            break
                    except Exception:
                        pass
    # build subedges with merged vertices
    subedges = []

    def vkey(layer, x, y):
        return (layer, round(x / MERGE_TOL), round(y / MERGE_TOL))

    for s in segs:
        ts = sorted(s.splits)
        merged = []
        for t in ts:
            if merged and t - merged[-1][0] < MERGE_TOL / max(
                    math.hypot(s.b[0] - s.a[0], s.b[1] - s.a[1]), 1e-9):
                # keep the stronger kind: pad > pour > via > junction
                order = {'end': 0, 'junction': 1, 'via': 2,
                         'pour': 3, 'pad': 4}
                if order[s.splits[t]] > order[merged[-1][1]]:
                    merged[-1] = (merged[-1][0], s.splits[t])
                continue
            merged.append((t, s.splits[t]))
        for (t0, k0), (t1, k1) in zip(merged, merged[1:]):
            x0 = s.a[0] + t0 * (s.b[0] - s.a[0])
            y0 = s.a[1] + t0 * (s.b[1] - s.a[1])
            x1 = s.a[0] + t1 * (s.b[0] - s.a[0])
            y1 = s.a[1] + t1 * (s.b[1] - s.a[1])
            subedges.append({
                'seg': s, 't0': t0, 't1': t1,
                'v0': vkey(s.layer, x0, y0), 'v1': vkey(s.layer, x1, y1),
                'k0': k0, 'k1': k1, 'len': (t1 - t0) * math.hypot(
                    s.b[0] - s.a[0], s.b[1] - s.a[1])})
    return subedges, segs, vias, pads


def trim(subedges):
    """Leaf-trim; returns set of id(subedge) that survive."""
    adj = {}
    for e in subedges:
        adj.setdefault(e['v0'], []).append(e)
        adj.setdefault(e['v1'], []).append(e)

    def terminal(v, e_end_kind):
        return e_end_kind in ('pad', 'pour')

    alive = {id(e) for e in subedges}
    deg = {}
    for e in subedges:
        for v in (e['v0'], e['v1']):
            deg[v] = deg.get(v, 0) + 1
    changed = True
    while changed:
        changed = False
        for e in subedges:
            if id(e) not in alive:
                continue
            for v, k in ((e['v0'], e['k0']), (e['v1'], e['k1'])):
                if deg.get(v, 0) == 1 and not terminal(v, k):
                    alive.discard(id(e))
                    deg[e['v0']] -= 1
                    deg[e['v1']] -= 1
                    changed = True
                    break
    # components with no terminal end at all: drop wholesale
    comp = {}
    for e in subedges:
        if id(e) not in alive:
            continue
        comp.setdefault(e['v0'], []).append(e)
        comp.setdefault(e['v1'], []).append(e)
    seen = set()
    for e in subedges:
        if id(e) not in alive or id(e) in seen:
            continue
        stack, group, has_term = [e], [], False
        seen.add(id(e))
        while stack:
            cur = stack.pop()
            group.append(cur)
            for v, k in ((cur['v0'], cur['k0']), (cur['v1'], cur['k1'])):
                if terminal(v, k):
                    has_term = True
                for n in comp.get(v, []):
                    if id(n) not in seen:
                        seen.add(id(n))
                        stack.append(n)
        if not has_term:
            for g in group:
                alive.discard(id(g))
    return alive


def main():
    src = sys.argv[1]
    dry = '--dry-run' in sys.argv
    out_path = None if dry else sys.argv[2]
    exclude = set()
    for a in sys.argv:
        if a.startswith('--exclude='):
            exclude = set(a.split('=', 1)[1].split(','))
    board = pcbnew.LoadBoard(src)
    before = partition(board)

    zone_polys = {}
    for z in board.Zones():
        net = z.GetNetname()
        if not net:
            continue
        layer = z.GetLayer()
        poly = z.GetFilledPolysList(layer)
        if poly.OutlineCount() == 0:
            continue
        zone_polys.setdefault(net, []).append((layer, poly))

    nets = sorted({t.GetNetname() for t in board.GetTracks()
                   if t.GetNetname()})
    plan = {}   # net -> (objs_to_delete, [(seg, t_lo, t_hi)])
    report = {}
    for net in nets:
        if net in exclude:
            continue
        subedges, segs, vias, pads = build_graph(board, net, zone_polys)
        if not subedges and not vias:
            continue
        alive = trim(subedges)
        dead_len = sum(e['len'] for e in subedges if id(e) not in alive)
        # map back to segments
        delete, shorten = [], []
        live_by_seg = {}
        for e in subedges:
            live_by_seg.setdefault(id(e['seg']), []).append(e)
        for s in segs:
            es = live_by_seg.get(id(s), [])
            live_es = [e for e in es if id(e) in alive]
            if not es:
                continue
            if not live_es:
                delete.append(s.obj)
                continue
            ts = sorted([(e['t0'], e['t1']) for e in live_es])
            merged = [list(ts[0])]
            ok = True
            for t0, t1 in ts[1:]:
                if t0 <= merged[-1][1] + 1e-9:
                    merged[-1][1] = max(merged[-1][1], t1)
                else:
                    ok = False
                    break
            if not ok:
                continue  # disjoint live parts: leave the segment
            t0, t1 = merged[0]
            if t0 > 1e-9 or t1 < 1 - 1e-9:
                shorten.append((s, t0, t1))
        # vias: dead if no live subedge touches their contact and
        # they touch no pad and no pour
        dead_vias = []
        for vobj, c, d in vias:
            touched = False
            for e in subedges:
                if id(e) not in alive:
                    continue
                s = e['seg']
                dist, perp = proj(s.a, s.b, c)
                L = math.hypot(s.b[0] - s.a[0], s.b[1] - s.a[1])
                if 0 <= dist <= L and perp <= s.w / 2 + d / 2 + REACH_TOL:
                    touched = True
                    break
            if not touched:
                # via still valuable if it touches a pad directly
                pad_hit = False
                for _p, pc, sz, layers, _d in pads:
                    if math.hypot(pc[0] - c[0], pc[1] - c[1]) <= \
                            max(sz) / 2 + d / 2:
                        pad_hit = True
                        break
                if not pad_hit:
                    dead_vias.append(vobj)
        if delete or shorten or dead_vias:
            plan[net] = (delete + dead_vias, shorten)
            report[net] = (len(delete), len(dead_vias), len(shorten),
                           dead_len)
    # apply + prove; revert offenders by reload
    bad = []
    for attempt in range(2):
        for net, (dels, shorts) in plan.items():
            if net in bad:
                continue
            for o in dels:
                board.Remove(o)
            for s, t0, t1 in shorts:
                a = (s.a[0] + t0 * (s.b[0] - s.a[0]),
                     s.a[1] + t0 * (s.b[1] - s.a[1]))
                b = (s.a[0] + t1 * (s.b[0] - s.a[0]),
                     s.a[1] + t1 * (s.b[1] - s.a[1]))
                s.obj.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
                s.obj.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
        after = partition(board)
        bad = [n for n in plan
               if after.get(n) != before.get(n) and n not in bad]
        if not bad:
            break
        print(f"PARTITION MOVED for {bad}: reverting those nets")
        board = pcbnew.LoadBoard(src)
    tot_r = sum(v[0] + v[1] for k, v in report.items() if k not in bad)
    tot_s = sum(v[2] for k, v in report.items() if k not in bad)
    tot_l = sum(v[3] for k, v in report.items() if k not in bad)
    print(f"nets pruned: {len([k for k in report if k not in bad])}, "
          f"reverted: {bad}")
    print(f"segments+vias removed: {tot_r}, tracks shortened: {tot_s}, "
          f"dead length removed: {tot_l:.1f} mm")
    for net in sorted(report, key=lambda n: -report[n][3]):
        d, v, s, L = report[net]
        mark = ' (REVERTED)' if net in bad else ''
        print(f"  {net}: removed {d} segs + {v} vias, shortened {s}, "
              f"dead length {L:.1f} mm{mark}")
    if dry:
        print("dry run: board NOT saved")
        return
    assert all(after.get(n) == before.get(n) for n in plan), \
        "partition proof failed"
    repair6.save_checkpoint(board, out_path)
    print(f"saved {out_path}")


if __name__ == '__main__':
    main()
