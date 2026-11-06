#!/usr/bin/env python3
"""Model-gap analysis: for every audit-flagged via/track on the v5
board, ask whether the router's OWN clearance model (point-sampled
dist_to_item tests, as in router.blocked) accepts the item, and
whether an EXACT segment-capsule distance test accepts it.

Classifies each flagged item:
  MODEL-ACCEPTS  -> the router believed it was legal: a model gap.
                    Sub-classify point-vs-exact for tracks: if the
                    point model accepts but the exact test rejects,
                    the gap is sampling; if both accept, the gap is
                    elsewhere (zone, exemption, neck mismatch...).
  MODEL-REJECTS  -> the router model also forbids it: the item was
                    placed by a path that did not apply the test
                    (or the registry differed at route time).

Run: xvfb-run -a python3 hw/analyze_model_gap.py [board] [audit.txt]
"""
import math, re, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import router
from router import Items, netclass, dist_to_item, LAYERS
import repair

MM = pcbnew.FromMM

# ---------- exact geometry (candidate v6 model) ----------

def pt_seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def segs_cross(ax, ay, bx, by, cx, cy, dx, dy):
    def s(px, py, qx, qy, rx, ry):
        return (qx - px) * (ry - py) - (qy - py) * (rx - px)
    d1 = s(cx, cy, dx, dy, ax, ay); d2 = s(cx, cy, dx, dy, bx, by)
    d3 = s(ax, ay, bx, by, cx, cy); d4 = s(ax, ay, bx, by, dx, dy)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))

def seg_seg_dist(ax, ay, bx, by, cx, cy, dx, dy):
    if segs_cross(ax, ay, bx, by, cx, cy, dx, dy):
        return 0.0
    return min(pt_seg_dist(ax, ay, cx, cy, dx, dy),
               pt_seg_dist(bx, by, cx, cy, dx, dy),
               pt_seg_dist(cx, cy, ax, ay, bx, by),
               pt_seg_dist(dx, dy, ax, ay, bx, by))

def seg_item_dist(item, ax, ay, bx, by):
    """Exact distance from segment AB to the item's copper SURFACE
    (same convention as router.dist_to_item: 0 inside/on)."""
    kind = item[0]
    if kind == 'pad':
        (cx, cy, hw, hh, rot) = item[2]
        c, s = math.cos(-rot), math.sin(-rot)
        def loc(x, y):
            dx, dy = x - cx, y - cy
            return (dx * c - dy * s, dx * s + dy * c)
        lax, lay = loc(ax, ay); lbx, lby = loc(bx, by)
        # segment vs rectangle [-hw,hw]x[-hh,hh] in local frame
        def inside(lx, ly):
            return abs(lx) <= hw and abs(ly) <= hh
        if inside(lax, lay) or inside(lbx, lby):
            return 0.0
        edges = [(-hw, -hh, hw, -hh), (hw, -hh, hw, hh),
                 (hw, hh, -hw, hh), (-hw, hh, -hw, -hh)]
        return min(seg_seg_dist(lax, lay, lbx, lby, *e) for e in edges)
    if kind == 'seg':
        (x1, y1, x2, y2, hw) = item[2]
        return seg_seg_dist(ax, ay, bx, by, x1, y1, x2, y2) - hw
    (cx, cy, r) = item[2]  # via
    return pt_seg_dist(cx, cy, ax, ay, bx, by) - r

def point_item_dist(item, x, y):
    return dist_to_item(item, x, y)

# ---------- model verdicts ----------

def via_model_verdict(items, net, x, y, r):
    """Router's own via test (both endpoints layers + middle skipped?
    we test ALL 3 layers here to expose the F<->B middle-layer gap),
    point distance. Returns (ok_all3, ok_tested_pairs_only, worst)."""
    clr = netclass(net)[1]
    worst = 1e9; worst_layers = 1e9
    for li in range(3):
        for it in items[li].near(li, x, y):
            if it[1] == net:
                continue
            need = r + max(clr if not (net in router.HV_NETS and li == 1) else 0.3,
                           it[3] if not (it[1] in router.HV_NETS and li == 1) else 0.3)
            d = point_item_dist(it, x, y)
            worst = min(worst, d - need)
    return worst

