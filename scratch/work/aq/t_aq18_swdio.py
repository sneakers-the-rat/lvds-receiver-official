"""t_aq18: SWDIO full chain + J4 pad layers on exp235."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp235.kicad_pcb')
items = load_items(b)
print('=== SWDIO full chain ===')
for li in range(3):
    for it in items[li]:
        if it[1] == 'SWDIO':
            print(f'L{li} {fmt_it(it)}')
print('=== J4 pads per layer (load_items) ===')
for li in range(3):
    ns = [fmt_it(it) for it in items[li]
          if it[0] == 'pad' and it[2][0] > 90 and it[2][1] < -20]
    print(f'L{li}: {len(ns)} pads')
    for s in ns:
        print('   ', s)
