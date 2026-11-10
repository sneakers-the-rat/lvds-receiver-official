"""t_af14: forced verification of one assembled skeleton.

V4=(80.0,14.5) d0.5, V5=(80.25,15.1875) d0.5,
V6=(80.75,14.625) d0.6; D6 tail row raised to y15.75;
D5 stub bend (79.5,15.125). Prints every margin in the
chain (statics per layer, F pairwise, In2 groute attempt)
so the exact binds are visible whether it passes or not.
"""
import math, sys
sys.path.insert(0, 'hw')

sys.argv = ['t_af11_d5d4small.py', 'hw/pdlvds_rx.exp216.kicad_pcb']
src = open('scratch/work/t_af11_d5d4small.py').read()
head = src.split('# ---- option build')[0]
g = {'__name__': 'af11model'}
exec(compile(head, 't_af11_head', 'exec'), g)

static_box = g['static_box']; RAD = g['RAD']; ANCH = g['ANCH']
TRK_HW = g['TRK_HW']; PAD = g['PAD']
pt_margin = g['pt_margin']; poly_margin = g['poly_margin']
poly_items = g['poly_items']; item_pair_margin = g['item_pair_margin']
groute_in2 = g['groute_in2']
from repair import build_items
from router import dist_to_item

V4 = (80.0, 14.5); V5 = (80.25, 15.1875); V6 = (80.75, 14.625)
stub4 = [(78.4375, 14.25), (78.6875, 14.25), (79.125, 14.375),
         (79.375, 14.625), V4]
stub4b = [(78.4375, 14.25), (78.6875, 14.25), (79.125, 14.375), V4]
stub5 = [(78.4375, 14.75), (79.5, 15.125), V5]
stub6 = [(78.4375, 15.25), (78.6875, 15.25), (79.125, 15.375),
         (79.375, 15.625), (79.875, 15.75), (80.95, 15.75), V6]
R = {'ULPI_D4': 0.25, 'ULPI_D5': 0.25, 'ULPI_D6': 0.30}

def via_statics(net, V):
    for li, lname in ((0, 'F'), (2, 'In2'), (1, 'B')):
        m, worst = 9e9, None
        for it in static_box[li]:
            if it[1] == net:
                continue
            d = dist_to_item(V[0], V[1], it) - R[net] - g['net_clr'](it[1], net)
            if d < m:
                m, worst = d, it
        print(f'  {net} via {V} on {lname}: {m:+.3f}  worst {worst}')

print('== via statics ==')
via_statics('ULPI_D4', V4)
via_statics('ULPI_D5', V5)
via_statics('ULPI_D6', V6)
print('== stub statics (F) ==')
for net, sp in (('ULPI_D4', stub4), ('ULPI_D4', stub4b),
                ('ULPI_D5', stub5), ('ULPI_D6', stub6)):
    print(f'  {net} stub -> {poly_margin(0, sp, net, TRK_HW, static_box[0]):+.3f}'
          f'  {sp}')
print('== F pairwise ==')
def show(na, sp_a, Va, nb, sp_b, Vb):
    A = poly_items(na, sp_a) + [('via', na, (Va[0], Va[1], R[na]), 0.2)]
    B = poly_items(nb, sp_b) + [('via', nb, (Vb[0], Vb[1], R[nb]), 0.2)]
    pairs = sorted([(item_pair_margin(0, a, b), a, b) for a in A for b in B])
    print(f'  {na}-{nb}: worst {pairs[0][0]:+.3f}  {pairs[0][1]} vs {pairs[0][2]}')
    print(f'          2nd   {pairs[1][0]:+.3f}  {pairs[1][1]} vs {pairs[1][2]}')
show('ULPI_D4', stub4, V4, 'ULPI_D6', stub6, V6)
show('ULPI_D4', stub4b, V4, 'ULPI_D6', stub6, V6)
show('ULPI_D4', stub4, V4, 'ULPI_D5', stub5, V5)
show('ULPI_D6', stub6, V6, 'ULPI_D5', stub5, V5)
print('== via-via ==')
for a, b, na, nb in ((V4, V5, 'D4', 'D5'), (V4, V6, 'D4', 'D6'),
                     (V5, V6, 'D5', 'D6')):
    d = math.hypot(a[0]-b[0], a[1]-b[1])
    print(f'  {na}-{nb}: {d:.3f}')
print('== In2 groute ==')
via4 = ('via', 'ULPI_D4', (V4[0], V4[1], R['ULPI_D4']), 0.2)
via5 = ('via', 'ULPI_D5', (V5[0], V5[1], R['ULPI_D5']), 0.2)
via6 = ('via', 'ULPI_D6', (V6[0], V6[1], R['ULPI_D6']), 0.2)
c4 = groute_in2('ULPI_D4', V4,
                lambda x, y, A=ANCH['ULPI_D4']:
                math.hypot(x-A[0], y-A[1]) <= 0.03, [via6, via5])
print(f'  D4 connector: {"None" if c4 is None else len(c4)} pts')
if c4:
    i4 = poly_items('ULPI_D4', c4)
    c6 = groute_in2('ULPI_D6', V6,
                    lambda x, y, A=ANCH['ULPI_D6']:
                    math.hypot(x-A[0], y-A[1]) <= 0.03,
                    [via4, via5] + i4)
    print(f'  D6 connector: {"None" if c6 is None else len(c6)} pts')
    if c6:
        i6 = poly_items('ULPI_D6', c6)
        c5 = groute_in2('ULPI_D5', V5,
                        lambda x, y: x >= 84.25 or y <= 11.25,
                        [via4, via6] + i4 + i6)
        print(f'  D5 connector: {"None" if c5 is None else len(c5)} pts')
        if c5:
            print(f'  conn4={c4}')
            print(f'  conn6={c6}')
            print(f'  conn5={c5}')
