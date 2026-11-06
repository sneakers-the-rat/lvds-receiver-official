import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
src = open('scratch/island_stitch.py').read()
exec(src.split('gnd_net = ')[0])
x0, x1, y0, y1 = 71.3, 73.2, 23.7, 27.1   # island 7
ccx, ccy = (x0 + x1) / 2, (y0 + y1) / 2
n_in1 = n_viaok = 0
reasons = {}
r = 0.4
while r <= 3.0:
    n = max(16, int(2 * math.pi * r / 0.125))
    for k in range(n):
        a = 2 * math.pi * k / n
        x, y = round(ccx + r * math.cos(a), 3), round(ccy + r * math.sin(a), 3)
        if not in1_polys.Contains(pcbnew.VECTOR2I(MM(x), MM(y))):
            reasons['in1'] = reasons.get('in1', 0) + 1; continue
        n_in1 += 1
        # via_ok with reason
        why = None
        for li in range(3):
            for it in items[li].near(li, x, y):
                if it[1] == 'GND': continue
                clr = max(gnd_clr, netclass(it[1])[1]) + MARGIN
                if router.dist_to_item(it, x, y) < VIA_R + clr:
                    why = f'item {it[1]} L{li}'; break
            if why: break
        if not why:
            for net, a2, b2, hw in in1_foreign:
                clr = max(gnd_clr, netclass(net)[1]) + MARGIN
                if seg_pt_dist(x, y, a2, b2) < hw + VIA_R + clr:
                    why = f'in1trk {net}'; break
        if not why and any(in_fills(x, y, l, foreign_fills) for l in foreign_fills):
            why = 'foreign_fill'
        if not why:
            for hx, hy, hr in holes:
                if math.hypot(x - hx, y - hy) < VIA_D / 2 + hr + 0.25:
                    why = 'hole'; break
        if why: reasons[why] = reasons.get(why, 0) + 1
        else: n_viaok += 1
    r += 0.2
print('island 7 candidates: in1 pass', n_in1, 'via_ok pass', n_viaok)
for k2, v2 in sorted(reasons.items(), key=lambda kv: -kv[1])[:6]: print('   ', k2, v2)
