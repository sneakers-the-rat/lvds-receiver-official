#!/usr/bin/env python3
"""Grid A* router for the scripted PCB build.

Layers used: F.Cu, In2.Cu, B.Cu (In1.Cu is the solid GND plane).
Cell 0.25 mm. Obstacles are the real pad/track/via geometries kept in
2 mm spatial buckets; a cell is blocked when the routed track (with its
netclass width + clearance) would come too close to another net's
copper. Multi-pin nets are routed pin-to-tree. This is a pragmatic
scripted router, not a production autorouter: failures are reported,
never silently dropped.
"""
import heapq, math
import pcbnew

CELL = 0.25
W, H = 400, 320            # 100 x 80 mm
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
MM = pcbnew.FromMM

HV_NETS = {"APD_K", "HV_RAW", "HV_SEC"}
POWER_NETS = {"+5V", "+3V3D", "+3V3D_CDR", "+3V3A", "+VA", "-VA",
              "NEG_RAW", "VBUS_RAW", "PHY_1V8", "PHY_1V8A"}
LVDS_NETS = {"CDR_DATP", "CDR_DATN", "CDR_CLKP", "CDR_CLKN",
             "CMP_QP", "CMP_QN"}

def netclass(name):
    if name in HV_NETS: return (0.40, 1.00)
    if name in POWER_NETS: return (0.60, 0.25)
    if name in LVDS_NETS: return (0.30, 0.20)
    return (0.25, 0.20)

def cell_of(x_mm, y_mm):
    return (min(W - 1, max(0, int(x_mm / CELL))), min(H - 1, max(0, int(y_mm / CELL))))

class Items:
    """Copper geometry registry with buckets. Item: (kind, net, data)
    kind 'pad': data=(cx,cy,hw,hh,rot_rad) OBB; 'seg': (x1,y1,x2,y2,hw);
    'via': (cx,cy,r). Each item also stores its clearance demand."""
    def __init__(self):
        self.buckets = {}
    def _keys(self, x1, y1, x2, y2):
        for bx in range(int(x1 // 2), int(x2 // 2) + 1):
            for by in range(int(y1 // 2), int(y2 // 2) + 1):
                yield (bx, by)
    def add(self, layer, item, bbox):
        for k in self._keys(*bbox):
            self.buckets.setdefault((layer,) + k, []).append(item)
    def near(self, layer, x, y):
        bx, by = int(x // 2), int(y // 2)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                yield from self.buckets.get((layer, bx + dx, by + dy), ())

def dist_to_item(item, x, y):
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
        px, py = x - x1, y - y1; dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, (px * dx + py * dy) / L2))
        return math.hypot(px - t * dx, py - t * dy) - hw
    (cx, cy, r) = item[2]  # via
    return math.hypot(x - cx, y - cy) - r

def route(board, net_objs, fps):
    items = {l: Items() for l in range(3)}
    pad_cells = {}   # netname -> list of (pin_id, [(layer, cx, cy), ...])
    for ref, fp in fps.items():
        rot = math.radians(fp.GetOrientationDegrees())
        for pad in fp.Pads():
            net = pad.GetNetname()
            pos = pcbnew.ToMM(pad.GetPosition())
            size = pcbnew.ToMM(pad.GetSize())
            layers = []
            for li, lname in enumerate(LAYERS):
                if pad.IsOnLayer(lname):
                    layers.append(li)
            item = ('pad', net, (pos[0], pos[1], size[0] / 2, size[1] / 2,
                                 rot + math.radians(pad.GetOrientationDegrees())))
            clr = netclass(net)[1] if net else 0.2
            item = ('pad', net, item[2], clr)
            pad_hw = max(size) / 2 + 1.8
            for li in layers:
                items[li].add(li, ('pad', net, (pos[0], pos[1], size[0]/2, size[1]/2,
                                                rot + math.radians(pad.GetOrientationDegrees())), clr),
                              (pos[0] - pad_hw, pos[1] - pad_hw, pos[0] + pad_hw, pos[1] + pad_hw))
            if net:
                cx, cy = cell_of(pos[0], pos[1])
                pad_cells.setdefault(net, []).append((f"{ref}.{pad.GetNumber()}",
                                                      [(li, cx, cy) for li in layers],
                                                      (pos[0], pos[1])))
    stats = {"routed": [], "failed": [], "vias": 0, "gnd_vias": 0}
    # order: HV first, then by ascending pad spread
    def spread(net):
        pts = [p[2] for p in pad_cells[net]]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        return (max(xs) - min(xs)) + (max(ys) - min(ys))
    order = sorted((n for n in pad_cells if n != "GND"),
                   key=lambda n: (0 if n in HV_NETS else 1, spread(n)))
    import time
    t_start = time.time()
    for idx, netname in enumerate(order):
        width, clr = netclass(netname)
        hw_ = width / 2
        print(f"[{idx + 1}/{len(order)}] {netname} "
              f"({len(pad_cells[netname])} pins) "
              f"t={time.time() - t_start:.0f}s", flush=True)
        pins = pad_cells[netname]
        tree = set()
        for li, cx, cy in pins[0][1]:
            tree.add((li, cx, cy))
        ok = True
        for pin_id, cells, _ in pins[1:]:
            path = astar(items, cells, tree, netname, hw_, clr)
            if path is None:
                ok = False
                stats["failed"].append((netname, pin_id))
                continue
            emit(board, net_objs[netname], path, width, items, netname, clr, stats)
            for node in path:
                tree.add(node)
        if ok: stats["routed"].append(netname)
    # GND vias for SMD GND pads (reach the In1 plane)
    for ref, fp in fps.items():
        for pad in fp.Pads():
            if pad.GetNetname() != "GND" or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            pos = pcbnew.ToMM(pad.GetPosition())
            fpos = pcbnew.ToMM(fp.GetPosition())
            dx, dy = pos[0] - fpos[0], pos[1] - fpos[1]
            L = math.hypot(dx, dy) or 1.0
            dx, dy = dx / L, dy / L
            for dist, dang in [(1.1, 0), (1.1, 45), (1.1, -45), (1.6, 0), (1.6, 90), (1.6, -90)]:
                a = math.radians(dang)
                vx = pos[0] + (dx * math.cos(a) - dy * math.sin(a)) * dist
                vy = pos[1] + (dx * math.sin(a) + dy * math.cos(a)) * dist
                if not (0.8 < vx < 99.2 and 0.8 < vy < 79.2):
                    continue
                if all(dist_to_item(it, vx, vy) >= it[3] + 0.3 + 0.2
                       for li in range(3) for it in items[li].near(li, vx, vy)
                       if it[1] != "GND"):
                    via = pcbnew.PCB_VIA(board)
                    via.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy)))
                    via.SetWidth(MM(0.6)); via.SetDrill(MM(0.3))
                    via.SetNet(net_objs["GND"])
                    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                    board.Add(via)
                    stats["gnd_vias"] += 1
                    for li in range(3):
                        items[li].add(li, ('via', "GND", (vx, vy, 0.3), 0.2),
                                      (vx - 2, vy - 2, vx + 2, vy + 2))
                    break
    print(f"router: {len(stats['routed'])} nets routed, "
          f"{len(stats['failed'])} pin connections failed, "
          f"{stats['vias']} signal vias, {stats['gnd_vias']} gnd vias")
    for f in stats["failed"]:
        print("  FAILED:", f)
    return stats

