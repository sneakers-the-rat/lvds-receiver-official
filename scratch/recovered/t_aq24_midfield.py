"""t_aq24: mid-field census on exp236prep -- segs/vias in the corridor
region, excluding the two mapped mouth boxes. Tuple item format."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp236prep.kicad_pcb')
items = load_items(board)

def pts_of(it):
    if it[0] == 'via':
        return [(it[2][0], it[2][1])]
    if it[0] == 'seg':
        return [(it[2][0], it[2][1]), (it[2][2], it[2][3])]
    return []

def in_mouth(it):
    for (x, y) in pts_of(it):
        if 69.5 <= x <= 74.5 and 3.5 <= y <= 10.5:
            return True
        if 84.0 <= x <= 94.0 and -22.5 <= y <= -13.0:
            return True
    return False

for li, ln in enumerate(['F', 'In2', 'B']):
    print(f'== {ln} ==')
    out = []
    for it in items[li]:
        if it[0] not in ('seg', 'via'):
            continue
        ps = pts_of(it)
        if not any(64 <= x <= 94 and -22 <= y <= 11 for (x, y) in ps):
            continue
        if in_mouth(it):
            continue
        out.append(fmt_it(it))
    for s in sorted(out):
        print('  ', s)