def track_verdicts(items, li, net, ax, ay, bx, by, hw_):
    """(point-sample verdict, exact verdict): worst signed margin
    (distance - need) over foreign items near the segment. Point
    model samples endpoints + midpoint (router v5 behaviour);
    exact uses seg_item_dist over the whole segment."""
    clr = netclass(net)[1]
    my_clr = 0.3 if (net in router.HV_NETS and li == 1) else clr
    worst_pt = 1e9; worst_ex = 1e9
    cand = set()
    for (qx, qy) in ((ax, ay), (bx, by), ((ax + bx) / 2, (ay + by) / 2)):
        for it in items[li].near(li, qx, qy):
            cand.add(id(it))
    for it in items[li].near(li, (ax + bx) / 2, (ay + by) / 2):
        cand.add(id(it))
    byid = {id(it): it for it in items[li].near(li, (ax + bx) / 2, (ay + by) / 2)}
    # gather broadly: near() at 5 sample points, dedupe by identity
    seen = {}
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        qx, qy = ax + (bx - ax) * t, ay + (by - ay) * t
        for it in items[li].near(li, qx, qy):
            seen[id(it)] = it
    for it in seen.values():
        if it[1] == net:
            continue
        it_clr = 0.3 if (it[1] in router.HV_NETS and li == 1) else it[3]
        need = hw_ + max(my_clr, it_clr)
        for (qx, qy) in ((ax, ay), (bx, by), ((ax + bx) / 2, (ay + by) / 2)):
            worst_pt = min(worst_pt, point_item_dist(it, qx, qy) - need)
        worst_ex = min(worst_ex, seg_item_dist(it, ax, ay, bx, by) - need)
    return worst_pt, worst_ex

def main():
    board_path = sys.argv[1] if len(sys.argv) > 1 else "hw/pdlvds_rx.kicad_pcb"
    audit_path = sys.argv[2] if len(sys.argv) > 2 else "results/pcb-audit.txt"
    flagged_vias = set()    # (x, y) rounded 3dp
    flagged_tracks = set()  # (x, y) of GetPosition == start point
    for l in open(audit_path):
        m = re.match(r'\s*CLEARANCE (\S+) \((.*?)\) vs (\S+) \((.*?)\):', l)
        if not m:
            continue
        for d in (m.group(2), m.group(4)):
            mv = re.match(r'(via|track)@\(([\d.]+), ([\d.]+)\)', d)
            if mv:
                (flagged_vias if mv.group(1) == 'via' else flagged_tracks).add(
                    (round(float(mv.group(2)), 3), round(float(mv.group(3)), 3)))
    board = pcbnew.LoadBoard(board_path)
    items, _ = repair.build_items(board)
    print(f"flagged in audit: {len(flagged_vias)} via positions, "
          f"{len(flagged_tracks)} track starts")
    via_cls = {"model-accepts": 0, "model-rejects": 0}
    via_examples = {"model-accepts": [], "model-rejects": []}
    for t in board.GetTracks():
        if not isinstance(t, pcbnew.PCB_VIA):
            continue
        p = pcbnew.ToMM(t.GetPosition())
        key = (round(p[0], 3), round(p[1], 3))
        if key not in flagged_vias:
            continue
        net = t.GetNetname()
        r = pcbnew.ToMM(t.GetWidth()) / 2
        worst = via_model_verdict(items, net, p[0], p[1], r)
        cls = "model-accepts" if worst >= 0 else "model-rejects"
        via_cls[cls] += 1
        if len(via_examples[cls]) < 6:
            via_examples[cls].append((net, key, round(worst, 3)))
    print("VIAS:", via_cls)
    for k, v in via_examples.items():
        print(f"  {k}: {v}")
    tr_cls = {"both-accept": 0, "point-only-accepts (sampling gap)": 0,
              "both-reject": 0}
    tr_examples = {k: [] for k in tr_cls}
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        p = pcbnew.ToMM(t.GetPosition())
        key = (round(p[0], 3), round(p[1], 3))
        if key not in flagged_tracks:
            continue
        net = t.GetNetname()
        li = LAYERS.index(t.GetLayer())
        a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
        hw_ = pcbnew.ToMM(t.GetWidth()) / 2
        wpt, wex = track_verdicts(items, li, net, a[0], a[1], b[0], b[1], hw_)
        if wpt >= 0 and wex >= 0:
            cls = "both-accept"
        elif wpt >= 0:
            cls = "point-only-accepts (sampling gap)"
        else:
            cls = "both-reject"
        tr_cls[cls] += 1
        if len(tr_examples[cls]) < 6:
            tr_examples[cls].append((net, key, round(wpt, 3), round(wex, 3)))
    print("TRACKS (by flagged start point):", tr_cls)
    for k, v in tr_examples.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    main()
