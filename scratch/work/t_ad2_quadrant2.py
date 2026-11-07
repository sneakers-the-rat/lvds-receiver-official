"""t_ad2: ULPI trio exit repack v2 -- open STP's dive gate.

DIR via slide is limited to (75.5,17.521) by NXT's exit seg
(a via needs 0.55 from it and U7.10's pad corner needs 0.30:
the two fence points are 0.897 apart, feasible with slack).
CK via to (76.625,17.5). DIR/CK via centres end 1.125 apart:
no via fits between them (needs 1.4), but a TRACK threads
between (0.56/0.565 vs 0.55) and STP's dive via goes SOUTH of
the pair at (76.06,17.95) (0.706/0.723 vs 0.7) -- that dive is
t_ad3's job; this script only moves DIR/CK/NXT.

S1 ULPI_NXT F exit v3: rip (75.25,16.875)->(74.5,19.25);
   add (75.25,16.875)->(74.65,17.8)->(74.5,19.25). Perp 0.316
   to U7.10's GND pad corner, 0.561 to DIR's new via, 0.44 to
   DM_PHY's F vertical x74.125 (needs 0.425).
S2 ULPI_DIR: rip F stub + via (75.875,17.375) + B seg; add
   F stub (75.75,16.875)->(75.5,17.521), via (75.5,17.521),
   B seg (75.5,17.521)->(71.375,19.125) (via on its own line).
S3 ULPI_CK: rip F stub + via (76.62,17.30); add F stub
   (76.75,16.438)->(76.625,17.5), via (76.625,17.5), In2 seg
   (76.62,17.3)->(76.625,17.5).

Usage: xvfb-run -a python3 scratch/work/t_ad2_quadrant2.py IN OUT
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

def key(t):
    if t.Type() == pcbnew.PCB_VIA_T:
        p = MM(t.GetPosition())
        return ('via', round(p[0], 3), round(p[1], 3))
    a, b = MM(t.GetStart()), MM(t.GetEnd())
    return ('seg', t.GetLayerName(),
            (round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3)))

RIPS = {
    'ULPI_NXT': {('seg', 'F.Cu', (75.25, 16.875), (74.5, 19.25))},
    'ULPI_DIR': {('seg', 'F.Cu', (75.75, 16.875), (75.875, 17.375)),
                 ('via', 75.875, 17.375),
                 ('seg', 'B.Cu', (75.875, 17.375), (71.375, 19.125))},
    'ULPI_CK': {('seg', 'F.Cu', (76.75, 16.438), (76.62, 17.3)),
                ('via', 76.62, 17.3)},
}
doomed = []
for t in list(board.GetTracks()):
    net = t.GetNetname()
    if net not in RIPS:
        continue
    k = key(t)
    kswap = ('seg', k[1], k[3], k[2]) if k[0] == 'seg' else None
    if k in RIPS[net] or (kswap and kswap in RIPS[net]):
        doomed.append((net, k, t))
for net, k, t in doomed:
    board.Remove(t)
    print(f'ripped [{net}]', k)
assert len(doomed) == 6, len(doomed)

def seg(net, layer_id, a, b, w=0.2):
    t = pcbnew.PCB_TRACK(board)
    t.SetNetCode(codes[net])
    t.SetLayer(layer_id)
    t.SetWidth(pcbnew.FromMM(w))
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
    board.Add(t)
    print(f'added [{net}] seg', a, '->', b)

def via(net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetNetCode(codes[net])
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.FromMM(0.5))
    v.SetDrill(pcbnew.FromMM(0.3))
    board.Add(v)
    print(f'added [{net}] via ({x},{y})')

F = pcbnew.F_Cu
B = pcbnew.B_Cu
IN2 = board.GetLayerID('In2.Cu')

seg('ULPI_NXT', F, (75.25, 16.875), (74.65, 17.8))
seg('ULPI_NXT', F, (74.65, 17.8), (74.5, 19.25))
seg('ULPI_DIR', F, (75.75, 16.875), (75.5, 17.521))
via('ULPI_DIR', 75.5, 17.521)
seg('ULPI_DIR', B, (75.5, 17.521), (71.375, 19.125))
seg('ULPI_CK', F, (76.75, 16.438), (76.625, 17.5))
via('ULPI_CK', 76.625, 17.5)
seg('ULPI_CK', IN2, (76.62, 17.3), (76.625, 17.5))

board.Save(out)
print('saved', out)
