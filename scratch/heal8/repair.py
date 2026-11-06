#!/usr/bin/env python3
"""Group-targeted repair pass on a saved board.

The full re-route (gen_pcb.py) is a 15-50 minute lottery; the audit
(hw/check_pcb.py) meanwhile reports per-net copper GROUPS — most
split by a single missing hop. This script loads the saved board,
rebuilds the router's obstacle registry from the EXISTING copper,
finds each net's groups with the same union-find geometry the audit
uses, and routes every isolated group to its net's main group with
router.astar/emit. Zones are refilled afterwards (new copper
invalidates pours; ZONE_FILLER needs the save/reload cycle, see
gen_pcb.py). GND is excluded: it connects through zones + stitch
vias, not tracks.

Run: xvfb-run -a python3 hw/repair.py [board]
"""
import math, sys
sys.path.insert(0, 'hw')
import pcbnew
import router
from router import Items, netclass, cell_of, astar, emit, LAYERS

MM = pcbnew.FromMM
KI_LAYERS = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)


def build_items(board):
    items = {l: Items() for l in range(3)}
    pad_cells = {}
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for ref, fp in fps.items():
        rot = math.radians(fp.GetOrientationDegrees())
        for pad in fp.Pads():
            net = pad.GetNetname()
            pos = pcbnew.ToMM(pad.GetPosition())
            size = pcbnew.ToMM(pad.GetSize())
            layers = [li for li, ln in enumerate(LAYERS)
                      if pad.IsOnLayer(ln)]
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
    for t in board.GetTracks():
        net = t.GetNetname()
        clr = netclass(net)[1] if net else 0.2
        if isinstance(t, pcbnew.PCB_VIA):
            p = pcbnew.ToMM(t.GetPosition())
            try:
                r = pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)) / 2
            except Exception:
                r = pcbnew.ToMM(t.GetWidth()) / 2
            for li in range(3):
                items[li].add(li, ('via', net, (p[0], p[1], r), clr),
                              (p[0] - r - 2, p[1] - r - 2,
                               p[0] + r + 2, p[1] + r + 2))
        else:
            if t.GetLayer() not in LAYERS:
                # Copper on a layer the 3-layer routing grid does
                # not model (In1.Cu -- first used by the hand-placed
                # hauls of passes 116-117). It is not an obstacle on
                # any routed layer, so skip it here; compute_groups
                # still accounts its connectivity (below). Crashing
                # here (ValueError: 1 is not in list) killed every
                # heal run on post-116 boards.
                continue
            li = LAYERS.index(t.GetLayer())
            a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
            w = pcbnew.ToMM(t.GetWidth())
            items[li].add(li, ('seg', net, (a[0], a[1], b[0], b[1], w / 2),
                               clr),
                          (min(a[0], b[0]) - 2, min(a[1], b[1]) - 2,
                           max(a[0], b[0]) + 2, max(a[1], b[1]) + 2))
    return items, pad_cells


class AItem:
    __slots__ = ("kind", "net", "layers", "shape", "bbox", "desc", "cells")

    def __init__(self, kind, net, layers, shape, bbox, desc, cells):
        self.kind, self.net, self.layers = kind, net, layers
        self.shape, self.bbox, self.desc, self.cells = shape, bbox, desc, cells


def seg_cells(a, b, li):
    cells = set()
    n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.2))
    for i in range(n + 1):
        x = a[0] + (b[0] - a[0]) * i / n
        y = a[1] + (b[1] - a[1]) * i / n
        cx, cy = cell_of(x, y)
        cells.add((li, cx, cy))
    return cells


def compute_groups(board):
    """Mirror of check_pcb.py's connectivity: union-find over copper
    items touching (Collide 0) on a shared layer, per net."""
    bynet = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            layers = {l for l in KI_LAYERS if pad.IsOnLayer(l)}
            pos = pcbnew.ToMM(pad.GetPosition())
            cells = {(LAYERS.index(l),) + cell_of(pos[0], pos[1])
                     for l in layers if l in LAYERS}
            it = AItem("pad", net, layers, pad.GetEffectiveShape(),
                       pad.GetBoundingBox(),
                       f"{fp.GetReference()}.{pad.GetNumber()}", cells)
            bynet.setdefault(net, []).append(it)
    for t in board.GetTracks():
        net = t.GetNetname()
        if isinstance(t, pcbnew.PCB_VIA):
            layers = set(KI_LAYERS)
            p = pcbnew.ToMM(t.GetPosition())
            cells = {(li,) + cell_of(p[0], p[1]) for li in range(3)}
            kind = "via"
        else:
            layers = {t.GetLayer()}
            a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
            # Unmodelled layers (In1.Cu) take virtual layer index 3:
            # group union is shape-based and unaffected; the cells
            # are bookkeeping only (heal's goal set always also
            # holds the group's routed-layer cells via pads/vias).
            li = LAYERS.index(t.GetLayer()) \
                if t.GetLayer() in LAYERS else 3
            cells = seg_cells(a, b, li)
            kind = "track"
        it = AItem(kind, net, layers, t.GetEffectiveShape(),
                   t.GetBoundingBox(),
                   f"{kind}@{pcbnew.ToMM(t.GetPosition())}", cells)
        bynet.setdefault(net, []).append(it)
    groups_by_net = {}
    for net, idx_items in bynet.items():
        parent = list(range(len(idx_items)))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for i in range(len(idx_items)):
            for j in range(i + 1, len(idx_items)):
                a, b = idx_items[i], idx_items[j]
                if not (a.layers & b.layers):
                    continue
                if not a.bbox.Intersects(b.bbox):
                    continue
                try:
                    hit = a.shape.Collide(b.shape, 0)
                except Exception:
                    hit = True
                if hit:
                    ri, rj = find(i), find(j)
                    if ri != rj:
                        parent[ri] = rj
        groups = {}
        for i, it in enumerate(idx_items):
            groups.setdefault(find(i), []).append(it)
        groups_by_net[net] = list(groups.values())
    return groups_by_net


