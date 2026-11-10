import sys, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp236prep.kicad_pcb')
LN = {0: 'F', 1: 'In2', 2: 'B'}
def mm(v): return v / 1e6
items = {0: [], 1: [], 2: []}
for fp in b.GetFootprints():
    for p in fp.Pads():
        net = p.GetNetname(); c = p.GetCenter()
        for li in range(3):
            if p.IsOnLayer(li):
                r = p.GetBoundingBox()
                items[li].append(('pad', net, (mm(r.GetLeft()), mm(r.GetTop()), mm(r.GetRight()), mm(r.GetBottom()))))
for t in b.GetTracks():
    net = t.GetNetname(); ty = type(t).__name__
    if ty == 'PCB_VIA':
        c = t.GetPosition(); d = mm(t.GetWidth())
        for li in range(3):
            items[li].append(('via', net, (round(mm(c.x), 3), round(mm(c.y), 3), round(d / 2, 3))))
    else:
        s, e = t.GetStart(), t.GetEnd(); w = mm(t.GetWidth())
        items[t.GetLayer()].append(('seg', net, (round(mm(s.x), 3), round(mm(s.y), 3), round(mm(e.x), 3), round(mm(e.y), 3), round(w / 2, 3))))
X0, X1, Y0, Y1 = 66.0, 74.6, -3.0, 8.6
for li in range(3):
    print(f'== {LN[li]} ==')
    out = []
    for kind, net, g in items[li]:
        if net in ('DAC_SYNC', 'BIST_DRV'): continue
        if kind == 'pad':
            cx, cy = (g[0] + g[2]) / 2, (g[1] + g[3]) / 2
            if X0 - 1 < cx < X1 + 1 and Y0 - 1 < cy < Y1 + 1:
                out.append(f'  pad {net} rect[{g[0]:.2f},{g[2]:.2f}]x[{g[1]:.2f},{g[3]:.2f}]')
        elif kind == 'via':
            if X0 - 1 < g[0] < X1 + 1 and Y0 - 1 < g[1] < Y1 + 1:
                out.append(f'  via {net} ({g[0]:.3f},{g[1]:.3f}) r{g[2]:.2f}')
        else:
            mx, my = (g[0] + g[2]) / 2, (g[1] + g[3]) / 2
            if X0 - 1 < mx < X1 + 1 and Y0 - 1 < my < Y1 + 1:
                out.append(f'  seg {net} ({g[0]:.2f},{g[1]:.2f})->({g[2]:.2f},{g[3]:.2f}) hw{g[4]:.2f}')
    for l in sorted(set(out)): print(l)
