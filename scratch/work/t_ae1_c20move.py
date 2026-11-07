"""t_ae1: STP quadrant job, stage 1 -- relocate C20 off the dive
latitude and re-tap XI at the new site.

Why: STP's dive via south of the DIR/CK pair sits at (76.06,17.95)
(0.706/0.723 vs 0.7 from the two vias) but C20's pads fence it:
C20.1 rect x[75.275,76.175] y[18.025,18.975] -- a d0.5 via centre
must be >=0.45 from the rect; at x76.06 that forces y<=17.575,
contradicting y>=17.93 from the via pair. For ANY x of C20 in its
row the y17.9 latitude stays fenced (pass-185/186 fence proof).
Relocation is the frontrunner per the inherited arithmetic.

C20 (X1's load cap on XI) moves centre (76.5,18.5)->(80.975,18.4):
pads C20.1 [XI] (80.2,18.4), C20.2 [GND] (81.75,18.4). Site fences
hand-checked vs sv_c20east dump: SQUELCH NE diagonal >=0.45 from
both pad rects; U5.16 pad dy 1.03; +3V3D F y20.375 far; X1.1 pad
west edge x84.75 far. Courtyard vs U5 refereed by check_pcb.

XI re-plan part 1 (this script): rip the B staircase west end that
only existed to touch C20's old pad -- via (75.625,18.625) d0.6
(its disc sat inside C20.1's old rect) + 7 B segs west of
(77.375,20.125). The staircase from (77.375,20.125) east to X1.1
stays. New tap at the moved C20.1: F stub (80.2,18.4)->(80.5,19.35),
via d0.5 (80.5,19.35) (0.625 from XO's In2 vertical x79.875 vs
0.575 needed; 0.555 from U5.16's rect vs 0.45), B vertical
(80.5,19.35)->(80.5,21.125) joining XI's B horizontal y21.125.
XI's U7.28 leg is a separate groute job (t_ae2).

C20.2 [GND]: zone refill decides; stitch via fallback if DRC
shows it isolated.

Usage: xvfb-run -a python3 scratch/work/t_ae1_c20move.py IN OUT
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

# --- move C20 ---
moved = False
for fp in board.GetFootprints():
    if fp.GetReference() == 'C20':
        print('C20 old pos', MM(fp.GetPosition()))
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(80.975),
                                       pcbnew.FromMM(18.4)))
        print('C20 new pos', MM(fp.GetPosition()))
        for pad in fp.Pads():
            print('  pad', pad.GetNumber(), pad.GetNetname(),
                  MM(pad.GetPosition()))
        moved = True
assert moved

def key(t):
    if t.Type() == pcbnew.PCB_VIA_T:
        p = MM(t.GetPosition())
        return ('via', round(p[0], 3), round(p[1], 3))
    a, b = MM(t.GetStart()), MM(t.GetEnd())
    return ('seg', t.GetLayerName(),
            (round(a[0], 3), round(a[1], 3)), (round(b[0], 3), round(b[1], 3)))

RIPS = {
    'XI': {('via', 75.625, 18.625),
           ('seg', 'B.Cu', (75.625, 18.625), (75.875, 18.875)),
           ('seg', 'B.Cu', (75.875, 18.875), (76.125, 19.125)),
           ('seg', 'B.Cu', (76.125, 19.125), (76.375, 19.125)),
           ('seg', 'B.Cu', (76.375, 19.125), (76.625, 19.375)),
           ('seg', 'B.Cu', (76.625, 19.375), (76.875, 19.625)),
           ('seg', 'B.Cu', (76.875, 19.625), (77.125, 19.875)),
           ('seg', 'B.Cu', (77.125, 19.875), (77.375, 20.125))},
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
seg('XI', F, (80.2, 18.4), (80.5, 19.35))
via('XI', 80.5, 19.35)
seg('XI', B, (80.5, 19.35), (80.5, 21.125))

board.Save(out)
print('saved', out)
