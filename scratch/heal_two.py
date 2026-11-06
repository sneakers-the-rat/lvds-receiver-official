import os, sys, time
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair
import router6
from router import netclass
from repairg import save_checkpoint

# like heal_nets, but only the groups containing a named pad get
# healed (GND's other ~130 copper groups are pour-connected and
# must NOT be track-merged).
board_path, out = sys.argv[1], sys.argv[2]
want = set(sys.argv[3:])  # pad descs like U10.5
board = pcbnew.LoadBoard(board_path)
items, pad_cells = repair.build_items(board)
groups = repair.compute_groups(board)['GND']
def descs(g): return {it.desc for it in g if it.kind == 'pad'}
main = max(groups, key=len)
main_cells = set()
for it in main: main_cells |= it.cells
print('main GND group items:', len(main))
width, clr = netclass('GND')
neck_pts = [p[2] for p in pad_cells.get('GND', [])]
anchors = {}
for _, cs, pos in pad_cells.get('GND', []):
    for c in cs: anchors[c] = pos
for g in groups:
    if g is main or not (descs(g) & want):
        continue
    starts = []
    for it in g:
        if it.kind == 'pad': starts += list(it.cells)
    if not starts:
        for it in g: starts += list(it.cells)[:2]
    print('healing group', descs(g), 'starts', len(starts), flush=True)
    rpath, fb, lb = router6.astar6(items, starts, main_cells, 'GND',
                                   width, clr, cap=1500000,
                                   neck_pts=neck_pts, anchors=anchors)
    print('  astar:', 'path' if rpath else None, flush=True)
    if rpath:
        st = {'vias': 0, 'neck_pts': neck_pts, 'anchors': anchors,
              'first_bend': fb, 'last_bend': lb}
        router6.emit6(board, board.FindNet('GND'), rpath, width,
                      items, 'GND', clr, st)
        for node in rpath: main_cells.add(node)
        print('  connected, vias:', st['vias'], flush=True)
save_checkpoint(board, out)
print('saved', out)
