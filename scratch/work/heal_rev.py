"""Reversed heal: search FROM the U7-side group TO the U6 pad group.

heal_nets always searches from the smallest group (here the lone
U6 west-row pad) toward the main group. Its flood covers 445,790
cells board-wide yet never enters the U7 district ring in the
router model (goal cells all unvisited; district box holds only
114/135/377 visited cells per layer) - the model-sealed ring is
crossed more easily from inside, where the start set already sits
past the choke points. This driver swaps the direction: starts =
all cells of the group containing the U7 pad, goals = cells of the
group containing the named U6 pad; anchors (pad true centres) are
passed for both pads, exactly as heal_nets builds them.

Run: xvfb-run -a python3 scratch/work/heal_rev.py IN OUT NET:U6PAD [NET:U6PAD...]
e.g. ... ULPI_DIR:U6.28 ULPI_NXT:U6.29
"""
import sys, time
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
    specs = [s.split(':') for s in sys.argv[3:]]
    board = pcbnew.LoadBoard(board_path)
    items, pad_cells = repair.build_items(board)
    groups_by_net = repair.compute_groups(board)
    total = 0
    for net, u6pad in specs:
        gs = groups_by_net.get(net)
        if not gs or len(gs) <= 1:
            print(f"{net}: single group already, skipped", flush=True)
            continue
        main = next((g for g in gs if any(it.desc.startswith('U7.') for it in g)), None)
        other = next((g for g in gs if any(it.desc == u6pad for it in g)), None)
        assert main is not None and other is not None, (net, [ [it.desc for it in g] for g in gs])
        starts = set()
        for it in main: starts |= it.cells
        goals = set()
        for it in other: goals |= it.cells
        width, clr = netclass(net)
        neck_pts = [p[2] for p in pad_cells.get(net, [])]
        anchors = {}
        for _, cs, pos in pad_cells.get(net, []):
            for c in cs: anchors[c] = pos
        print(f"{net}: reversed search starts={len(starts)} cells goals={len(goals)} cells", flush=True)
        t0 = time.time()
        rpath, fb, lb = router6.astar6(items, sorted(starts), goals, net,
                                       width, clr, cap=1500000,
                                       neck_pts=neck_pts, anchors=anchors)
        if rpath is None:
            print(f"  {net}: STILL isolated reversed ({time.time()-t0:.0f}s)", flush=True)
            continue
        st = {"vias": 0, "neck_pts": neck_pts, "anchors": anchors,
              "first_bend": fb, "last_bend": lb}
        router6.emit6(board, board.FindNet(net), rpath, width, items, net, clr, st)
        total += 1
        print(f"  {net}: CONNECTED reversed, {len(rpath)} nodes, {st['vias']} vias ({time.time()-t0:.0f}s)", flush=True)
        items, pad_cells = repair.build_items(board)
        groups_by_net = repair.compute_groups(board)
    save_checkpoint(board, out)
    print(f"heal_rev done: {total} groups connected, output {out}", flush=True)

if __name__ == '__main__':
    main()
