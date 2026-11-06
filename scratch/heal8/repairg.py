#!/usr/bin/env python3
"""Group-targeted repair pass with the v6 exact clearance model.

Same strategy as hw/repair.py (route every isolated copper group to
its net's main group, using the audit's own union-find grouping),
but all searches/emissions go through router6.astar6/emit6, so new
copper is exact-tested against everything on the board, anchors
(true pad centres) included. Finishes partial boards from any
source: v6 checkpoints, interrupted runs, or the v5 board (whose
pre-existing violations it does not add to — ripping those is a
separate decision driven by the audit).

Checkpoint discipline inherited from the repair.py saga: lockfile,
output path computed before the sweeps, save after every sweep and
every 10 connections, save verified by reload + track count, zones
refilled at the end.

Run: xvfb-run -a python3 hw/repair6.py [board] [out]
     (defaults: hw/pdlvds_rx.kicad_pcb -> .repaired6.kicad_pcb)
"""
import os, sys, time
sys.path.insert(0, 'hw')
import pcbnew
import repair
import router6
from router import netclass

# NOTE (verified 2026-11-04): repair.build_items / compute_groups
# key layers by router.LAYERS = [F_Cu, In2_Cu, B_Cu] — the same
# indices router6 uses (F=0, In2=1, B=2). A duplicate re-keyed
# builder pair was briefly added here under a misdiagnosis (the
# audit-repair6-attempt1 spike was stale zone fills on a killed
# run's checkpoint, not layer keys) and removed; the originals are
# correct and are what this file uses.


def main(board_path="hw/pdlvds_rx.kicad_pcb", out=None):
    if out is None:
        out = board_path.replace(".kicad_pcb", ".repaired6.kicad_pcb")
    lock = board_path + ".repair6.lock"
    if os.path.exists(lock):
        raise SystemExit(f"repair6 lock present ({lock}) — another "
                         "run is active or crashed; remove manually "
                         "if certain")
    with open(lock, "w") as f:
        f.write(str(os.getpid()))
    try:
        return _run(board_path, out)
    finally:
        os.unlink(lock)


def save_checkpoint(board, out):
    """Save with zones refilled, so every checkpoint state audits
    comparably (user pass discipline, 2026-11-04: each checkpoint
    is committed with a fresh audit; without a refill the audit
    counts the input board's stale pours against new copper —
    pass 14 read 1,435 violations where the refilled number is
    ~64). The refill runs on a reloaded copy via the save/reload
    cycle; the in-memory working board is untouched (routing
    ignores zones). Costs ~30 s per checkpoint on this board."""
    board.Save(out)
    chk = pcbnew.LoadBoard(out)
    filler = pcbnew.ZONE_FILLER(chk)
    filler.Fill(chk.Zones())
    chk.Save(out)

def _run(board_path, out):
    board = pcbnew.LoadBoard(board_path)
    items, pad_cells = repair.build_items(board)
    total = 0
    t_start = time.time()
    for sweep in range(3):
        groups_by_net = repair.compute_groups(board)
        todo = [(net, gs) for net, gs in groups_by_net.items()
                if len(gs) > 1 ]
        if not todo:
            print("all nets single-group", flush=True)
            break
        print(f"sweep {sweep + 1}: {len(todo)} nets with >1 group, "
              f"t={time.time() - t_start:.0f}s", flush=True)
        progressed = False
        for net, gs in sorted(todo, key=lambda kv: -len(kv[1])):
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
                progressed = True
                print(f"  {net}: connected group of {len(g)} items "
                      f"({time.time() - t0:.0f}s, {st['vias']} vias)",
                      flush=True)
                if total % 10 == 0:
                    save_checkpoint(board, out)
                    print(f"  checkpoint: {total} groups, saved",
                          flush=True)
        save_checkpoint(board, out)
        print(f"checkpoint saved after sweep {sweep + 1}: {out}",
              flush=True)
        if not progressed:
            print("no progress this sweep — stopping", flush=True)
            break
    n_tracks = len(list(board.GetTracks()))
    board.Save(out)
    chk = pcbnew.LoadBoard(out)
    n_after = len(list(chk.GetTracks()))
    print(f"saved {out}: {os.path.getsize(out)} bytes, tracks "
          f"{n_after} (in-memory {n_tracks})", flush=True)
    if n_after < n_tracks:
        raise SystemExit("save verification failed")
    board = chk
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(out)
    print(f"repair6 done: {total} groups connected, zones refilled, "
          f"output {out}", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
