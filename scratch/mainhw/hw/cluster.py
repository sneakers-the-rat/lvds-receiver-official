#!/usr/bin/env python3
"""Cluster clearing: rip EVERY foreign segment/via inside a disc,
then connect the cluster's target pads through the cleared field.

For QFN pad rows whose escape field is fenced 2-3 segments deep on
every layer (diagnosis POCKET with reach ~10-30 cells): incremental
rip-up restores the fence before the next pad is tried, and ripping
only the nearest few never opens a corridor. Here the whole thicket
inside the disc goes at once (victims are short fanout stubs of
neighbouring nets; they are re-connected afterwards by repair6 in
the same cleared field), each target group is attempted with the
repair machinery, and the clearing STANDS (no restore).

Run: xvfb-run -a python3 hw/cluster.py IN OUT CX CY RADIUS \
    NET:PAD[,PAD...] [NET:PAD...]
e.g. hw/cluster.py b.kicad_pcb o.kicad_pcb 30.5 57.8 3.2 \
    +3V3A:U7.25,U7.30,U7.31 PHY_1V8:U7.26
"""
import sys, time, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
import repair6
from ripup import attempt, snapshot, seg_dist

def main():
    src, out = sys.argv[1], sys.argv[2]
    cx, cy, radius = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
    targets = []          # (net, pad_desc)
    target_nets = set()
    for spec in sys.argv[6:]:
        net, pads = spec.split(':', 1)
        target_nets.add(net)
        for p in pads.split(','):
            targets.append((net, p.strip()))
    board = pcbnew.LoadBoard(src)
    items, pad_cells = repair.build_items(board)
    # --- clear the disc ---
    ripped = []
    for t in list(board.GetTracks()):
        if t.GetNetname() in target_nets:
            continue
        if seg_dist(cx, cy, t) < radius:
            ripped.append(snapshot(t))
            board.Remove(t)
    from collections import Counter
    print(f"cleared {len(ripped)} foreign items in disc "
          f"({cx},{cy}) r={radius}: {dict(Counter(s[1] for s in ripped))}",
          flush=True)
    items, pad_cells = repair.build_items(board)
    groups_by_net = repair.compute_groups(board)
    # --- attempt each target ---
    connected = 0
    for net, desc in targets:
        groups_by_net = repair.compute_groups(board)
        g = None
        for gg in groups_by_net.get(net, []):
            if any(it.desc == desc and it.kind == 'pad' for it in gg):
                g = gg
                break
        if g is None:
            print(f"  {net} {desc}: already in main group", flush=True)
            connected += 1
            continue
        if len(groups_by_net[net]) < 2:
            print(f"  {net} {desc}: net already single-group", flush=True)
            connected += 1
            continue
        t0 = time.time()
        if attempt(board, items, pad_cells, groups_by_net, net, g):
            print(f"  {net} {desc}: CONNECTED "
                  f"({time.time() - t0:.0f}s)", flush=True)
            connected += 1
        else:
            print(f"  {net} {desc}: still isolated "
                  f"({time.time() - t0:.0f}s)", flush=True)
    repair6.save_checkpoint(board, out)
    groups_by_net = repair.compute_groups(board)
    left = sum(len(gs) - 1 for gs in groups_by_net.values() if len(gs) > 1)
    print(f"cluster done: {connected}/{len(targets)} targets connected; "
          f"isolated groups remaining: {left}", flush=True)

if __name__ == "__main__":
    main()
