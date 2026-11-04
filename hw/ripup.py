#!/usr/bin/env python3
"""Rip-up-and-retry for copper-walled isolated groups.

repair6's A* cannot cross foreign copper, so a pad ringed by other
nets' tracks at clearance distance (diagnosis NO_EXIT / POCKET) can
never connect, however long the search runs. This tool attacks
exactly those groups: for each still-isolated group it finds the
foreign track segments/vias walling its pads (nearest first), removes
up to 3 of them from the board, and retries the group's connection
through the opened corridor (router6.astar6/emit6, the repair
machinery verbatim). On success the deletions stand and the victim
nets gain a new isolated group each — they are re-connected by a
following repair6 run, whose endpoints are open copper fronts rather
than sealed pads. On failure the deleted copper is re-created from
snapshots, byte-for-byte in geometry/net/layer/width.

Batch discipline: at most MAXG groups per invocation (board.Remove
in-process is SWIG-fragile in bulk on KiCad 7.0.11); state persists
in the board file, so re-invoke to continue. Checkpoint save (zones
refilled) every 5 connections and at exit.

Run: xvfb-run -a python3 hw/ripup.py IN.kicad_pcb OUT.kicad_pcb [MAXG]
"""
import os, sys, time, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
import repair6
import router6
from router import netclass

WALL_R = 1.6          # mm: wall candidates within this of a pad centre
MAX_RIP = 3           # segments removed per group at most
CAP = 1_000_000       # astar6 node cap per trial


def pad_positions(pad_cells, net, descs):
    return [pos for desc, _cs, pos in pad_cells.get(net, [])
            if desc in descs]


def seg_dist(px, py, t):
    if isinstance(t, pcbnew.PCB_VIA):
        q = pcbnew.ToMM(t.GetPosition())
        return math.hypot(px - q[0], py - q[1])
    a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vy * vy
    s = 0.0 if L2 == 0 else max(0.0, min(1.0,
        ((px - a[0]) * vx + (py - a[1]) * vy) / L2))
    return math.hypot(px - (a[0] + s * vx), py - (a[1] + s * vy))


def snapshot(t):
    net = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition())
        return ("via", net, p[0], p[1],
                pcbnew.ToMM(t.GetWidth()), pcbnew.ToMM(t.GetDrill()))
    a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
    return ("track", net, t.GetLayer(), a[0], a[1], b[0], b[1],
            pcbnew.ToMM(t.GetWidth()))


def restore(board, snap):
    if snap[0] == "via":
        _k, net, x, y, w, d = snap
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        v.SetWidth(pcbnew.FromMM(w)); v.SetDrill(pcbnew.FromMM(d))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(board.FindNet(net))
        board.Add(v)
    else:
        _k, net, layer, x1, y1, x2, y2, w = snap
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        tr.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
        tr.SetWidth(pcbnew.FromMM(w)); tr.SetLayer(layer)
        tr.SetNet(board.FindNet(net))
        board.Add(tr)


def attempt(board, items, pad_cells, groups_by_net, net, g):
    gs = sorted(groups_by_net[net], key=len, reverse=True)
    main_cells = set()
    for it in gs[0]:
        main_cells |= it.cells
    width, clr = netclass(net)
    neck_pts = [p[2] for p in pad_cells.get(net, [])]
    anchors = {}
    for _d, cs, pos in pad_cells.get(net, []):
        for c in cs:
            anchors[c] = pos
    starts = []
    for it in g:
        if it.kind == "pad":
            starts += list(it.cells)
    if not starts:
        for it in g:
            starts += list(it.cells)[:2]
    rpath, fb, lb = router6.astar6(items, starts, main_cells, net,
                                   width, clr, cap=CAP,
                                   neck_pts=neck_pts, anchors=anchors)
    if rpath is None:
        return False
    st = {"vias": 0, "neck_pts": neck_pts, "anchors": anchors,
          "first_bend": fb, "last_bend": lb}
    router6.emit6(board, board.FindNet(net), rpath, width, items,
                  net, clr, st)
    return True


