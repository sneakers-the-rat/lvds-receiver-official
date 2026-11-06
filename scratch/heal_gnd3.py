import sys, time
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair
import router6
from router import netclass
from repairg import save_checkpoint

board_path, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(board_path)
items, pad_cells = repair.build_items(board)

# which GND pads touch F or B fill (KiCad Contains, holes accounted)?
polys = {}
for z in board.Zones():
    if z.GetNetname() != 'GND': continue
    for l in (pcbnew.F_Cu, pcbnew.B_Cu):
        if z.IsOnLayer(l): polys[l] = z.GetFilledPolysList(l)
FM = pcbnew.FromMM
def touches_fill(desc):
    for _, cs_list, pos in pad_cells.get('GND', []):
        pass
    return None
connected_descs = set()
for name, cs_list, pos in pad_cells.get('GND', []):
    pt = pcbnew.VECTOR2I(FM(pos[0]), FM(pos[1]))
    if any(p.Contains(pt) for p in polys.values()):
        connected_descs.add(name)

groups = repair.compute_groups(board)['GND']
def descs(g): return {it.desc for it in g if it.kind == 'pad'}
goal = set()
target_groups = []
for g in groups:
    ds = descs(g)
    if ds & {'U10.5', 'C29.2'}:
        target_groups.append(g)
    elif ds & connected_descs or len(g) > 20:
        for it in g: goal |= it.cells
print('connected pads:', len(connected_descs), 'goal cells:', len(goal),
      'targets:', [descs(g) for g in target_groups])
width, clr = netclass('GND')
neck_pts = [p[2] for p in pad_cells.get('GND', [])]
anchors = {}
for _, cs, pos in pad_cells.get('GND', []):
    for c in cs: anchors[c] = pos
for g in target_groups:
    starts = []
    for it in g: starts += list(it.cells)
    print('healing', descs(g), 'items', len(g), flush=True)
    t0 = time.time()
    rpath, fb, lb = router6.astar6(items, starts, goal, 'GND', width,
                                   clr, cap=4000000, neck_pts=neck_pts,
                                   anchors=anchors)
    print(f'  astar: {"path " + str(len(rpath)) if rpath else None} ({time.time()-t0:.0f}s)', flush=True)
    if rpath:
        st = {'vias': 0, 'neck_pts': neck_pts, 'anchors': anchors,
              'first_bend': fb, 'last_bend': lb}
        router6.emit6(board, board.FindNet('GND'), rpath, width,
                      items, 'GND', clr, st)
        for node in rpath: goal.add(node)
        print('  connected, vias:', st['vias'], flush=True)
save_checkpoint(board, out)
print('saved', out)
