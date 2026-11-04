#!/usr/bin/env python3
"""Router v6: exact-clearance grid A* for the scripted PCB build.

Design rule (the v6 invariant): EVERY emitted copper item is tested,
before emission, with the exact distance between its true geometry
(segment capsule / via disc) and every foreign item's true geometry,
on every layer it occupies, at the same width the search tested.
There are no entry exemptions and no search/emit width mismatch, so
a board produced by this router passes the audit's clearance check
by construction (zones and cross-footprint pad pairs are not router
output and are accounted separately).

What v5 got wrong (results/model-gap-v5.txt): point-sampled tests
(cell centre + midpoint) missed 18 flagged tracks outright, via
tests covered only the source+target layers while the barrel also
occupies the third routing layer, the neck-down width was chosen by
the search from distance-to-any-own-pad but by emit from
distance-along-path (goal approaches drawn wider than tested), goal
and own-pad entry steps skipped the track test entirely, and GND
stitch vias used an ad-hoc point test.

v6 fixes, point by point:
  * Moves are tested as swept segments: seg_item_dist() is the exact
    Euclidean distance from the segment to a pad OBB / segment /
    via disc (all in surface-distance convention, 0 = touching).
  * A via step tests the via disc on ALL THREE routing layers.
  * Neck width is a per-step geometric property (both endpoints of
    the step inside the neck disc of the SAME own pad); emit groups
    steps by that same property, so drawn width == tested width.
  * No exemptions: steps into own pad cells and tree cells are
    tested like any other step (own-net items are skipped by net
    identity — overlapping them IS the connection).
  * GND stitch vias use the same exact via test as signal vias.
  * Pad entry/exit runs from the TRUE pad centre (anchor), not the
    grid cell centre: the first trial without anchors boxed in 8 of
    13 isolated +3V3A groups instantly — quantisation error up to
    0.18 mm exceeds the legal escape margin at 0.5 mm pitch. The
    anchor segment is tested and drawn identically, so the
    invariant is untouched; vias stay on cell centres.

Search grid, net ordering, classes and neck parameters are inherited
from router.py unchanged: v6 changes the clearance model, not the
search strategy, so the two remain comparable.
"""
import heapq, math, time
import pcbnew

from router import (CELL, W, H, LAYERS, HV_NETS, POWER_NETS, LVDS_NETS,
                    PROMOTE, NECK_W, NECK_R, Items, netclass, cell_of)

MM = pcbnew.FromMM
SAFE = 0.005   # required margin beyond the class clearance (mm);
               # the audit flags gaps < need - 0.001, so 5 um of
               # headroom absorbs float error without costing real
               # routability.

# ---------------- exact geometry ----------------

def pt_seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def _cross(px, py, qx, qy, rx, ry):
    return (qx - px) * (ry - py) - (qy - py) * (rx - px)

def seg_seg_dist(ax, ay, bx, by, cx, cy, dx, dy):
    d1 = _cross(cx, cy, dx, dy, ax, ay); d2 = _cross(cx, cy, dx, dy, bx, by)
    d3 = _cross(ax, ay, bx, by, cx, cy); d4 = _cross(ax, ay, bx, by, dx, dy)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(pt_seg_dist(ax, ay, cx, cy, dx, dy),
               pt_seg_dist(bx, by, cx, cy, dx, dy),
               pt_seg_dist(cx, cy, ax, ay, bx, by),
               pt_seg_dist(dx, dy, ax, ay, bx, by))

