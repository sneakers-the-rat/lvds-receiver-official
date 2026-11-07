"""t_ac25: move I2C_SDA's mouth via to (69.900,0.820) -- clear of
+3V3A's F escape tracks (0.613 vs the y1.25 seg), SCL's via
(69.375,1.375) (0.764), U6.32's pad (edge 0.448) and the GND
tie's first seg (0.56). SDA continuity: rip the In2 staircase's
last step (70.125,0.875)-(69.875,0.625) and the old via; add
In2 seg (70.125,0.875)->(69.900,0.820), via (69.900,0.820)
d0.5/drill 0.3, B seg w0.25 (69.900,0.820)->(69.875,0.625)
joining the B vertical's kept top endpoint.

Usage: xvfb-run -a python3 scratch/work/t_ac25_sda_move2.py IN OUT
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

def seg(layer_id, a, b, w):
    t = pcbnew.PCB_TRACK(board)
    t.SetNetCode(sda)
    t.SetLayer(layer_id)
    t.SetWidth(pcbnew.FromMM(w))
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
    board.Add(t)
    print('added seg', a, '->', b)

seg(board.GetLayerID('In2.Cu'), (70.125, 0.875), (69.9, 0.82), 0.25)
v = pcbnew.PCB_VIA(board)
v.SetNetCode(sda)
v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(69.9), pcbnew.FromMM(0.82)))
v.SetWidth(pcbnew.FromMM(0.5))
v.SetDrill(pcbnew.FromMM(0.3))
board.Add(v)
print('added SDA via (69.900,0.820)')
seg(pcbnew.B_Cu, (69.9, 0.82), (69.875, 0.625), 0.25)
board.Save(out)
print('saved', out)
