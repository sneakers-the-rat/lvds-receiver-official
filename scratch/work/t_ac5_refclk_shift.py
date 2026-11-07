"""t_ac5: REFCLK west-end re-lay — open the canyon slot for ULPI_NXT.

Ground truth (exp214 dumps + t_ac4 probes): NXT's In2 canyon between
DM_PHY's vertical (x68.375, y24.375-27.625) and REFCLK's staircase
dies at its south end: REFCLK's diagonal (line x+y=95.5) turns south
at (68.875,26.625) into a vertical at x68.875 (y26.625-27.875), and
the slot between the two verticals is 68.675..68.575 for an NXT
track centreline — empty, closed by 0.10 total. The canyon pinch at
(68.875,26.125) is short by 0.071 against REFCLK's diagonal.

Fix: end REFCLK's diagonal one step early and run its south vertical
at x69.125 instead of x68.875 (+0.25 east). The diagonal stays on its
own line x+y=95.5; only the corner moves. Slot centreline window
becomes 68.675..68.825; canyon margins at y26.5 go 0.34 -> 0.525.
Blend anchors: NE (69.625,25.875) on the untouched staircase, SW
(68.935,28.375) on the untouched pass-183 zigzag. REFCLK stays one
continuous chain by construction; DRC referees.

Ripped (REFCLK, In2, w0.25) — exact endpoints from the board dump:
  (69.375,26.125)-(69.625,25.875)   staircase step
  (69.125,26.375)-(69.375,26.125)   staircase step
  (68.875,26.625)-(69.125,26.375)   staircase step
  (68.875,26.625)-(68.875,27.875)   south vertical
  (68.875,27.875)-(69.125,28.125)   zigzag step 1
  (69.125,28.125)-(68.935,28.375)   zigzag step 2
Added (same net/layer/width):
  (69.625,25.875)-(69.375,26.125)
  (69.375,26.125)-(69.125,26.375)
  (69.125,26.375)-(69.125,26.625)
  (69.125,26.625)-(69.125,27.875)
  (69.125,27.875)-(69.375,28.125)
  (69.375,28.125)-(68.935,28.375)

Usage: xvfb-run -a python3 scratch/work/t_ac5_refclk_shift.py IN OUT
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

src, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
MM = pcbnew.FromMM

# capture netcodes BEFORE any Remove() (map dies after removal)
code = board.GetNetcodeFromNetname('REFCLK')
assert code > 0

RIP = [((69.375, 26.125), (69.625, 25.875)),
       ((69.125, 26.375), (69.375, 26.125)),
       ((68.875, 26.625), (69.125, 26.375)),
       ((68.875, 26.625), (68.875, 27.875)),
       ((68.875, 27.875), (69.125, 28.125)),
       ((69.125, 28.125), (68.935, 28.375))]
ADD = [((69.625, 25.875), (69.375, 26.125)),
       ((69.375, 26.125), (69.125, 26.375)),
       ((69.125, 26.375), (69.125, 26.625)),
       ((69.125, 26.625), (69.125, 27.875)),
       ((69.125, 27.875), (69.375, 28.125)),
       ((69.375, 28.125), (68.935, 28.375))]

def key(a, b):
    return tuple(sorted([(round(a[0], 3), round(a[1], 3)),
                         (round(b[0], 3), round(b[1], 3))]))

want = {key(a, b) for a, b in RIP}
ripped = 0
for t in list(board.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != 'REFCLK':
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
b2 = pcbnew.LoadBoard(out)
n = sum(1 for t in b2.GetTracks() if t.GetNetname() == 'REFCLK')
print(f'reload REFCLK: {n} items')
