"""t_ac18: remove groute's duplicated DIR dive on the combined
board: via (75.750,17.250), B seg (75.750,17.250)-(71.375,19.125),
F seg (75.750,16.875)-(75.750,17.250). The original stub (via
(75.875,17.375) + identical B seg) keeps DIR continuous:
pad -> F stub -> via (75.875,17.375) -> B -> (71.375,19.125) ->
the new B journey. Refill + reload-verify netname counts.
"""
import sys
import wx
_app = wx.App(False)
import pcbnew

src, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
MM = pcbnew.ToMM

def key(t):
    if t.Type() == pcbnew.PCB_VIA_T:
        p = MM(t.GetPosition())
        return ('via', round(p[0], 3), round(p[1], 3))
    a, b = MM(t.GetStart()), MM(t.GetEnd())
    return ('seg', t.GetLayerName(),
            (round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3)))

targets = {
    ('via', 75.75, 17.25),
    ('seg', 'B.Cu', (75.75, 17.25), (71.375, 19.125)),
    ('seg', 'F.Cu', (75.75, 16.875), (75.75, 17.25)),
}
ripped = 0
for t in list(board.GetTracks()):
    if t.GetNetname() != 'ULPI_DIR':
        continue
    k = key(t)
    kswap = None
    if k[0] == 'seg':
        kswap = ('seg', k[1], k[3], k[2])
    if k in targets or (kswap and kswap in targets):
        board.Remove(t)
        ripped += 1
        print('ripped', k)
print('total ripped', ripped)
assert ripped == 3, 'expected exactly the 3 duplicate items'

board.Save(out)
print('saved (unfilled)', out)