def main(path="hw/pdlvds_rx.kicad_pcb"):
    # Lockfile (cheap insurance): attempts 1-2 both lost their boards
    # at the save step — attempt 2's post-mortem found the true cause
    # (the A* result variable `path` shadowed the board-path argument,
    # so the save used a route/None; see _main_locked). Concurrency
    # was suspected for attempt 1 but the shadowing explains both.
    import os
    lock = path + ".repair.lock"
    if os.path.exists(lock):
        raise SystemExit(f"repair lock present ({lock}) — another "
                         "repair is running or crashed; remove it "
                         "manually if certain")
    with open(lock, "w") as f:
        f.write(str(os.getpid()))
    try:
        return _main_locked(path)
    finally:
        os.unlink(lock)


def _main_locked(board_path):
    board = pcbnew.LoadBoard(board_path)
    out = board_path.replace(".kicad_pcb", ".repaired.kicad_pcb")
    items, pad_cells = build_items(board)
    net_objs = {}

    def net_obj(name):
        if name not in net_objs:
            net_objs[name] = board.FindNet(name)
        return net_objs[name]
    total = 0
    for sweep in range(2):
        groups_by_net = compute_groups(board)
        todo = [(net, gs) for net, gs in groups_by_net.items()
                if len(gs) > 1 and net != "GND"]
        if not todo:
            print("all nets single-group")
            break
        print(f"sweep {sweep + 1}: {len(todo)} nets with >1 group",
              flush=True)
        progressed = False
        for net, gs in sorted(todo, key=lambda kv: -len(kv[1])):
            gs.sort(key=len, reverse=True)
            main_cells = set()
            for it in gs[0]:
                main_cells |= it.cells
            width, clr = netclass(net)
            neck_pts = [p[2] for p in pad_cells.get(net, [])]
            own_cells = frozenset(c for _, cs, _ in pad_cells.get(net, [])
                                  for c in cs)
            for g in gs[1:]:
                starts = []
                for it in g:
                    if it.kind == "pad":
                        starts += list(it.cells)
                if not starts:
                    for it in g:
                        starts += list(it.cells)[:2]
                rpath = astar(items, starts, main_cells, net, width / 2,
                              clr, cap=1500000, neck_pts=neck_pts,
                              own_cells=own_cells)
                if rpath is None:
                    print(f"  {net}: group ({len(g)} items, "
                          f"{[it.desc for it in g[:3]]}) STILL isolated",
                          flush=True)
                    continue
                stats = {"vias": 0}
                emit(board, net_obj(net), rpath, width, items, net, clr,
                     stats)
                for node in rpath:
                    main_cells.add(node)
                total += 1
                progressed = True
                print(f"  {net}: connected group of {len(g)} items",
                      flush=True)
                if total % 10 == 0:
                    # Fine checkpoint: VM replacements kill long runs
                    # without warning (four on 2026-11-03); losing at
                    # most 10 connections beats losing a whole sweep.
                    board.Save(out)
                    print(f"  checkpoint: {total} groups, saved",
                          flush=True)
        # Checkpoint after every sweep: a late crash must not be able
        # to take earlier sweeps' connections with it (attempts 1-2
        # each lost a full run at the final save).
        board.Save(out)
        print(f"checkpoint saved after sweep {sweep + 1}: {out}",
              flush=True)
        if not progressed:
            print("no progress this sweep — stopping")
            break
    n_tracks_before = len(list(board.GetTracks()))
    board.Save(out)
    # Verify the save actually landed before trusting it (attempt 1
    # printed 'saved' while the file on disk stayed the input board).
    import os
    chk = pcbnew.LoadBoard(out)
    n_tracks_after = len(list(chk.GetTracks()))
    print(f"saved {out}: {os.path.getsize(out)} bytes, tracks "
          f"{n_tracks_before} (expect >= input count)", flush=True)
    if n_tracks_after < n_tracks_before:
        raise SystemExit("save verification failed — output has "
                         "fewer tracks than the in-memory board")
    board = chk
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(out)
    print(f"repair done: {total} groups connected, zones refilled, "
          f"output {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "hw/pdlvds_rx.kicad_pcb")
