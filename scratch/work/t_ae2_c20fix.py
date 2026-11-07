"""t_ae2: fix t_ae1 -- C20's first east site was dead on arrival.

t_ae1 put C20.1's pad on top of I2C_SDA's via (80.625,18.375)
d0.6 (short XI<->SDA, hole_clearance 0.0) and the tap via
(80.5,19.35) into SDA's In2 vertical x80.375. Cause: the site
was designed against a head-truncated survey dump. Lesson
re-learned: read the FULL dump.

New site: C20 centre (80.975,18.4)->(83.075,18.4); pads
C20.1 [XI] (82.3,18.4), C20.2 [GND] (83.85,18.4). Verified vs
sv_c20east2 (full box x81-86 y15.5-22.5 + SDA full copper):
F band y17.9-18.9 x81.8-84.3 empty (SQUELCH diag is at y<=17.4
there, +3V3D F at y>=20.305); C20.2 rect to X1.1 rect dx 0.45.
Tap via (82.6,19.35) clean on F/In2/B (SDA In2 x80.375 is 2mm
west; SDA B x82.375 ends y15.375; +3V3D B x81.625 ends y15.125;
XO In2 y<=14.7 there). B vertical x82.6 joins XI horizontal
y21.125 as a T.

Also rip the now-redundant XI B staircase west tip
(77.375,20.125)->...->(78.375,21.125) (5 segs): t_ae1 left its
west end dangling (track_dangling) and the tap joins the
horizontal east of it, so the whole tip is dead copper.

Usage: xvfb-run -a python3 scratch/work/t_ae2_c20fix.py IN OUT
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
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(83.075),
                                       pcbnew.FromMM(18.4)))
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
    'XI': {('seg', 'F.Cu', (80.2, 18.4), (80.5, 19.35)),
           ('via', 80.5, 19.35),
           ('seg', 'B.Cu', (80.5, 19.35), (80.5, 21.125)),
           ('seg', 'B.Cu', (77.375, 20.125), (77.625, 20.375)),
           ('seg', 'B.Cu', (77.625, 20.375), (77.625, 20.625)),
           ('seg', 'B.Cu', (77.625, 20.625), (77.875, 20.875)),
           ('seg', 'B.Cu', (77.875, 20.875), (78.125, 20.875)),
           ('seg', 'B.Cu', (78.125, 20.875), (78.375, 21.125))},
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
assert len(doomed) == 8, len(doomed)

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
seg('XI', F, (82.3, 18.4), (82.6, 19.35))
via('XI', 82.6, 19.35)
seg('XI', B, (82.6, 19.35), (82.6, 21.125))

board.Save(out)
print('saved', out)