def seg_item_dist(item, ax, ay, bx, by):
    """Exact distance from segment AB to the item's copper surface
    (router.dist_to_item convention: surface distance, 0 inside)."""
    kind = item[0]
    if kind == 'pad':
        (cx, cy, hw, hh, rot) = item[2]
        c, s = math.cos(-rot), math.sin(-rot)
        def loc(x, y):
            dx, dy = x - cx, y - cy
            return (dx * c - dy * s, dx * s + dy * c)
        lax, lay = loc(ax, ay); lbx, lby = loc(bx, by)
        if abs(lax) <= hw and abs(lay) <= hh: return 0.0
        if abs(lbx) <= hw and abs(lby) <= hh: return 0.0
        return min(
            seg_seg_dist(lax, lay, lbx, lby, -hw, -hh, hw, -hh),
            seg_seg_dist(lax, lay, lbx, lby, hw, -hh, hw, hh),
            seg_seg_dist(lax, lay, lbx, lby, hw, hh, -hw, hh),
            seg_seg_dist(lax, lay, lbx, lby, -hw, hh, -hw, -hh))
    if kind == 'seg':
        (x1, y1, x2, y2, hw) = item[2]
        return seg_seg_dist(ax, ay, bx, by, x1, y1, x2, y2) - hw
    (cx, cy, r) = item[2]  # via
    return pt_seg_dist(cx, cy, ax, ay, bx, by) - r

def pt_item_dist(item, x, y):
    kind = item[0]
    if kind == 'pad':
        (cx, cy, hw, hh, rot) = item[2]
        dx, dy = x - cx, y - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        ex = max(abs(lx) - hw, 0.0); ey = max(abs(ly) - hh, 0.0)
        return math.hypot(ex, ey)
    if kind == 'seg':
        (x1, y1, x2, y2, hw) = item[2]
        return pt_seg_dist(x, y, x1, y1, x2, y2) - hw
    (cx, cy, r) = item[2]
    return math.hypot(x - cx, y - cy) - r

# ---------------- clearance model ----------------

def _clr(net, stored_clr, li):
    """Layer-aware clearance (mirror of router.blocked/check_pcb):
    the 1.0 mm HV rule is surface creepage; on buried In2.Cu the
    pair clearance for an HV participant is 0.3 mm."""
    if li == 1 and net in HV_NETS:
        return 0.3
    return stored_clr

def _candidates(items_li, li, ax, ay, bx, by):
    seen = {}
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        qx, qy = ax + (bx - ax) * t, ay + (by - ay) * t
        for it in items_li.near(li, qx, qy):
            seen[id(it)] = it
    return seen.values()

def seg_margin(items, li, netname, my_clr, ax, ay, bx, by, hw_):
    """Worst signed margin (surface distance - required gap) of the
    swept segment against foreign items on layer li. >= SAFE means
    the move is legal. Early-exits below SAFE."""
    worst = float('inf')
    for it in _candidates(items[li], li, ax, ay, bx, by):
        if it[1] == netname:
            continue
        need = hw_ + max(_clr(netname, my_clr, li), _clr(it[1], it[3], li))
        d = seg_item_dist(it, ax, ay, bx, by)
        if d - need < worst:
            worst = d - need
            if worst < SAFE:
                return worst
    return worst

def via_margin(items, netname, my_clr, x, y, vr):
    """Worst signed margin of a via disc of radius vr at (x, y),
    tested on ALL routing layers (the barrel occupies all of them).
    In1.Cu is the GND plane: antipads there are carved by the zone
    filler, as in v5."""
    worst = float('inf')
    for li in range(3):
        for it in _candidates(items[li], li, x, y, x, y):
            if it[1] == netname:
                continue
            need = vr + max(_clr(netname, my_clr, li),
                            _clr(it[1], it[3], li))
            d = pt_item_dist(it, x, y)
            if d - need < worst:
                worst = d - need
                if worst < SAFE:
                    return worst
    return worst

def via_size(width):
    """(diameter, drill) for a net of the given full track width —
    the single rule search and emit both use."""
    return (0.8, 0.4) if width >= 0.4 else (0.6, 0.3)

# ---------------- search ----------------

def _neck_hw(width, ax, ay, bx, by, neck_pts):
    """Half-width for one step: necked iff the whole step lies inside
    the neck disc of ONE own pad (both endpoints within NECK_R of
    the same pad centre). A pure function of geometry — emit uses
    the identical rule, so drawn width == tested width."""
    if width <= NECK_W:
        return width / 2
    for (px, py) in neck_pts:
        if (ax - px) ** 2 + (ay - py) ** 2 <= NECK_R ** 2 and \
           (bx - px) ** 2 + (by - py) ** 2 <= NECK_R ** 2:
            return NECK_W / 2
    return width / 2

