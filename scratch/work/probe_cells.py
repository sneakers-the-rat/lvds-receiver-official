import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
board = pcbnew.LoadBoard(sys.argv[1])
items, pad_cells = repair.build_items(board)
width, clr_net = netclass('GND'); HW = width/2
print('GND width', width, 'clr', clr_net)
pts = [(22.25,-1.0),(22.25,-0.75),(22.25,-0.5),(22.75,-0.5),(23.25,-0.5),(23.25,0.0),(23.25,0.375),(23.25,0.5),(24.25,0.5),(25.25,0.5),(25.75,0.375),(25.75,0.0),(22.25,-1.25),(21.75,-0.5),(23.75,-0.5)]
for x, y in pts:
    bl = []
    for it in items[0].near(0, x, y):
        if it[1] == 'GND': continue
        clr = max(clr_net, netclass(it[1])[1]) + 0.02
        d = router.dist_to_item(it, x, y)
        if d < HW + clr + 0.6:  # show even near misses
            bl.append(f'{it[1]}({it[0]}) d={d:.3f} need={HW+clr:.3f} {"BLOCK" if d < HW+clr else ""}')
    print((x,y), '->', bl if bl else 'clear')
