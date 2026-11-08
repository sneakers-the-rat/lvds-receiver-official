"""t_aq22: debug margins at candidate points (statics as t_aq21)."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool, fmt_it
from router import netclass

exec(open('scratch/work/aq/t_aq21_jointscan.py').read().split('pool =')[0])
pool = in_box_pool(statics, (84.0, 94.0, -21.5, -13.0), pad=1.2)

for (net, x, y) in [('SPI_MOSI', 88.75, -17.85), ('DAC_SYNC', 89.95, -17.85),
                    ('SPI_MOSI', 88.75, -18.10), ('DAC_SYNC', 89.75, -18.30)]:
    print(f'== via {net} ({x},{y}) ==')
    for l in range(3):
        m, w = pt_margin(l, x, y, net, 0.25, pool[l])
        print(f'   L{l} {m:+.3f} vs {fmt_it(w)}')
for (net, a, c, li) in [
        ('SPI_MOSI', (88.75, -17.85), (88.75, -17.05), 0),
        ('DAC_SYNC', (89.95, -17.85), (90.25, -17.55), 0),
        ('DAC_SYNC', (89.95, -19.6), (89.95, -17.85), 2),
        ('DAC_SYNC', (88.9, -19.6), (89.95, -19.6), 2)]:
    m, w = seg_margin(li, a, c, net, 0.1, pool[li], step=0.02)
    print(f'== seg {net} {a}->{c} L{li}: {m:+.3f} vs {fmt_it(w)} ==')
