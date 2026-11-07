"""t_ac22: move ULPI_DIR's mouth via west-south to free the GND
fill neck around U6.31's scrap.

Rip: DIR via (67.500,0.125), F seg (67.500,0.125)-(70.625,-1.250).
Add: In2 seg (67.500,0.125)->(67.000,-0.500) (DIR's In2 arrival
stays, via moves to the hop's end), via (67.000,-0.500) d0.5,
F seg (67.000,-0.500)->(70.625,-1.250) (south of the neck strip
and of ULPI_NXT's horizontal mouth seg; clears NXT's diagonal
by >=0.51 at the closest approach).

Usage: xvfb-run -a python3 scratch/work/t_ac22_dir_mouth.py IN OUT
(Refill afterwards in a fresh process with t_ac19.)
"""
import sys
import wx
_app = wx.App(False)
import pcbnew

src, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
MM = pcbnew.ToMM
dirc = None
codes = {}
for t in board.GetTracks():
    codes.setdefault(t.GetNetname(), t.GetNetCode())
dirc = codes['ULPI_DIR']

def key(t):
    if t.Type() == pcbnew.PCB_VIA_T:
        p = MM(t.GetPosition())
        return ('via', round(p[0], 3), round(p[1], 3))
    a, b = MM(t.GetStart()), MM(t.GetEnd())
    return ('seg', t.GetLayerName(),
            (round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3)))

targets = {('via', 67.5, 0.125),
           ('seg', 'F.Cu', (67.5, 0.125), (70.625, -1.25))}
ripped = 0
for t in list(board.GetTracks()):
    if t.GetNetname() != 'ULPI_DIR':
        continue
    k = key(t)
    kswap = ('seg', k[1], k[3], k[2]) if k[0] == 'seg' else None
    if k in targets or (kswap and kswap in targets):
        board.Remove(t)
        ripped += 1
        print('ripped', k)
assert ripped == 2, f'expected 2 rips, got {ripped}'

def seg(layer_id, a, b, w=0.2):
    t = pcbnew.PCB_TRACK(board)
    t.SetNetCode(dirc)
    t.SetLayer(layer_id)
    t.SetWidth(pcbnew.FromMM(w))
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
    board.Add(t)
    print('added seg', a, '->', b)

seg(board.GetLayerID('In2.Cu'), (67.5, 0.125), (67.0, -0.5))
v = pcbnew.PCB_VIA(board)
v.SetNetCode(dirc)
v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(67.0), pcbnew.FromMM(-0.5)))
v.SetWidth(pcbnew.FromMM(0.5))
v.SetDrill(pcbnew.FromMM(0.3))
board.Add(v)
print('added via (67.000,-0.500)')
seg(pcbnew.F_Cu, (67.0, -0.5), (70.625, -1.25))
board.Save(out)
print('saved', out)
