"""Gate the GND-island heal design (exp223 field, post-rip):
rip +3V3D diagonal + landing + trunk east run; add via(74.25,3.50),
In2 jog, via(72.875,3.375). Exact item model, t_ai_lib."""
import sys, wx
_app = wx.App(False)
sys.path.insert(0, 'scratch/work/ai')
import pcbnew
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp223.kicad_pcb')
items = load_items(b)
RIPSEG = {((74.25, 3.662), (73.625, 3.375)), ((73.625, 3.375), (73.375, 3.375)),
          ((72.625, 3.375), (73.375, 3.375)), ((73.375, 3.375), (72.625, 3.375))}
def is_rip(it):
    if it[0] != 'seg' or it[1] != '+3V3D':
        return False
    d = it[2]
    return ((round(d[0],3), round(d[1],3)), (round(d[2],3), round(d[3],3))) in RIPSEG or \
           ((round(d[2],3), round(d[3],3)), (round(d[0],3), round(d[1],3))) in RIPSEG
n = 0
items2 = {0: [], 1: [], 2: []}
for li in range(3):
    for it in items[li]:
        if is_rip(it):
            n += 1
        else:
            items2[li].append(it)
print(f'ripped {n} seg instances (expect 3, F only)')
box = (70.0, 77.0, 0.5, 7.0)
pool = {li: in_box_pool(items2[li], box, pad=1.2) for li in range(3)}
for (x, y) in [(74.25, 3.50), (74.25, 3.55), (72.875, 3.375)]:
    for li in range(3):
        m, w = pt_margin(li, x, y, '+3V3D', 0.25, pool[li])
        print(f'via ({x},{y}) L{li}: margin {m:+.3f} worst {fmt_it(w) if w else None}')
m, w = seg_margin(1, (74.25, 3.50), (72.875, 3.375), '+3V3D', 0.125, pool[1])
print(f'In2 jog: margin {m:+.3f} worst {fmt_it(w) if w else None}')
m, w = seg_margin(0, (72.625, 3.375), (72.875, 3.375), '+3V3D', 0.30, pool[0])
print(f'F trunk short: margin {m:+.3f} worst {fmt_it(w) if w else None}')
