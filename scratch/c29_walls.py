import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
board = pcbnew.LoadBoard('scratch/exp182cand.kicad_pcb')
items, pad_cells = repair.build_items(board)
width, clr_net = netclass('GND'); HW = width / 2
def blockers(x, y, li=0):
    out = []
    for it in items[li].near(li, x, y):
        if it[1] == 'GND': continue
        clr = max(clr_net, netclass(it[1])[1]) + 0.02
        d = router.dist_to_item(it, x, y)
        if d < HW + clr: out.append(f'{it[1]}({it[0]}) d={d:.2f} need={HW + clr:.2f}')
    return out
print('WEST edge (x=21.3):')
for y in (-1.2, -1.8, -2.4, -3.0): print('  ', y, blockers(21.3, y))
print('EAST edge (x=24.0):')
for y in (-1.2, -1.8, -2.4, -3.0): print('  ', y, blockers(24.0, y))
print('NORTH edge (y=-0.6):')
for x in (21.8, 22.3, 22.8, 23.3): print('  ', x, blockers(x, -0.6))
print('SOUTH edge (y=-3.4):')
for x in (21.8, 22.3, 22.8, 23.3): print('  ', x, blockers(x, -3.4))
print('IN2 under the well (li=1), via-scale blockers at (21.75,-3.0),(22.25,-2.75):')
for pt in ((21.75, -3.0), (22.25, -2.75), (21.75, -1.25)):
    bl = []
    for it in items[1].near(1, *pt):
        if it[1] == 'GND': continue
        clr = max(clr_net, netclass(it[1])[1]) + 0.05
        d = router.dist_to_item(it, *pt)
        if d < 0.3 + clr: bl.append(f'{it[1]}({it[0]}) d={d:.2f} need={0.3 + clr:.2f}')
    print('  ', pt, bl)
