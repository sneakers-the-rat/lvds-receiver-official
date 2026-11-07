"""t_af16: skeleton v3 + off-grid groute seeding.

v2 binds and their fixes:
- D5 stub grazed D6 pad (-0.000) and D4's rising seg
  (-0.006): rise shifted +0.1 east, gentler start.
- D6 row vs V5: -0.112 at row 15.625, -0.050 at 15.6875;
  row 15.75 full-width died on CDR_SQUELCH (-0.036) at its
  east end -> row 15.75 only as far as x80.875, drop from
  there (SQUELCH seg endpoint distance ~0.45).
- D4 groute returned None from the off-grid via
  (79.96875,14.53125): groute_in2's A* seeds on the 0.125
  grid. groute_from_via() seeds the 4 surrounding grid
  points, each joined to the via by a seg_margin-verified
  stub, then runs groute between seed and goal.
"""
import math, sys
sys.path.insert(0, 'hw')

sys.argv = ['t_af11_d5d4small.py', 'hw/pdlvds_rx.exp216.kicad_pcb']
src = open('scratch/work/t_af11_d5d4small.py').read()
head = src.split('# ---- option build')[0]
g = {'__name__': 'af11model'}
exec(compile(head, 't_af11_head', 'exec'), g)

static_box = g['static_box']; ANCH = g['ANCH']; TRK_HW = g['TRK_HW']
pt_margin = g['pt_margin']; seg_margin = g['seg_margin']
poly_items = g['poly_items']; item_pair_margin = g['item_pair_margin']
groute_in2 = g['groute_in2']; pair_clr = g['pair_clr']
from router import dist_to_item

def stub_statics(net, sp):
    m_all = 9e9
    for a, b in zip(sp, sp[1:]):
        m_all = min(m_all, seg_margin(1 - 1, a, b, net, TRK_HW,
                                      static_box[0]))
    return m_all

def groute_from_via(net, V, goal_pred, extra):
    """Seed groute from the grid points around off-grid V."""
    gx = math.floor(V[0] / 0.125) * 0.125
    gy = math.floor(V[1] / 0.125) * 0.125
    seeds = [(gx, gy), (gx + 0.125, gy), (gx, gy + 0.125),
             (gx + 0.125, gy + 0.125)]
    for S in seeds:
        if math.hypot(S[0]-V[0], S[1]-V[1]) < 1e-9:
            path = groute_in2(net, V, goal_pred, extra)
            if path:
                return path
            continue
        pool = static_box[1] + list(extra)
        if pt_margin(1, S[0], S[1], net, TRK_HW, pool) < 0.004:
            continue
        if seg_margin(1, V, S, net, TRK_HW, pool) < 0:
            continue
        path = groute_in2(net, S, goal_pred, extra)
        if path:
            return [V] + path
    return None

V4 = (79.96875, 14.53125); V5 = (80.25, 15.1875); V6 = (80.75, 14.625)
stub4 = [(78.4375, 14.25), (78.6875, 14.25), (79.125, 14.375),
         (79.375, 14.625), V4]
stub5 = [(78.4375, 14.75), (79.0, 14.78), (79.4, 15.05),
         (79.6, 15.14), V5]
stub6 = [(78.4375, 15.25), (78.6875, 15.25), (79.125, 15.375),
         (79.375, 15.625), (79.875, 15.625), (80.0, 15.75),
         (80.875, 15.75), V6]
R = {'ULPI_D4': 0.25, 'ULPI_D5': 0.25, 'ULPI_D6': 0.30}

print('== stub statics ==')
for net, sp in (('ULPI_D4', stub4), ('ULPI_D5', stub5),
                ('ULPI_D6', stub6)):
    print(f'  {net}: {stub_statics(net, sp):+.3f}')
print('== F pairwise ==')
def show(na, sp_a, Va, nb, sp_b, Vb):
    A = poly_items(na, sp_a) + [('via', na, (Va[0], Va[1], R[na]), 0.2)]
    B = poly_items(nb, sp_b) + [('via', nb, (Vb[0], Vb[1], R[nb]), 0.2)]
    pairs = sorted([(item_pair_margin(0, a, b), a, b) for a in A for b in B])
    print(f'  {na}-{nb}: {pairs[0][0]:+.3f}  {pairs[0][1]} vs {pairs[0][2]}')
show('ULPI_D4', stub4, V4, 'ULPI_D5', stub5, V5)
show('ULPI_D6', stub6, V6, 'ULPI_D5', stub5, V5)
show('ULPI_D4', stub4, V4, 'ULPI_D6', stub6, V6)
print('== In2 groute (seeded) ==')
via4 = ('via', 'ULPI_D4', (V4[0], V4[1], R['ULPI_D4']), 0.2)
via5 = ('via', 'ULPI_D5', (V5[0], V5[1], R['ULPI_D5']), 0.2)
via6 = ('via', 'ULPI_D6', (V6[0], V6[1], R['ULPI_D6']), 0.2)
c4 = groute_from_via('ULPI_D4', V4,
                     lambda x, y, A=ANCH['ULPI_D4']:
                     math.hypot(x-A[0], y-A[1]) <= 0.03, [via6, via5])
print(f'  D4 connector: {"None" if c4 is None else len(c4)} pts')
if c4:
    print(f'    {c4}')
    i4 = poly_items('ULPI_D4', c4)
    c6 = groute_from_via('ULPI_D6', V6,
                         lambda x, y, A=ANCH['ULPI_D6']:
                         math.hypot(x-A[0], y-A[1]) <= 0.03,
                         [via4, via5] + i4)
    print(f'  D6 connector: {"None" if c6 is None else len(c6)} pts')
    if c6:
        print(f'    {c6}')
        i6 = poly_items('ULPI_D6', c6)
        c5 = groute_from_via('ULPI_D5', V5,
                             lambda x, y: x >= 84.25 or y <= 11.25,
                             [via4, via6] + i4 + i6)
        print(f'  D5 connector: {"None" if c5 is None else len(c5)} pts')
        if c5:
            print(f'    {c5}')
