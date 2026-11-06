import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
board = pcbnew.LoadBoard('scratch/exp182cand.kicad_pcb')
items, pad_cells = repair.build_items(board)
for pt in ((21.5, -2.25), (21.625, -2.5), (21.5, -1.75), (21.75, -3.0), (22.25, -2.75)):
    print(pt)
    for li, ln in ((0, 'F'), (1, 'In2'), (2, 'B')):
        for it in items[li].near(li, *pt):
            if it[1] == 'GND': continue
            clr = max(netclass('GND')[1], netclass(it[1])[1]) + 0.05
            d = router.dist_to_item(it, *pt)
            if d < 0.3 + clr: print(f'   {ln}: {it[1]}({it[0]}) d={d:.2f} need={0.3 + clr:.2f}')
print('pads near the well:')
for fp in board.GetFootprints():
    for pad in fp.Pads():
        p = pcbnew.ToMM(pad.GetPosition())
        if 19 < p[0] < 25 and -5 < p[1] < 1:
            s = pcbnew.ToMM(pad.GetSize())
            print(f'   {fp.GetReference()}.{pad.GetNumber()} [{pad.GetNetname()}] @({p[0]:.2f},{p[1]:.2f}) size {s[0]:.2f}x{s[1]:.2f}')
