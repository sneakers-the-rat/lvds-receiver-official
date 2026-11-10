"""t_af29: connect +3V3A U7.25 (77.75,11.562) on exp217.

F stub south (77.75,11.562)->(77.75,10.15); via d0.8 at
(77.75,10.15) (drill copied from the existing +3V3A via at
(75.625,8.625)); In2 (77.75,10.15)->(77.0,10.125)->
(75.625,10.125) landing on the +3V3A In2 vertical's top
joint. All gated in-model first (stub/via/seg margins vs
the full exp217 item model); refill; save candidate.
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from router import netclass, dist_to_item

MMf = pcbnew.ToMM
SRC = 'hw/pdlvds_rx.exp217.kicad_pcb'
OUT = 'scratch/work/exp218cand.kicad_pcb'
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

NET = '+3V3A'
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

PAD = (77.75, 11.562); VIA = (77.75, 10.15)
IN2_PATH = [(77.75, 10.15), (77.0, 10.125), (75.625, 10.125)]
fails = []
m, w = seg_margin(0, PAD, VIA)
print(f'F stub: {m:+.3f} worst {w}')
if m < 0:
    fails.append(('F stub', m, w))
for li in range(3):
    m, w = pt_margin(li, VIA[0], VIA[1], 0.4)
    print(f'via layer {li}: {m:+.3f} worst {w}')
    if m < 0:
        fails.append(('via', li, m, w))
for a, b in zip(IN2_PATH, IN2_PATH[1:]):
    m, w = seg_margin(1, a, b)
    print(f'In2 {a}->{b}: {m:+.3f} worst {w}')
    if m < 0:
        fails.append(('In2', a, m, w))
if fails:
    print('GATE FAILURES — not laying')
    sys.exit(1)

# drill of the existing +3V3A via at (75.625,8.625)
drill = 0.4
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == NET:
        p = MMf(t.GetPosition())
        if abs(p[0] - 75.625) < 0.01 and abs(p[1] - 8.625) < 0.01:
            drill = MMf(t.GetDrillValue())
            print(f'existing +3V3A via drill: {drill}')
code = board.GetNetcodeFromNetname(NET)
MM = pcbnew.FromMM
def add_track(a, b, lay, w=0.2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(w))
    t.SetLayer(lay)
    t.SetNetCode(code)
    board.Add(t)
add_track(PAD, VIA, pcbnew.F_Cu)
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(VIA[0]), MM(VIA[1])))
v.SetWidth(MM(0.8))
v.SetDrill(MM(drill))
v.SetViaType(pcbnew.VIATYPE_THROUGH)
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNetCode(code)
board.Add(v)
for a, b in zip(IN2_PATH, IN2_PATH[1:]):
    add_track(a, b, pcbnew.In2_Cu)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')
