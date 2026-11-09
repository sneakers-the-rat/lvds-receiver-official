"""t_ax7: binder for the SCL In2 approach seg + bent variants."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

pool = load_board_pool()
W = (67.4, 5.65)


def seg_gate(a, b, l=1, hw=0.10):
    others = [o for o in pool[l] if o[1] != 'I2C_SCL']
    m, binder = L.seg_margin(l, a, b, 'I2C_SCL', hw, others)
    return m, binder


for a, b in (((66.875, 6.75), W),
             ((66.875, 6.75), (67.05, 6.2)),
             ((66.875, 6.75), (67.15, 6.1)),
             ((66.875, 6.75), (67.3, 6.0))):
    m, binder = seg_gate(a, b)
    print(f'{a}->{b}: {m:+.3f} binder: '
          f'{L.fmt_it(binder) if binder else None}', flush=True)
# two-seg variants via a knuckle
for k in ((67.05, 6.2), (67.15, 6.1), (67.3, 6.0), (67.2, 5.95)):
    m1, b1 = seg_gate((66.875, 6.75), k)
    m2, b2 = seg_gate(k, W)
    print(f'knuckle {k}: seg1 {m1:+.3f} ({L.fmt_it(b1) if b1 else None}) '
          f'seg2 {m2:+.3f} ({L.fmt_it(b2) if b2 else None})', flush=True)
