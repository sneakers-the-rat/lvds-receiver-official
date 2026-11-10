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
shape = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(77.62), MMf(17.88)),
                             pcbnew.VECTOR2I(MMf(77.62), MMf(17.88)), MMf(0.6))
hit = None
for n2, l2, s2, desc in items:
    if n2 == 'ULPI_CK':
        continue
    shared = ALL & l2
    need = need_for('ULPI_CK', n2, shared)
    if shape.Collide(s2, MMf(need - 0.001)):
        hit = f"BLOCKED by {n2} {desc} need{need}"
        break
print(hit or 'CK via (77.62,17.88): clean')
