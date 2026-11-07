"""t_ac23: move I2C_SDA's mouth via NE from (69.875,0.625) to
(70.125,0.875) -- an existing waypoint of SDA's own In2 staircase
-- so its d0.6 disc stops poisoning the GND fill neck west of
U6.31. SDA stays continuous: In2 staircase now ends at the new
via; a short B seg (70.125,0.875)->(69.875,0.625) joins the top
of SDA's B vertical (which keeps its (69.875,0.625) endpoint).

Rip: SDA via (69.875,0.625); SDA In2 seg (70.125,0.875)-(69.875,0.625).
Add: SDA via (70.125,0.875) d0.5/drill 0.3; SDA B seg w0.25
(70.125,0.875)->(69.875,0.625).

Usage: xvfb-run -a python3 scratch/work/t_ac23_sda_move.py IN OUT
(Refill afterwards in a fresh process with t_ac19.)
"""
import sys
import wx
_app = wx.App(False)
import pcbnew

src, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
MM = pcbnew.ToMM
codes = {}
for t in board.GetTracks():
    codes.setdefault(t.GetNetname(), t.GetNetCode())
sda = codes['I2C_SDA']

def key(t):
    if t.Type() == pcbnew.PCB_VIA_T:
        p = MM(t.GetPosition())
        return ('via', round(p[0], 3), round(p[1], 3))
    a, b = MM(t.GetStart()), MM(t.GetEnd())
    return ('seg', t.GetLayerName(),
            (round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3)))

targets = {('via', 69.875, 0.625),
           ('seg', 'In2.Cu', (70.125, 0.875), (69.875, 0.625))}
ripped = 0
for t in list(board.GetTracks()):
    if t.GetNetname() != 'I2C_SDA':
        continue
    k = key(t)
    kswap = ('seg', k[1], k[3], k[2]) if k[0] == 'seg' else None
    if k in targets or (kswap and kswap in targets):
        board.Remove(t)
        ripped += 1
        print('ripped', k)
assert ripped == 2, f'expected 2 rips, got {ripped}'

v = pcbnew.PCB_VIA(board)
v.SetNetCode(sda)
v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(70.125), pcbnew.FromMM(0.875)))
v.SetWidth(pcbnew.FromMM(0.5))
v.SetDrill(pcbnew.FromMM(0.3))
board.Add(v)
print('added SDA via (70.125,0.875)')
t = pcbnew.PCB_TRACK(board)
t.SetNetCode(sda)
t.SetLayer(pcbnew.B_Cu)
t.SetWidth(pcbnew.FromMM(0.25))
t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(70.125), pcbnew.FromMM(0.875)))
t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(69.875), pcbnew.FromMM(0.625)))
board.Add(t)
print('added SDA B seg (70.125,0.875)->(69.875,0.625)')
board.Save(out)
print('saved', out)
