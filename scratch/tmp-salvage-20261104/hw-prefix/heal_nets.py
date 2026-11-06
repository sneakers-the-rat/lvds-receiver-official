#!/usr/bin/env python3
"""Targeted per-net heal: repairg's engine, coordinator's net list.

hw/repairg.py sweeps every net with >1 group in group-count order —
on this board that spends the first ~20 minutes on GND, whose
pour-blind groups are mostly clusters the GND zone fills already
join in the audit's grouping (pass 68: 22 merges + 18 failed
searches bought 1 audit group). This driver runs the identical
machinery (repair.build_items/compute_groups + router6.astar6/
emit6, cap 1.5M as in repairg.py) but only over the nets named on
the command line, in the order given, each net healed to one group
(or logged STILL isolated per group). Checkpoints: save+refill
every 10 connections and at end of run (repair6.save_checkpoint).

GND is excluded unless explicitly named: its audit groups are
defined by zone fills, which this item model does not see.

Run: xvfb-run -a python3 hw/heal_nets.py IN OUT NET [NET...]
"""
import os, sys, time
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
import router6
from router import netclass
from repairg import save_checkpoint


def main():
    board_path, out = sys.argv[1], sys.argv[2]
    nets = sys.argv[3:]
    board = pcbnew.LoadBoard(board_path)
    items, pad_cells = repair.build_items(board)
    total = 0
    t_start = time.time()
    groups_by_net = repair.compute_groups(board)
    for net in nets:
        gs = groups_by_net.get(net)
        if not gs or len(gs) <= 1:
            print(f"{net}: single group already, skipped", flush=True)
            continue
        gs = sorted(gs, key=len, reverse=True)
        main_cells = set()
        for it in gs[0]:
            main_cells |= it.cells
        width, clr = netclass(net)
        neck_pts = [p[2] for p in pad_cells.get(net, [])]
        anchors = {}
        for _, cs, pos in pad_cells.get(net, []):
            for c in cs:
                anchors[c] = pos
        print(f"{net}: {len(gs)} groups, main group {len(gs[0])} items",
              flush=True)
        for g in gs[1:]:
            starts = []
            for it in g:
                if it.kind == "pad":
                    starts += list(it.cells)
            if not starts:
                for it in g:
                    starts += list(it.cells)[:2]
            t0 = time.time()
            rpath, fb, lb = router6.astar6(
                items, starts, main_cells, net, width, clr,
                cap=1500000, neck_pts=neck_pts, anchors=anchors)
            if rpath is None:
                print(f"  {net}: group ({len(g)} items, "
                      f"{[it.desc for it in g[:3]]}) STILL "
                      f"isolated ({time.time() - t0:.0f}s)",
                      flush=True)
                continue
            st = {"vias": 0, "neck_pts": neck_pts,
                  "anchors": anchors, "first_bend": fb,
                  "last_bend": lb}
            router6.emit6(board, board.FindNet(net), rpath, width,
                          items, net, clr, st)
            for node in rpath:
                main_cells.add(node)
            total += 1
            print(f"  {net}: connected group of {len(g)} items "
                  f"({time.time() - t0:.0f}s, {st['vias']} vias)",
                  flush=True)
            if total % 10 == 0:
                save_checkpoint(board, out)
                print(f"  checkpoint: {total} groups, saved",
                      flush=True)
    save_checkpoint(board, out)
    print(f"heal_nets done: {total} groups connected in "
          f"{time.time() - t_start:.0f}s, output {out}", flush=True)


if __name__ == "__main__":
    main()
