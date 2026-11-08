"""t_ai_lib: shared exact-item-model gating helpers for the ai session.
Plain item lists in the t_af18 construction: items[li] is a list of
(kind, net, data, clr) with kind in {'pad','seg','via'}; data layouts
match router.dist_to_item. li: 0=F, 1=In2, 2=B."""
import math, sys
sys.path.insert(0, 'hw')
import pcbnew
from router import dist_to_item, netclass

LAYERS_K = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
EPS = 0.0


def load_items(board):
    items = {0: [], 1: [], 2: []}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetname()
            x, y = pcbnew.ToMM(pad.GetPosition())
            sx, sy = pcbnew.ToMM(pad.GetSize())
            data = (x, y, sx / 2, sy / 2,
                    math.radians(pad.GetOrientationDegrees()))
            clr = netclass(net)[1] if net else 0.2
            for li, ln in enumerate(LAYERS_K):
                if pad.IsOnLayer(ln):
                    items[li].append(('pad', net, data, clr))
    for t in board.GetTracks():
        net = t.GetNetname()
        clr = netclass(net)[1] if net else 0.2
        if isinstance(t, pcbnew.PCB_VIA):
            x, y = pcbnew.ToMM(t.GetPosition())
            r = pcbnew.ToMM(t.GetWidth()) / 2
            for li in range(3):
                items[li].append(('via', net, (x, y, r), clr))
        else:
            if t.GetLayer() not in LAYERS_K:
                continue
            li = LAYERS_K.index(t.GetLayer())
            a = pcbnew.ToMM(t.GetStart())
            b = pcbnew.ToMM(t.GetEnd())
            w = pcbnew.ToMM(t.GetWidth())
            items[li].append(('seg', net,
                              (a[0], a[1], b[0], b[1], w / 2), clr))
    return items


def pair_clr(n1, n2):
    return max(netclass(n1)[1], netclass(n2)[1] if n2 else 0.2)


def pt_margin(li, x, y, net, rad, pool):
    """Min over foreign items in pool of dist - rad - pair clearance."""
    m = 9.9
    worst = None
    for it in pool:
        if it[1] == net:
            continue
        d = dist_to_item(it, x, y) - rad - pair_clr(net, it[1])
        if d < m:
            m, worst = d, it
    return m, worst


def seg_margin(li, a, b, net, hw, pool, step=0.01):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
    m = 9.9
    worst = None
    for k in range(n + 1):
        mm_, w_ = pt_margin(li, a[0] + (b[0] - a[0]) * k / n,
                            a[1] + (b[1] - a[1]) * k / n, net, hw, pool)
        if mm_ < m:
            m, worst = mm_, w_
    return m, worst


def fmt_it(it):
    if it is None:
        return '-'
    k, n, d = it[0], it[1], it[2]
    if k == 'seg':
        return (f'seg {n} ({d[0]:.3f},{d[1]:.3f})->({d[2]:.3f},{d[3]:.3f}) '
                f'hw{d[4]:.3f}')
    if k == 'via':
        return f'via {n} ({d[0]:.3f},{d[1]:.3f}) r{d[2]:.3f}'
    return f'pad {n} ({d[0]:.3f},{d[1]:.3f}) hw{d[2]:.3f}x{d[3]:.3f}'


def in_box_pool(items, box, pad=1.0):
    """items whose geometry can touch the box (box = x0,x1,y0,y1).

    FIX (aj session, 2026-11-07): the old centre-in-expanded-box test
    for pads/vias silently DROPPED large pads whose centre lay more
    than `pad` outside the box while their copper reached inside it
    -- U7's EP (GND, half-size 1.55) vanished from a scan box ending
    at y12.5 (centre y14.0), producing false-positive via points at
    y12.5 with a fabricated +0.015 margin (true margin -0.450).
    Now: a pad/via is included iff its bounding circle comes within
    `pad` of the box. Over-inclusive is safe; under-inclusive lies."""
    x0, x1, y0, y1 = box
    out = {0: [], 1: [], 2: []}
    for li in range(3):
        for it in items[li]:
            k, _n, d = it[0], it[1], it[2]
            if k == 'pad':
                reach = math.hypot(d[2], d[3])
            elif k == 'via':
                reach = d[2]
            if k in ('pad', 'via'):
                dx = max(x0 - d[0], 0.0, d[0] - x1)
                dy = max(y0 - d[1], 0.0, d[1] - y1)
                if math.hypot(dx, dy) <= reach + pad:
                    out[li].append(it)
            else:
                if min(d[0], d[2]) <= x1 + pad and \
                        max(d[0], d[2]) >= x0 - pad and \
                        min(d[1], d[3]) <= y1 + pad and \
                        max(d[1], d[3]) >= y0 - pad:
                    out[li].append(it)
    return out


def match_item(it, spec):
    """spec: (kind, net, x, y) -- for segs, matches either endpoint."""
    kind, net, x, y = spec
    if it[0] != kind or it[1] != net:
        return False
    d = it[2]
    if kind in ('pad', 'via'):
        return abs(d[0] - x) < 0.01 and abs(d[1] - y) < 0.01
    return (abs(d[0] - x) < 0.01 and abs(d[1] - y) < 0.01) or \
        (abs(d[2] - x) < 0.01 and abs(d[3] - y) < 0.01)


def apply_rip(items, specs):
    """Return (statics, n_ripped): items minus any item matching a spec
    (a seg spec rips every seg with that endpoint, iterating to a
    fixpoint so chains named by one endpoint each are caught when the
    caller lists every seg)."""
    out = {0: [], 1: [], 2: []}
    n = 0
    for li in range(3):
        for it in items[li]:
            if any(match_item(it, s) for s in specs):
                n += 1
            else:
                out[li].append(it)
    return out, n
