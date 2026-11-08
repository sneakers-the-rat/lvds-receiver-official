"""t_ap10: per-segment worst-fence probe for the ap9 CC1 re-lay
poly (why did all 12 configs fail at correct widths?)."""
import sys, math, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, seg_margin, in_box_pool, apply_rip,
                      fmt_it)
from router import netclass

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp233.kicad_pcb')
items = load_items(b)
A5 = (29.250, 71.480)
CC1_ANCHOR = (30.925, 67.250)
BIGBOX = (26.0, 48.0, 42.0, 76.0)

RIPS = [('via', 'DM_CON', 29.875, 70.375),
        ('seg', 'DM_CON', 29.875, 70.375),
        ('seg', 'DM_CON', 30.250, 70.980),
        ('seg', 'DM_CON', 29.625, 70.625),
        ('seg', 'DM_CON', 30.125, 70.125),
        ('seg', 'DM_CON', 30.125, 69.875),
        ('via', 'CC2', 30.375, 72.375),
        ('seg', 'CC2', 30.500, 72.930),
        ('seg', 'CC2', 30.375, 72.375),
        ('seg', 'CC2', 30.375, 71.625),
        ('seg', 'CC2', 30.375, 70.875),
        ('seg', 'CC2', 30.625, 70.625),
        ('seg', 'CC2', 30.625, 70.125),
        ('seg', 'CC2', 30.875, 69.875),
        ('seg', 'CC2', 31.125, 69.625),
        ('seg', 'CC1', 29.250, 69.980),
        ('seg', 'CC1', 29.875, 69.625),
        ('seg', 'CC1', 30.125, 69.375),
        ('seg', 'CC1', 30.125, 68.875),
        ('seg', 'CC1', 30.375, 68.625),
        ('seg', 'CC1', 30.625, 68.375),
        ('seg', 'CC1', 30.875, 68.125),
        ('seg', 'CC1', 30.925, 67.500),
        ('seg', 'VBUS_RAW', 30.375, 70.875),
        ('seg', 'VBUS_RAW', 30.625, 70.625)]
statics, nrip = apply_rip(items, RIPS)
pool = in_box_pool(statics, BIGBOX, pad=1.2)
for ty in (69.60, 69.10):
    for ex in (30.30, 30.80):
        poly = [A5, (29.250, ty), (ex, ty), CC1_ANCHOR]
        hws = [0.125, 0.125, 0.10]
        print(f'-- ty={ty} ex={ex}')
        for i, (a, c) in enumerate(zip(poly, poly[1:])):
            m, w = seg_margin(0, a, c, 'CC1', hws[i], pool[0],
                              step=0.02)
            print(f'   seg{i} {a}->{c} hw{hws[i]}: {m:+.3f} '
                  f'[{fmt_it(w)}]')
