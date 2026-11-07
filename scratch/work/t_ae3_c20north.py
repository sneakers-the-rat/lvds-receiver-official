"""t_ae3: C20 east field is a three-way pinch -- abandon it.

Measured on t_ae2 (probe_court2, exact GetCourtyard bboxes):
X1 crt x[83.105,88.395] y[7.155,20.845]; C20 crt = centre
+-(1.525,0.775). Courtyard legality needs C20 centre x<81.58,
but I2C_SDA's via (80.625,18.375) d0.6 needs C20.1's rect west
edge >=81.125 i.e. centre >=82.35. Empty. Other east latitudes
die on CDR_SQUELCH's F staircase (y15.3-18.9, x79.9-82.9),
I2C_SDA's In2 x80.375, U5's crt (y>=19.505, x<=82.745).

New site NORTH: C20 centre (76.9,7.9) -- pads C20.1 [XI]
(76.125,7.9), C20.2 [GND] (77.675,7.9). Verified gaps:
courtyards vs C16 (y gap 0.3), R21 (x gap 0.1 bbox), U6, X1
all clear; pads vs R21.2 dx 0.4, vs C16 rects dy 0.9.

XI legs (all hand-checked vs full dumps sv_nw/sv_c20east2):
(i) U7.28 -> C20.1: F stub (76.25,11.562)->(76.25,10.9),
    diag to (76.0,10.6), vertical x76.0 y10.6->8.6 threading
    BETWEEN C16.1/C16.2 rects (gap channel [75.675,76.325],
    track edges 0.225 clear each side), diag into C20.1.
(ii) C20.1 -> XI B staircase: F (76.125,7.9)->(77.0,8.3)
    ->(79.33,9.0)->(79.33,15.6) (0.452 east of U7 D-row rect
    edge 78.878); via (79.33,15.6) (0.61 from I2C_SCL In2
    point (79.875,15.875) vs 0.575; 0.825+ from +3V3A F w0.6
    y16.625); In2 x79.33 y15.6->18.6 (0.545 from SCL In2 and
    XO In2 x79.875 vs 0.425), diag to via (79.3,20.6) (1.04
    from +3V3D via (78.375,20.125) d0.8 vs 0.85); B stub
    (79.3,20.6)->(79.3,21.125); B (79.3,21.125)->(83.125,21.125)
    replacing the ripped horizontal (78.375,21.125)->
    (83.125,21.125) whose west end dangled after t_ae2.

Rips: t_ae2's bad tap (F stub, via (82.6,19.35), B vertical)
and the dangling horizontal.

Usage: xvfb-run -a python3 scratch/work/t_ae3_c20north.py IN OUT
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

for fp in board.GetFootprints():
    if fp.GetReference() == 'C20':
        print('C20 old pos', MM(fp.GetPosition()))
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(76.9),
                                       pcbnew.FromMM(7.9)))
        print('C20 new pos', MM(fp.GetPosition()))
        for pad in fp.Pads():
            print('  pad', pad.GetNumber(), pad.GetNetname(),
                  MM(pad.GetPosition()))

def key(t):
    if t.Type() == pcbnew.PCB_VIA_T:
        p = MM(t.GetPosition())
        return ('via', round(p[0], 3), round(p[1], 3))
    a, b = MM(t.GetStart()), MM(t.GetEnd())
    return ('seg', t.GetLayerName(),
            (round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3)))

RIPS = {
    'XI': {('seg', 'F.Cu', (82.3, 18.4), (82.6, 19.35)),
           ('via', 82.6, 19.35),
           ('seg', 'B.Cu', (82.6, 19.35), (82.6, 21.125)),
           ('seg', 'B.Cu', (78.375, 21.125), (83.125, 21.125))},
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
assert len(doomed) == 4, len(doomed)

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

# leg (i) U7.28 -> C20.1
seg('XI', F, (76.25, 11.562), (76.25, 10.9))
seg('XI', F, (76.25, 10.9), (76.0, 10.6))
seg('XI', F, (76.0, 10.6), (76.0, 8.6))
seg('XI', F, (76.0, 8.6), (76.125, 7.9))
# leg (ii) C20.1 -> staircase
seg('XI', F, (76.125, 7.9), (77.0, 8.3))
seg('XI', F, (77.0, 8.3), (79.33, 9.0))
seg('XI', F, (79.33, 9.0), (79.33, 15.6))
via('XI', 79.33, 15.6)
seg('XI', IN2, (79.33, 15.6), (79.33, 18.6))
seg('XI', IN2, (79.33, 18.6), (79.3, 20.6))
via('XI', 79.3, 20.6)
seg('XI', B, (79.3, 20.6), (79.3, 21.125))
seg('XI', B, (79.3, 21.125), (83.125, 21.125))

board.Save(out)
print('saved', out)
