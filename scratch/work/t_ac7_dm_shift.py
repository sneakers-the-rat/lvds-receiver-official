"""t_ac7: DM_PHY In2 vertical re-lay, -0.50 west — open NXT's gate.

Ground truth (exp214 dumps, t_ac2/t_ac3 floods, t_ac4 probes;
dist_to_item measures to copper EDGE, so a w0.2 track between two
w0.25 walls needs 0.425 from each centreline):
NXT's In2 canyon runs between DM_PHY's vertical (x68.375,
y24.375-27.625) and REFCLK's staircase (line x+y=95.5, vertical
x68.875 y26.625-27.875), with XO's vertical at x69.625. The triple
span DM..XO is 1.25; every arrangement with all three standing is
0.05-0.10 too tight for a fourth track in either gap (proven by
margins: canyon pinch -0.071 at (68.875,26.125); slot window
68.675..68.575 empty; REFCLK east shift capped at x69.175 by XO,
leaving window 68.80..68.75 empty). Trial t_ac5 (REFCLK corner
+0.25 east, vertical x69.125) left the flood reach byte-identical:
the diagonal's endpoint still guards the pinch and the slot window
is 68.80..68.70 — still empty.

Fix: move DM's vertical west by 0.50 to x67.875 (re-lay its two
staircase joins with the same step rhythm). With REFCLK original:
slot centrelines 67.875..68.875 = 1.00, NXT centreline column
x68.375 passes with dist 0.500 to both verticals, 0.559 to
REFCLK's corner endpoint (68.875,26.625), 0.442 to REFCLK's
diagonal line at the last diagonal-governed row. REFCLK and XO
untouched; DP_PHY is on B (different layer) so the pair's layer
split is unaffected locally.

Ripped (DM_PHY, In2, w0.25), exact endpoints from the board dump:
  (68.375,24.375)-(68.625,24.125)   NE join step
  (68.375,24.375)-(68.375,27.625)   vertical
  (68.375,27.625)-(68.125,27.875)   SW corner step
  (68.125,27.875)-(67.875,28.125)   SW step
  (67.875,28.125)-(67.625,28.375)   SW step
Added (same net/layer/width), blend anchors (68.625,24.125) NE and
(67.625,28.375) SW, both untouched chain points:
  (68.625,24.125)-(68.375,24.375)
  (68.375,24.375)-(68.125,24.625)
  (68.125,24.625)-(67.875,24.875)
  (67.875,24.875)-(67.875,27.625)   vertical at x67.875
  (67.875,27.625)-(67.625,27.875)
  (67.625,27.875)-(67.625,28.375)
First-cut defects (DRC on t_ac9, fixed in this revision): the NE
diagonal passed 0.607 from the +3V3A via at (67.375,24.125) d0.6
(needs 0.625 centreline) — the join now steps further south before
turning onto the vertical, clearing the via by ~0.90; and the SW
blend anchor was wrongly taken as (67.375,28.625), orphaning the
step (67.625,28.375)-(67.375,28.625) — the chain now lands on
(67.625,28.375), the point that step actually hangs from.

Usage: xvfb-run -a python3 scratch/work/t_ac7_dm_shift.py IN OUT
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

src, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
MM = pcbnew.FromMM

code = board.GetNetcodeFromNetname('DM_PHY')
assert code > 0

RIP = [((68.375, 24.375), (68.625, 24.125)),
       ((68.375, 24.375), (68.375, 27.625)),
       ((68.375, 27.625), (68.125, 27.875)),
       ((68.125, 27.875), (67.875, 28.125)),
       ((67.875, 28.125), (67.625, 28.375))]
ADD = [((68.625, 24.125), (68.375, 24.375)),
       ((68.375, 24.375), (68.125, 24.625)),
       ((68.125, 24.625), (67.875, 24.875)),
       ((67.875, 24.875), (67.875, 27.625)),
       ((67.875, 27.625), (67.625, 27.875)),
       ((67.625, 27.875), (67.625, 28.375))]

def key(a, b):
    return tuple(sorted([(round(a[0], 3), round(a[1], 3)),
                         (round(b[0], 3), round(b[1], 3))]))

want = {key(a, b) for a, b in RIP}
ripped = 0
for t in list(board.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != 'DM_PHY':
        continue
    if t.GetLayer() != pcbnew.In2_Cu:
        continue
    a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
    if key(a, b) in want:
        board.Remove(t)
        ripped += 1
print(f'ripped {ripped} of {len(RIP)}')
assert ripped == len(RIP)

for a, b in ADD:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(0.25))
    t.SetLayer(pcbnew.In2_Cu)
    t.SetNetCode(code)
    board.Add(t)
print(f'added {len(ADD)}')

zr = pcbnew.ZONE_FILLER(board)
zr.Fill(board.Zones())
board.Save(out)
print('saved', out)