def main():
    src, out = sys.argv[1], sys.argv[2]
    maxg = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    mode = sys.argv[4] if len(sys.argv) > 4 else "inc"
    wall_r = 2.0 if mode == "all" else WALL_R
    max_rip = 12 if mode == "all" else MAX_RIP
    board = pcbnew.LoadBoard(src)
    items, pad_cells = repair.build_items(board)
    groups_by_net = repair.compute_groups(board)
    # target groups: non-main groups of multi-group nets (not GND),
    # single-pad groups first (the sealed pads of the census)
    targets = []
    for net, gs in groups_by_net.items():
        if net == "GND" or len(gs) < 2:
            continue
        main = max(gs, key=len)
        for g in gs:
            if g is main:
                continue
            npads = sum(1 for it in g if it.kind == "pad")
            targets.append((npads, net, g))
    targets.sort(key=lambda x: (x[0] == 0, x[0] if x[0] else 99, x[1]))
    print(f"ripup: {len(targets)} isolated groups, batch of "
          f"{min(maxg, len(targets))}", flush=True)
    connected = 0
    victims = set()
    tried = 0
    for _np, net, g in targets:
        if tried >= maxg:
            break
        tried += 1
        descs = [it.desc for it in g if it.kind == "pad"]
        label = f"{net} {descs[:2]}"
        # wall candidates from the live board
        pos = pad_positions(pad_cells, net, set(descs))
        if not pos:
            print(f"  {label}: no pad positions, skipped", flush=True)
            continue
        cands = []
        for t in board.GetTracks():
            if t.GetNetname() == net:
                continue
            d = min(seg_dist(px, py, t) for px, py in pos)
            if d < wall_r:
                cands.append((d, t))
        cands.sort(key=lambda x: x[0])
        if not cands:
            print(f"  {label}: no wall candidates within {wall_r} mm",
                  flush=True)
            continue
        removed = []
        ok = False
        # 'inc': add one candidate per trial, attempt after each.
        # 'all': remove the whole fence (up to max_rip) in one trial.
        steps = ([min(max_rip, len(cands))] if mode == "all"
                 else list(range(1, min(max_rip, len(cands)) + 1)))
        for upto in steps:
            while len(removed) < upto:
                _d, t = cands[len(removed)]
                removed.append(snapshot(t))
                victims.add(t.GetNetname())
                board.Remove(t)
                print(f"    rip {t.GetNetname()} "
                      f"{'via' if isinstance(t, pcbnew.PCB_VIA) else t.GetLayerName()} "
                      f"d={_d:.2f}", flush=True)
            items, _pc = repair.build_items(board)
            groups_by_net = repair.compute_groups(board)
            # the group object is stale after recompute; re-find it
            gnow = None
            for gg in groups_by_net[net]:
                if any(it.desc in descs and it.kind == "pad"
                       for it in gg):
                    gnow = gg
                    break
            if gnow is None:
                ok = True   # group already merged by the deletion
                break
            t0 = time.time()
            if attempt(board, items, pad_cells, groups_by_net,
                       net, gnow):
                print(f"  {label}: CONNECTED after ripping "
                      f"{len(removed)} ({time.time() - t0:.0f}s); "
                      f"victims: {[s[1] for s in removed]}",
                      flush=True)
                ok = True
                connected += 1
                break
        if not ok:
            for snap in removed:
                restore(board, snap)
            victims -= {s[1] for s in removed}
            items, _pc = repair.build_items(board)
            groups_by_net = repair.compute_groups(board)
            print(f"  {label}: still isolated after "
                  f"{len(removed)} rips; copper restored", flush=True)
        if connected and connected % 5 == 0:
            repair6.save_checkpoint(board, out)
            print(f"  checkpoint: {connected} ripup connections",
                  flush=True)
    repair6.save_checkpoint(board, out)
    groups_by_net = repair.compute_groups(board)
    left = sum(len(gs) - 1 for net, gs in groups_by_net.items()
               if len(gs) > 1)
    print(f"ripup done: {connected} groups connected, victims "
          f"{sorted(victims)}, isolated groups remaining: {left}",
          flush=True)


if __name__ == "__main__":
    main()
