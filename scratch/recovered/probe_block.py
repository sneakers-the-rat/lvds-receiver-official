import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MMf = pcbnew.FromMM
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp101.kicad_pcb')
items = []
for fp in b.GetFootprints():
    for pad in fp.Pads():
        net = pad.GetNetname()
        if not net:
            continue
        layers = {l for l in ALL if pad.IsOnLayer(l)}
        items.append((net, layers, pad.GetEffectiveShape(),
                      f"pad {fp.GetReference()}.{pad.GetNumber()}"))
for t in b.GetTracks():
    net = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        items.append((net, set(ALL), t.GetEffectiveShape(),
                      f"via@({pcbnew.ToMM(p.x):.2f},{pcbnew.ToMM(p.y):.2f})"))
    else:
        s, e = t.GetStart(), t.GetEnd()
        items.append((net, {t.GetLayer()}, t.GetEffectiveShape(),
                      f"trk L{t.GetLayer()} ({pcbnew.ToMM(s.x):.2f},{pcbnew.ToMM(s.y):.2f})->({pcbnew.ToMM(e.x):.2f},{pcbnew.ToMM(e.y):.2f})"))

def seg(x1, y1, x2, y2, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x1), MMf(y1)),
                                pcbnew.VECTOR2I(MMf(x2), MMf(y2)), MMf(w))

def probe(net, shape, layers, label):
    for n2, l2, s2, desc in items:
        if n2 == net:
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        if shape.Collide(s2, MMf(need - 0.001)):
            print(f"{label}: BLOCKED by {n2} {desc} need{need}")
            return
    print(f"{label}: clean")

probe('DP_PHY', seg(73.56, 15.25, 71.50, 15.25, 0.2), {0}, 'DP lane')
probe('DP_PHY', seg(71.50, 15.25, 71.50, 15.25, 0.6), ALL, 'DP via')
probe('+5V', seg(73.85, 13.55, 73.85, 13.55, 0.6), ALL, '+5V via')
probe('+5V', seg(73.56, 13.75, 73.85, 13.55, 0.25), {0}, '+5V neck')
probe('DP_PHY', seg(73.56, 15.25, 71.50, 15.45, 0.2), {0}, 'DP lane2')
probe('DP_PHY', seg(71.50, 15.45, 71.50, 15.45, 0.6), ALL, 'DP via2')
probe('+5V', seg(73.56, 13.75, 70.35, 13.75, 0.25), {0}, '+5V lane long')
probe('DP_PHY', seg(73.56, 15.25, 70.45, 15.35, 0.2), {0}, 'DP lane3')
probe('DP_PHY', seg(70.45, 15.35, 70.45, 15.35, 0.6), ALL, 'DP via3')
probe('ULPI_CK', seg(77.62, 17.88, 77.62, 17.88, 0.6), ALL, 'CK via restore')
