import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair, router
from router import netclass
exec(open('scratch/island_stitch.py').read().split('gnd_net = ')[0].replace("sys.argv[1]", "'scratch/heal182f.kicad_pcb'").replace("sys.argv[2]", "'/dev/null'"))
islands = [(7, (71.3, 73.2, 23.7, 27.1)), (10, (74.9, 77.8, 7.0, 10.9)),
           (12, (78.8, 80.4, 3.8, 6.7)), (13, (73.6, 73.9, 3.8, 5.5))]
for idx, (x0, x1, y0, y1) in islands:
    n_ring = n_in1 = n_ok = 0
    blockers = {}
    gx = x0 - 0.35
    while gx <= x1 + 0.35:
        gy = y0 - 0.35
        while gy <= y1 + 0.35:
            x, y = round(gx, 3), round(gy, 3)
            if ring_touches_F_fill(x, y):
                n_ring += 1
                if in1_polys.Contains(pcbnew.VECTOR2I(MM(x), MM(y))):
                    n_in1 += 1
                    # find blocker
                    blocked = None
                    for li in range(3):
                        for it in items[li].near(li, x, y):
                            if it[1] == 'GND': continue
                            clr = max(gnd_clr, netclass(it[1])[1]) + MARGIN
                            dd = router.dist_to_item(it, x, y)
                            if dd < VIA_R + clr:
                                blocked = f'{it[1]} L{li} d={dd:.2f} need={VIA_R + clr:.2f}'
                                break
                        if blocked: break
                    if blocked: blockers[blocked] = blockers.get(blocked, 0) + 1
                    else: n_ok += 1
            gy += 0.125
        gx += 0.125
    print(f'island {idx}: ring={n_ring} in1={n_in1} ok={n_ok}')
    for b, c in sorted(blockers.items(), key=lambda kv: -kv[1])[:3]: print('    blocked:', b, 'x', c)
