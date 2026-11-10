"""t_af22: gate and lay D5's onward journey on exp217cand.

In2 (w0.2): (80.25,15.1875) -> (82.6,15.1875) east, then a
x+y=97.79 diagonal to (94.49,3.3), west jog to via
(93.9,3.3) d0.5, F seg (93.9,3.3) -> U6.73 pad (92.662,2.75).
Every segment and the via are gated against the candidate
board's full item model (seg_margin / pt margins >= 0);
aborts on any negative. Refills zones, saves exp217cand2.
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from router import netclass, dist_to_item

MMf = pcbnew.ToMM
SRC = 'scratch/work/exp217cand.kicad_pcb'
OUT = 'scratch/work/exp217cand2.kicad_pcb'
board = pcbnew.LoadBoard(SRC)
LAYERS_K = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
items = {0: [], 1: [], 2: []}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        net = pad.GetNetname()
        x, y = MMf(pad.GetPosition())
        sx, sy = MMf(pad.GetSize())
        data = (x, y, sx / 2, sy / 2,
                math.radians(pad.GetOrientationDegrees()))
        clr = netclass(net)[1] if net else 0.2
        for li, ln in enumerate(LAYERS_K):
            if pad.IsOnLayer(ln):
                items[li].append(('pad', net, data, clr))
for t in board.GetTracks():
    net = t.GetNetname()
    clr = netclass(net)[1] if net else 0.2
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = MMf(t.GetPosition())
        r = MMf(t.GetWidth()) / 2
        for li in range(3):
            items[li].append(('via', net, (x, y, r), clr))
    else:
        if t.GetLayer() not in LAYERS_K:
            continue
        li = LAYERS_K.index(t.GetLayer())
        a = MMf(t.GetStart()); b = MMf(t.GetEnd())
        w = MMf(t.GetWidth())
        items[li].append(('seg', net, (a[0], a[1], b[0], b[1], w / 2), clr))

NET = 'ULPI_D5'
def pair_clr(n1, n2):
    return max(netclass(n1)[1], netclass(n2)[1])

def seg_margin(li, a, b, hw=0.1, step=0.01):
    m, worst = 9e9, None
    n = max(2, int(math.hypot(b[0]-a[0], b[1]-a[1]) / step) + 1)
    for i in range(n + 1):
        t = i / n
        x, y = a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t
        for it in items[li]:
            if it[1] == NET:
                continue
            d = dist_to_item(it, x, y) - hw - pair_clr(NET, it[1])
            if d < m:
                m, worst = d, it
    return m, worst

def pt_margin(li, x, y, rad):
    m, worst = 9e9, None
    for it in items[li]:
        if it[1] == NET:
            continue
        d = dist_to_item(it, x, y) - rad - pair_clr(NET, it[1])
        if d < m:
            m, worst = d, it
    return m, worst

IN2_PATH = [(80.25, 15.1875), (82.6, 15.1875), (94.49, 3.3),
            (93.9, 3.3)]
VIA = (93.9, 3.3)
F_SEG = [(93.9, 3.3), (92.662, 2.75)]
fails = []
for a, b in zip(IN2_PATH, IN2_PATH[1:]):
    m, w = seg_margin(1, a, b)
    print(f'In2 {a}->{b}: {m:+.3f} worst {w}')
    if m < 0:
        fails.append((a, b, m, w))
for li in range(3):
    m, w = pt_margin(li, VIA[0], VIA[1], 0.25)
    print(f'via {VIA} layer {li}: {m:+.3f} worst {w}')
    if m < 0:
        fails.append(('via', li, m, w))
m, w = seg_margin(0, F_SEG[0], F_SEG[1])
print(f'F arrival: {m:+.3f} worst {w}')
if m < 0:
    fails.append(('F', m, w))
if fails:
    print('GATE FAILURES — not laying')
    sys.exit(1)

code = board.GetNetcodeFromNetname(NET)
MM = pcbnew.FromMM
def add_track(a, b, lay):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(0.2))
    t.SetLayer(lay)
    t.SetNetCode(code)
    board.Add(t)
for a, b in zip(IN2_PATH, IN2_PATH[1:]):
    add_track(a, b, pcbnew.In2_Cu)
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(VIA[0]), MM(VIA[1])))
v.SetWidth(MM(0.5))
v.SetDrill(MM(0.3))
v.SetViaType(pcbnew.VIATYPE_THROUGH)
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNetCode(code)
board.Add(v)
add_track(F_SEG[0], F_SEG[1], pcbnew.F_Cu)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')
