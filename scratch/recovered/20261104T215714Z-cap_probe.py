import sys, time
sys.path.insert(0, 'hw')
import wx
_a = wx.App(False)
import pcbnew
import repair, repair6, router6
from repair6 import netclass

board = pcbnew.LoadBoard(sys.argv[2])
items, pad_cells = repair.build_items(board)
groups = repair.compute_groups(board)
net = sys.argv[1]
gs = groups[net]
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
for gi, g in enumerate(gs[1:], 1):
    starts = []
    for it in g:
        if it.kind == 'pad':
            starts += list(it.cells)
    if not starts:
        for it in g:
            starts += list(it.cells)[:2]
    print(f'{net} group {gi}: descs {[it.desc for it in g[:3]]}, '
          f'starts {len(starts)}', flush=True)
    t0 = time.time()
    r, fb, lb = router6.astar6(items, starts, main_cells, net,
                               width, clr, cap=1500000,
                               neck_pts=neck_pts, anchors=anchors)
    print(f'  {"FOUND len=" + str(len(r)) if r else "None"} '
          f'in {time.time() - t0:.0f}s', flush=True)
