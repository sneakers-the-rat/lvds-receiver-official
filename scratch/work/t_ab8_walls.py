"""t_ab8: full item dump + group census for the wall nets.

Usage: t_ab8_walls.py BOARD NET [NET...]
Prints every track/via/pad of each net (whole board) and the
net's copper groups (union-find over items+pads, contact =
dist <= 0.05 on a shared layer; vias join all layers).
"""
import math, sys
sys.path.insert(0, 'hw')
import pcbnew
import repair, router
from router import dist_to_item

board = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.ToMM
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
      pcbnew.B_Cu: 'B'}
targets = set(sys.argv[2:])

for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref in ('J1', 'X1', 'X2'):
        p = MM(fp.GetPosition())
        print(f'FOOTPRINT {ref} at ({p[0]:.2f},{p[1]:.2f}) '
              f'rot={fp.GetOrientationDegrees():.0f}')
    for pad in fp.Pads():
        if pad.GetNetname() in targets:
            p = MM(pad.GetPosition()); s = MM(pad.GetSize())
            print(f'PAD {ref}.{pad.GetNumber()} {pad.GetNetname()} '
                  f'c=({p[0]:.3f},{p[1]:.3f}) size=({s[0]:.2f}x{s[1]:.2f})')

items, pad_cells = repair.build_items(board)
for net in targets:
    print(f'===== {net}')
    for t in board.GetTracks():
        if t.GetNetname() != net:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            p = MM(t.GetPosition())
            print(f'  VIA c=({p[0]:.3f},{p[1]:.3f}) d={MM(t.GetWidth()):.2f}')
        else:
            a = MM(t.GetStart()); e = MM(t.GetEnd())
            print(f'  SEG {LN[t.GetLayer()]} w={MM(t.GetWidth()):.2f} '
                  f'({a[0]:.3f},{a[1]:.3f})->({e[0]:.3f},{e[1]:.3f})')
    # groups via pad_cells + track contact: reuse repair.compute_groups?
    try:
        groups = repair.compute_groups(board, items, pad_cells)
        mine = groups.get(net, [])
        print(f'  GROUPS: {len(mine)}')
        for gi, g in enumerate(mine):
            print(f'   g{gi}: pads={g}')
    except Exception as ex:
        print('  compute_groups failed:', ex)