def astar(items, starts, goals, netname, hw_, clr):
    goalset = set(goals)
    openh = []
    gscore = {}
    came = {}
    for (li, cx, cy) in starts:
        gscore[(li, cx, cy)] = 0
        heapq.heappush(openh, (0, (li, cx, cy)))
    def h(node):
        li, cx, cy = node
        return min(abs(cx - gx) + abs(cy - gy) for (_, gx, gy) in goalset)
    visited = 0
    while openh:
        _, node = heapq.heappop(openh)
        if node in goalset and gscore[node] > 0 or (node in goalset and any(s != node for s in starts)):
            path = [node]
            while node in came:
                node = came[node]; path.append(node)
            return list(reversed(path))
        visited += 1
        if visited > 260000:
            return None
        li, cx, cy = node
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            nb = (li, nx, ny)
            if nb in gscore and gscore[nb] <= gscore[node] + 1:
                continue
            wx_, wy_ = (nx + 0.5) * CELL, (ny + 0.5) * CELL
            if blocked(items, li, wx_, wy_, netname, hw_, clr):
                continue
            gscore[nb] = gscore[node] + 1; came[nb] = node
            heapq.heappush(openh, (gscore[nb] + h(nb), nb))
        for lj in range(3):
            if lj == li: continue
            nb = (lj, cx, cy)
            if nb in gscore and gscore[nb] <= gscore[node] + 6:
                continue
            wx_, wy_ = (cx + 0.5) * CELL, (cy + 0.5) * CELL
            if blocked(items, lj, wx_, wy_, netname, hw_, clr):
                continue
            gscore[nb] = gscore[node] + 6; came[nb] = node
            heapq.heappush(openh, (gscore[nb] + h(nb), nb))
    return None

def blocked(items, li, x, y, netname, hw_, clr):
    for it in items[li].near(li, x, y):
        if it[1] == netname:
            continue
        need = hw_ + max(clr, it[3])
        if dist_to_item(it, x, y) < need:
            return True
    return False

def emit(board, netobj, path, width, items, netname, clr, stats):
    # simplify collinear runs
    pts = []
    for node in path:
        if pts and pts[-1][0] == node[0] and len(pts) >= 2:
            p0, p1 = pts[-2], pts[-1]
            if (p0[1] == p1[1] == node[1]) or (p0[2] == p1[2] == node[2]):
                pts[-1] = node; continue
        pts.append(node)
    for a, b in zip(pts, pts[1:]):
        if a[0] == b[0]:
            x1, y1 = (a[1] + 0.5) * CELL, (a[2] + 0.5) * CELL
            x2, y2 = (b[1] + 0.5) * CELL, (b[2] + 0.5) * CELL
            tr = pcbnew.PCB_TRACK(board)
            tr.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
            tr.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
            tr.SetWidth(MM(width)); tr.SetLayer(LAYERS[a[0]]); tr.SetNet(netobj)
            board.Add(tr)
            items[a[0]].add(a[0], ('seg', netname, (x1, y1, x2, y2, width / 2), clr),
                            (min(x1, x2) - 2, min(y1, y2) - 2, max(x1, x2) + 2, max(y1, y2) + 2))
        else:
            x, y = (a[1] + 0.5) * CELL, (a[2] + 0.5) * CELL
            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
            vd, dr = (0.8, 0.4) if width >= 0.4 else (0.6, 0.3)
            via.SetWidth(MM(vd)); via.SetDrill(MM(dr))
            via.SetNet(netobj); via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            board.Add(via)
            stats["vias"] += 1
            for li in range(3):
                items[li].add(li, ('via', netname, (x, y, vd / 2), clr),
                              (x - 2, y - 2, x + 2, y + 2))
