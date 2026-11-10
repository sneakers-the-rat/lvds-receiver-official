import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai'); sys.path.insert(0, 'hw')
from t_ai_lib import load_items, pt_margin, in_box_pool, fmt_it
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp231.kicad_pcb')
items = load_items(b)
pool = in_box_pool(items, (29.0, 34.6, -5.8, 1.5), pad=1.2)
for li in range(3):
    m, w = pt_margin(li, 30.72, -3.55, 'HV_SHDN', 0.25, pool[li])
    print(f'L{li}: {m:+.3f} worst {fmt_it(w)}')
