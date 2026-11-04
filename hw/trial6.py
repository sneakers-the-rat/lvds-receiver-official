#!/usr/bin/env python3
"""Small-scale v6 trial: rip the tracks/vias of the named nets from
a saved board, re-route their audit groups with router6 (exact
model), save to a trial board. Compare with check_pcb.py runs
before/after (pairs involving the ripped nets + totals).

Two phases, one process each — this KiCad 7.0.11 SWIG build
corrupts its container proxies when ~100 Remove() calls happen in a
process that then keeps using the board (bisected 2026-11-03:
GetFootprints() starts returning a dead SwigPyObject; the saved
file itself is fine and a fresh process loads it cleanly). So:

  xvfb-run -a python3 hw/trial6.py rip   IN.kicad_pcb TMP.kicad_pcb NET...
  xvfb-run -a python3 hw/trial6.py route TMP.kicad_pcb OUT.kicad_pcb NET...
"""
import sys, time
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

def rip(in_path, out_path, nets):
    board = pcbnew.LoadBoard(in_path)
    ripped = 0
    for t in list(board.GetTracks()):
        if t.GetNetname() in nets:
            board.Remove(t)
            ripped += 1
    board.Save(out_path)
    print(f"ripped {ripped} tracks/vias of {nets} -> {out_path}",
          flush=True)

def route(in_path, out_path, nets):
    import repair
    import router6
    from router import netclass
    board = pcbnew.LoadBoard(in_path)
    items, pad_cells = repair.build_items(board)
    groups_by_net = repair.compute_groups(board)
    total_conn = 0
    for net in nets:
        gs = groups_by_net.get(net, [])
        print(f"{net}: {len(gs)} groups after rip", flush=True)
        if len(gs) <= 1:
            continue
        gs.sort(key=len, reverse=True)
        main_cells = set()
        for it in gs[0]:
            main_cells |= it.cells
        width, clr = netclass(net)
        neck_pts = [p[2] for p in pad_cells.get(net, [])]
        anchors = {}
        for _, cs, pos in pad_cells.get(net, []):
            for c in cs:
                anchors[c] = pos
        for g in gs[1:]:
            starts = []
            for it in g:
                if it.kind == "pad":
                    starts += list(it.cells)
            if not starts:
                for it in g:
                    starts += list(it.cells)[:2]
            t0 = time.time()
            path = router6.astar6(items, starts, main_cells, net,
                                  width, clr, cap=1500000,
                                  neck_pts=neck_pts, anchors=anchors)
            if path is None:
                print(f"  {net}: group of {len(g)} items STILL "
                      f"isolated ({time.time() - t0:.0f}s)", flush=True)
                continue
            st = {"vias": 0, "neck_pts": neck_pts, "anchors": anchors}
            router6.emit6(board, board.FindNet(net), path, width,
                          items, net, clr, st)
            for node in path:
                main_cells.add(node)
            total_conn += 1
            print(f"  {net}: connected group of {len(g)} items "
                  f"({time.time() - t0:.0f}s, {st['vias']} vias)",
                  flush=True)
    board.Save(out_path)
    print(f"saved {out_path}: {total_conn} groups connected")

if __name__ == "__main__":
    mode, in_path, out_path, nets = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    if mode == "rip":
        rip(in_path, out_path, nets)
    else:
        route(in_path, out_path, nets)