def astar6(items, starts, goals, netname, width, clr, cap=900000,
           neck_pts=(), via_cost=6, anchors=None):
    """anchors: optional {node: (x, y)} giving the TRUE pad centre
    for pad cells. The first step out of an anchored start node and
    the last step into an anchored goal node are tested (and later
    drawn) from/to the anchor point instead of the cell centre —
    grid quantisation puts cell centres up to 0.18 mm from the pad
    centre, which under exact testing boxes in fine-pitch pads that
    a real router escapes trivially from the true centre. The tested
    segment is still exactly the emitted segment."""
    anchors = anchors or {}
    starts_set = set(starts)
    vr = via_size(width)[0] / 2
    goalset = set(goals)
    openh = []
    gscore = {}
    came = {}
    for node in starts:
        gscore[node] = 0
        heapq.heappush(openh, (0, node))
    hgoals = sorted(goalset)[::max(1, len(goalset) // 300)] or list(goalset)
    def h(node):
        li, cx, cy = node
        return min(abs(cx - gx) + abs(cy - gy) for (_, gx, gy) in hgoals)
    def centre(node):
        return ((node[1] + 0.5) * CELL, (node[2] + 0.5) * CELL)
    visited = 0
    while openh:
        _, node = heapq.heappop(openh)
        if node in goalset and gscore[node] > 0 or \
           (node in goalset and any(s != node for s in starts)):
            path = [node]
            while node in came:
                node = came[node]; path.append(node)
            return list(reversed(path))
        visited += 1
        if visited > cap:
            return None
        li, cx, cy = node
        ax, ay = anchors.get(node, centre(node)) \
            if node in starts_set else centre(node)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            nb = (li, nx, ny)
            ng = gscore[node] + 1
            if nb in gscore and gscore[nb] <= ng:
                continue
            bx, by = anchors.get(nb, centre(nb)) \
                if nb in goalset else centre(nb)
            hw_ = _neck_hw(width, ax, ay, bx, by, neck_pts)
            if seg_margin(items, li, netname, clr,
                          ax, ay, bx, by, hw_) < SAFE:
                continue
            gscore[nb] = ng; came[nb] = node
            heapq.heappush(openh, (ng + h(nb), nb))
        # via steps: the disc is tested on every routing layer
        if 2 <= cx <= W - 3 and 2 <= cy <= H - 3:
            for lj in range(3):
                if lj == li:
                    continue
                nb = (lj, cx, cy)
                ng = gscore[node] + via_cost
                if nb in gscore and gscore[nb] <= ng:
                    continue
                vx, vy = centre(node)   # vias are emitted at cell
                                        # centres, anchored or not
                if via_margin(items, netname, clr, vx, vy, vr) < SAFE:
                    continue
                gscore[nb] = ng; came[nb] = node
                heapq.heappush(openh, (ng + h(nb), nb))
    return None

# ---------------- emission ----------------

def emit6(board, netobj, path, width, items, netname, clr, stats):
    """Draw the path. Steps are grouped into segments only when
    collinear AND of the same width class (neck rule), so every
    drawn segment is exactly a union of steps the search tested at
    that width. Vias use via_size(width) — the size the search
    tested."""
    def centre(node):
        return ((node[1] + 0.5) * CELL, (node[2] + 0.5) * CELL)
    neck_pts = stats.get("neck_pts", ())
    anchors = stats.get("anchors", {})
    def point_of(node, anchored):
        # The first step is drawn from the start node's anchor and
        # the last step to the goal node's anchor when present —
        # exactly as astar6 tested them.
        if anchored and node in anchors:
            return anchors[node]
        return centre(node)
    def draw_seg(li, a, b, w):
        (x1, y1), (x2, y2) = a, b
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        tr.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
        tr.SetWidth(MM(w)); tr.SetLayer(LAYERS[li]); tr.SetNet(netobj)
        board.Add(tr)
        items[li].add(li, ('seg', netname, (x1, y1, x2, y2, w / 2), clr),
                      (min(x1, x2) - 2, min(y1, y2) - 2,
                       max(x1, x2) + 2, max(y1, y2) + 2))
    run = None  # (li, start_pt, last_pt, w)
    def flush():
        nonlocal run
        if run is not None:
            li, a, b, w = run
            if a != b:
                draw_seg(li, a, b, w)
            run = None
    for i, (a_node, b_node) in enumerate(zip(path, path[1:])):
        if a_node[0] == b_node[0]:
            li = a_node[0]
            a = point_of(a_node, i == 0)
            b = point_of(b_node, i == len(path) - 2)
            hw_ = _neck_hw(width, a[0], a[1], b[0], b[1], neck_pts)
            w = hw_ * 2
            if run is not None and run[0] == li and run[3] == w and \
               run[2] == a and \
               (run[1][0] == a[0] == b[0] or run[1][1] == a[1] == b[1]):
                run = (li, run[1], b, w)
            else:
                flush()
                run = (li, a, b, w)
        else:
            flush()
            x, y = centre(a_node)
            vd, dr = via_size(width)
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
            via.SetWidth(MM(vd)); via.SetDrill(MM(dr))
            via.SetNet(netobj); via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            board.Add(via)
            stats["vias"] += 1
            for li in range(3):
                items[li].add(li, ('via', netname, (x, y, vd / 2), clr),
                              (x - 2, y - 2, x + 2, y + 2))
    flush()

# ---------------- full-board route (gen_pcb entry) ----------------

def route6(board, net_objs, fps, checkpoint=None):
    items = {l: Items() for l in range(3)}
    pad_cells = {}
    for ref, fp in fps.items():
        rot = math.radians(fp.GetOrientationDegrees())
        for pad in fp.Pads():
            net = pad.GetNetname()
            pos = pcbnew.ToMM(pad.GetPosition())
            size = pcbnew.ToMM(pad.GetSize())
            layers = [li for li, lname in enumerate(LAYERS)
                      if pad.IsOnLayer(lname)]
            clr = netclass(net)[1] if net else 0.2
            bhw = max(size) / 2 + 1.8
            for li in layers:
                items[li].add(li, ('pad', net,
                                   (pos[0], pos[1], size[0] / 2, size[1] / 2,
                                    rot + math.radians(
                                        pad.GetOrientationDegrees())), clr),
                              (pos[0] - bhw, pos[1] - bhw,
                               pos[0] + bhw, pos[1] + bhw))
            if net:
                cx, cy = cell_of(pos[0], pos[1])
                pad_cells.setdefault(net, []).append(
                    (f"{ref}.{pad.GetNumber()}",
                     [(li, cx, cy) for li in layers], (pos[0], pos[1])))
    stats = {"routed": [], "failed": [], "vias": 0, "gnd_vias": 0}
    def spread(net):
        pts = [p[2] for p in pad_cells[net]]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        return (max(xs) - min(xs)) + (max(ys) - min(ys))
    def order_class(n):
        if n in HV_NETS: return 0
        if n in POWER_NETS: return 1
        if n in PROMOTE: return 2
        if n in LVDS_NETS: return 3
        return 4
    order = sorted((n for n in pad_cells if n != "GND"),
                   key=lambda n: (order_class(n), spread(n)))
    t_start = time.time()
    trees = {}
    failed = []
    for idx, netname in enumerate(order):
        width, clr = netclass(netname)
        print(f"[{idx + 1}/{len(order)}] {netname} "
              f"({len(pad_cells[netname])} pins) "
              f"t={time.time() - t_start:.0f}s", flush=True)
        pins = pad_cells[netname]
        tree = set()
        for li, cx, cy in pins[0][1]:
            tree.add((li, cx, cy))
        trees[netname] = tree
        ok = True
        neck_pts = [p[2] for p in pins]
        anchors = {}
        for _, cs, pos in pins:
            for c in cs:
                anchors[c] = pos
        for pin_id, cells, _ in pins[1:]:
            path = astar6(items, cells, tree, netname, width, clr,
                          neck_pts=neck_pts, anchors=anchors)
            if path is None:
                ok = False
                failed.append((netname, pin_id, cells))
                continue
            st = {"vias": 0, "neck_pts": neck_pts, "anchors": anchors}
            emit6(board, net_objs[netname], path, width, items,
                  netname, clr, st)
            stats["vias"] += st["vias"]
            for node in path:
                tree.add(node)
        if ok:
            stats["routed"].append(netname)
        if checkpoint and (idx + 1) % 10 == 0:
            checkpoint(idx + 1)
    for attempt in range(2):
        if not failed:
            break
        print(f"retry pass {attempt + 1}: {len(failed)} failed pins, "
              f"t={time.time() - t_start:.0f}s", flush=True)
        still = []
        for netname, pin_id, cells in failed:
            width, clr = netclass(netname)
            neck_pts = [p[2] for p in pad_cells[netname]]
            anchors = {}
            for _, cs, pos in pad_cells[netname]:
                for c in cs:
                    anchors[c] = pos
            path = astar6(items, cells, trees[netname], netname,
                          width, clr, cap=2500000, neck_pts=neck_pts,
                          via_cost=6 if attempt == 0 else 3,
                          anchors=anchors)
            if path is None:
                still.append((netname, pin_id, cells))
                continue
            st = {"vias": 0, "neck_pts": neck_pts, "anchors": anchors}
            emit6(board, net_objs[netname], path, width, items,
                  netname, clr, st)
            stats["vias"] += st["vias"]
            for node in path:
                trees[netname].add(node)
        failed = still
        if checkpoint:
            checkpoint(-(attempt + 1))
    stats["failed"] = [(n, p) for (n, p, _) in failed]
    # GND stitch vias for SMD GND pads — same exact via test as
    # signal vias (v5 used an ad-hoc point test here).
    gnd_clr = netclass("GND")[1]
    for ref, fp in fps.items():
        for pad in fp.Pads():
            if pad.GetNetname() != "GND" or \
               pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            pos = pcbnew.ToMM(pad.GetPosition())
            fpos = pcbnew.ToMM(fp.GetPosition())
            dx, dy = pos[0] - fpos[0], pos[1] - fpos[1]
            L = math.hypot(dx, dy) or 1.0
            dx, dy = dx / L, dy / L
            for dist, dang in [(1.1, 0), (1.1, 45), (1.1, -45),
                               (1.6, 0), (1.6, 90), (1.6, -90)]:
                a = math.radians(dang)
                vx = pos[0] + (dx * math.cos(a) - dy * math.sin(a)) * dist
                vy = pos[1] + (dx * math.sin(a) + dy * math.cos(a)) * dist
                if not (0.8 < vx < 99.2 and 0.8 < vy < 79.2):
                    continue
                if via_margin(items, "GND", gnd_clr, vx, vy, 0.3) >= SAFE:
                    via = pcbnew.PCB_VIA(board)
                    via.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy)))
                    via.SetWidth(MM(0.6)); via.SetDrill(MM(0.3))
                    via.SetNet(net_objs["GND"])
                    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                    board.Add(via)
                    stats["gnd_vias"] += 1
                    for li in range(3):
                        items[li].add(li, ('via', "GND", (vx, vy, 0.3),
                                           gnd_clr),
                                      (vx - 2, vy - 2, vx + 2, vy + 2))
                    break
    print(f"router6: {len(stats['routed'])} nets routed, "
          f"{len(stats['failed'])} pin connections failed, "
          f"{stats['vias']} signal vias, {stats['gnd_vias']} gnd vias")
    for f in stats["failed"]:
        print("  FAILED:", f)
    return stats
