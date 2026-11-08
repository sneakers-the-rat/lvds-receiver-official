"""t_as9: gate the exp239 heal on exp238 statics.
Heal = rip +3V3D In2 seg (72.875,3.375)->(74.25,3.5) [redundant parallel hop],
add GND stitch via (73.68,3.5) d0.5 into the orphaned F GND strip.
(Deleting SCK's dangling B-B via needs no gate: removal only.)"""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, apply_rip

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp238.kicad_pcb')
items = load_items(board)
rips = [('seg', '+3V3D', 74.25, 3.5)]  # endpoint spec: matches only the In2 seg
statics, nrip = apply_rip({l: list(items[l]) for l in range(3)}, rips)
print('model rips applied:', nrip)
worst_all = 9
for l in range(3):
    m, w = pt_margin(l, 73.68, 3.5, 'GND', 0.25, statics[l])
    print(f'layer {l}: stitch via (73.68,3.5) margin {m:+.3f} worst {w}')
    worst_all = min(worst_all, m)
print('WORST', f'{worst_all:+.3f}', '-> GATE', 'CLEAN' if worst_all >= 0 else 'FAIL')
