import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
def mm(v): return round(v/1e6, 4)
tracks = [t for t in b.GetTracks()]
pads = []
for fp in b.GetFootprints():
    for pad in fp.Pads():
        pads.append((pad.GetNetname(), mm(pad.GetPosition().x), mm(pad.GetPosition().y),
                     mm(pad.GetSize().x)/2, mm(pad.GetSize().y)/2))
def touches(net, layer, x, y, skip):
    # endpoint touch: same-net pad rect, via centre, or any same-net track
    # endpoint/on-segment (layers: vias touch all, pads F, tracks own layer)
    for (n, px, py, hx, hy) in pads:
        if n == net and abs(x-px) <= hx+0.01 and abs(y-py) <= hy+0.01:
            return True
    for t in tracks:
        if t is skip or t.GetNetname() != net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            vx, vy = mm(t.GetPosition().x), mm(t.GetPosition().y)
            if math.hypot(x-vx, y-vy) <= t.GetWidth()/2e6 + 0.01:
                return True
        elif t.GetLayer() == layer:
            ax, ay = mm(t.GetStart().x), mm(t.GetStart().y)
            bx, by = mm(t.GetEnd().x), mm(t.GetEnd().y)
            dx, dy = bx-ax, by-ay
            L2 = dx*dx+dy*dy
            tt = 0 if L2 == 0 else max(0, min(1, ((x-ax)*dx+(y-ay)*dy)/L2))
            if math.hypot(x-(ax+tt*dx), y-(ay+tt*dy)) <= t.GetWidth()/2e6 + 0.01:
                return True
    return False
LN = {pcbnew.F_Cu:'F', pcbnew.In2_Cu:'In2', pcbnew.B_Cu:'B'}
for t in tracks:
    if t.Type() != pcbnew.PCB_TRACE_T:
        continue
    net = t.GetNetname(); lay = t.GetLayer()
    a = (mm(t.GetStart().x), mm(t.GetStart().y)); c = (mm(t.GetEnd().x), mm(t.GetEnd().y))
    ta = touches(net, lay, a[0], a[1], t); tc = touches(net, lay, c[0], c[1], t)
    if not (ta and tc):
        print(f"DANGLE {net} {LN.get(lay,lay)} {a}->{c} w{mm(t.GetWidth())} len {t.GetLength()/1e6:.4f} touchA={ta} touchB={tc}")
