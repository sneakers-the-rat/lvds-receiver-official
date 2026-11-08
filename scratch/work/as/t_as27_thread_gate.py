import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = load_items(board)
THREAD = [(69.9, 3.18), (69.95, 3.9), (70.0, 4.5), (69.875, 4.625),
          (69.8, 4.85), (69.625, 5.0), (69.5, 5.4), (69.5, 5.5)]
for a, b in zip(THREAD, THREAD[1:]):
    m, w = seg_margin(0, a, b, 'CAP_DATA', 0.1, items[0], step=0.02)
    print(f'F CAP_DATA {a}->{b}: {m:+.3f} vs {w}')
