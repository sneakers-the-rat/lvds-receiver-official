"""t_af15: forced verification of skeleton v2 (see t_af14 for
v1 and its binds). Changes: V4=(79.96875,14.53125) (D3-via
margin +0.024, groute-passable), V5=(80.25,15.1875) with a
channel-threaded stub, V6=(80.75,14.625); D6 tail tried at
rows 15.625/15.6875/15.75. Prints worst item for every check.
"""
import math, sys
sys.path.insert(0, 'hw')

sys.argv = ['t_af11_d5d4small.py', 'hw/pdlvds_rx.exp216.kicad_pcb']
src = open('scratch/work/t_af11_d5d4small.py').read()
head = src.split('# ---- option build')[0]
g = {'__name__': 'af11model'}
exec(compile(head, 't_af11_head', 'exec'), g)

static_box = g['static_box']; ANCH = g['ANCH']; TRK_HW = g['TRK_HW']
pt_margin = g['pt_margin']; poly_items = g['poly_items']
item_pair_margin = g['item_pair_margin']; groute_in2 = g['groute_in2']
pair_clr = g['pair_clr']
from router import dist_to_item

def seg_worst(li, a, b, net, hw, pool):
    m, worst = 9e9, None
    n = max(2, int(math.hypot(b[0]-a[0], b[1]-a[1]) / 0.02) + 1)
    for i in range(n + 1):
        t = i / n
        x, y = a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t
        for it in pool:
            if it[1] == net:
                continue
            d = dist_to_item(it, x, y) - hw - pair_clr(net, it[1])
            if d < m:
                m, worst = d, it
    return m, worst

def stub_statics(net, sp):
    w_all, w_it = 9e9, None
    for a, b in zip(sp, sp[1:]):
        m, it = seg_worst(0, a, b, net, TRK_HW, static_box[0])
        if m < w_all:
            w_all, w_it = m, (a, b, it)
    return w_all, w_it

V4 = (79.96875, 14.53125); V5 = (80.25, 15.1875); V6 = (80.75, 14.625)
stub4 = [(78.4375, 14.25), (78.6875, 14.25), (79.125, 14.375),
         (79.375, 14.625), V4]
stub5 = [(78.4375, 14.75), (78.9, 14.78), (79.3, 15.05),
         (79.5, 15.13), V5]
R = {'ULPI_D4': 0.25, 'ULPI_D5': 0.25, 'ULPI_D6': 0.30}
PRE6 = [(78.4375, 15.25), (78.6875, 15.25), (79.125, 15.375),
        (79.375, 15.625), (79.875, 15.625)]
stub6s = {'row15.625': PRE6 + [(80.875, 15.625), V6],
          'row15.6875': PRE6[:-1] + [(79.875, 15.6875),
                                     (80.875, 15.6875), V6],
          'row15.75': PRE6[:-1] + [(79.875, 15.75),
                                   (80.95, 15.75), V6]}

print('== stub statics ==')
for net, sp in (('ULPI_D4', stub4), ('ULPI_D5', stub5)):
    m, w = stub_statics(net, sp)
    print(f'  {net}: {m:+.3f} worst {w}')
for tag, sp in stub6s.items():
    m, w = stub_statics('ULPI_D6', sp)
    print(f'  ULPI_D6 {tag}: {m:+.3f} worst {w}')

print('== F pairwise ==')
def show(na, sp_a, Va, nb, sp_b, Vb):
    A = poly_items(na, sp_a) + [('via', na, (Va[0], Va[1], R[na]), 0.2)]
    B = poly_items(nb, sp_b) + [('via', nb, (Vb[0], Vb[1], R[nb]), 0.2)]
    pairs = sorted([(item_pair_margin(0, a, b), a, b) for a in A for b in B])
    print(f'  {na}-{nb}: {pairs[0][0]:+.3f}  {pairs[0][1]} vs {pairs[0][2]}')
show('ULPI_D4', stub4, V4, 'ULPI_D5', stub5, V5)
for tag, sp6 in stub6s.items():
    show('ULPI_D6', sp6, V6, 'ULPI_D5', stub5, V5)
    show('ULPI_D4', stub4, V4, 'ULPI_D6', sp6, V6)

print('== via statics (groute threshold 0.004) ==')
for net, V in (('ULPI_D4', V4), ('ULPI_D5', V5), ('ULPI_D6', V6)):
    ms = [pt_margin(li, V[0], V[1], net, R[net], static_box[li])
          for li in range(3)]
    print(f'  {net} {V}: F {ms[0]:+.3f} In2 {ms[1]:+.3f} B {ms[2]:+.3f}')

print('== In2 groute ==')
via4 = ('via', 'ULPI_D4', (V4[0], V4[1], R['ULPI_D4']), 0.2)
via5 = ('via', 'ULPI_D5', (V5[0], V5[1], R['ULPI_D5']), 0.2)
via6 = ('via', 'ULPI_D6', (V6[0], V6[1], R['ULPI_D6']), 0.2)
c4 = groute_in2('ULPI_D4', V4,
                lambda x, y, A=ANCH['ULPI_D4']:
                math.hypot(x-A[0], y-A[1]) <= 0.03, [via6, via5])
print(f'  D4 connector: {"None" if c4 is None else len(c4)} pts')
if c4:
    print(f'    {c4}')
    i4 = poly_items('ULPI_D4', c4)
    c6 = groute_in2('ULPI_D6', V6,
                    lambda x, y, A=ANCH['ULPI_D6']:
                    math.hypot(x-A[0], y-A[1]) <= 0.03,
                    [via4, via5] + i4)
    print(f'  D6 connector: {"None" if c6 is None else len(c6)} pts')
    if c6:
        print(f'    {c6}')
        i6 = poly_items('ULPI_D6', c6)
        c5 = groute_in2('ULPI_D5', V5,
                        lambda x, y: x >= 84.25 or y <= 11.25,
                        [via4, via6] + i4 + i6)
        print(f'  D5 connector: {"None" if c5 is None else len(c5)} pts')
        if c5:
            print(f'    {c5}')
