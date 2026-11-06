import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
board = pcbnew.LoadBoard('scratch/u3nudge-n.kicad_pcb')
items, pad_cells = repair.build_items(board)
width, clr_net = netclass('+VA')
from collections import Counter
blockers = Counter()
stub_blockers = Counter()
n_via = 0
gx = 37.4
while gx <= 38.8:
    gy = 39.6
    while gy <= 41.8:
        x, y = round(gx, 3), round(gy, 3)
        ok = True
        for li in range(3):
            for it in items[li].near(li, x, y):
                if it[1] == '+VA': continue
                clr = max(clr_net, netclass(it[1])[1]) + 0.05
                d = router.dist_to_item(it, x, y)
                if d < 0.3 + clr:
                    blockers[f'{it[1]} L{li} d={d:.2f} need={0.3 + clr:.2f}'] += 1; ok = False; break
            if not ok: break
        if ok: n_via += 1
        gy += 0.125
    gx += 0.125
print('via_ok points in wide box:', n_via)
for b, c in blockers.most_common(5): print('   ', b, 'x', c)
