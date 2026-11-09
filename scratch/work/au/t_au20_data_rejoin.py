"""t_au20: (1) find first DATA30 index (from NW end backwards) whose
tail is fully legal vs the real pool (band included); (2) re-plan
CLK's B entry west-side and re-gate CLK."""
import wx
_app = wx.App(False)
import pcbnew, sys, math, json
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)
J = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
pts = [tuple(p) for p in J['runs'][0]['pts']]
# per-point worst margin of the two adjacent segs vs full pool
pool = [it for l in range(3) for it in items[l]]
segm = []
for a, b in zip(pts, pts[1:]):
    cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    m, w = L.seg_margin(1, a, b, 'CAP_DATA', 0.10,
                        [it for it in items[1]
                         if isinstance(it, tuple) and len(it) >= 4])
    segm.append(m)
# first index from the entry side where ALL subsequent segs >= +0.03
bad = [i for i, m in enumerate(segm) if m < 0.03]
print('last bad seg idx:', max(bad), 'of', len(segm))
for i in range(max(bad) - 2, max(bad) + 4):
    print(f'  seg{i} margin {segm[i]:+.3f} from {pts[i]}')
print('REJOIN candidate point:', pts[max(bad) + 1])
