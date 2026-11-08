"""t_at27: measure min field along the as-session CLK journey in its
own ablated model (band + +3V3D-web removed). Samples the polyline
at 0.01 and reports min G per run + the binding fence."""
import wx
_app = wx.App(False)
import pcbnew, sys, math, json
import numpy as np
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)

def centre(it):
    d = it[2]
    if it[0] == 'seg':
        return ((d[0] + d[2]) / 2, (d[1] + d[3]) / 2)
    return (d[0], d[1])

pool = {0: [], 1: [], 2: []}
for li in range(3):
    for it in items[li]:
        cx, cy = centre(it)
        if li == 1 and it[1] == 'HV_SHDN' and cx < 70.2 and cy < 7:
            continue
        if li == 0 and it[1] == '+3V3D' and 70 < cx < 76 and 20 < cy < 26:
            continue
        pool[li].append(it)

net = 'CAP_CLK'
J = json.load(open('scratch/work/as/journey_CAP_CLK_CD.json'))

def margin_at(l, x, y):
    box = (x - 2.2, x + 2.2, y - 2.2, y + 2.2)
    local = L.in_box_pool(pool, box, pad=0.6)
    return L.pt_margin(l, x, y, net, 0.10, local[l])

for run in J['runs']:
    l = run['layer']
    pts = run['pts']
    worst = (9.9, None, None)
    for a, b in zip(pts, pts[1:]):
        n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.01))
        for i in range(n):
            x = a[0] + (b[0] - a[0]) * i / n
            y = a[1] + (b[1] - a[1]) * i / n
            m, w = margin_at(l, x, y)
            if m < worst[0]:
                worst = (m, (round(x, 2), round(y, 2)), w)
    print(f"L{l} {pts[0]} -> {pts[-1]}: min field {worst[0]:+.3f} "
          f"at {worst[1]} vs {L.fmt_it(worst[2])}", flush=True)
for (vx, vy) in J['vias']:
    ms = []
    for l in range(3):
        box = (vx - 2.2, vx + 2.2, vy - 2.2, vy + 2.2)
        local = L.in_box_pool(pool, box, pad=0.6)
        m, w = L.pt_margin(l, vx, vy, net, 0.25, local[l])
        ms.append(m)
    print(f"via ({vx},{vy}): per-layer margins "
          f"{['%+.3f' % m for m in ms]}", flush=True)
