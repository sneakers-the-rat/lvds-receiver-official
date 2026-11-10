import sys
sys.path.insert(0, 'hw')
import pcbnew, repair, router6
from router import netclass

b = pcbnew.LoadBoard('hw/pdlvds_rx.fr10.kicad_pcb')
items, pad_cells = repair.build_items(b)
# map pad desc -> (net, anchor, layer)
targets = sys.argv[1:]
for net, descs in [(n, d) for n, d in
                   [(t.split(':')[0], t.split(':')[1]) for t in targets]]:
    width, clr = netclass(net)
    neck_pts = [p[2] for p in pad_cells[net]]
    for d, cs, p in pad_cells[net]:
        if d != descs:
            continue
        ax, ay = p
        li = cs[0][0]
        print(f'== {descs} net {net} anchor ({ax:.3f},{ay:.3f}) layer {li} '
              f'width {width} clr {clr}')
        for ux, uy, nm in ((1,0,'E'),(-1,0,'W'),(0,1,'S'),(0,-1,'N')):
            for bd in router6.BEND_DS:
                bx, by = ax + ux*bd, ay + uy*bd
                hw1 = router6._neck_hw(width, ax, ay, bx, by, neck_pts)
                # worst blocker
                worst = 1e9; wnet = None
                for it in router6._candidates(items[li], li, ax, ay, bx, by):
                    if it[1] == net:
                        continue
                    need = hw1 + max(router6._clr(net, clr, li),
                                     router6._clr(it[1], it[3], li))
                    dd = router6.seg_item_dist(it, ax, ay, bx, by)
                    if dd - need < worst:
                        worst = dd - need; wnet = it[1]
                print(f'   {nm} d={bd:4.2f} margin={worst:7.3f} '
                      f'blocker={wnet}')
