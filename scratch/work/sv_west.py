import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp211.kicad_pcb')
MM = pcbnew.ToMM
X0, X1, Y0, Y1 = 63, 76.5, -5, 21
for lay_name in ('In2.Cu', 'B.Cu', 'F.Cu'):
    print("=====", lay_name)
    rows = []
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            if lay_name != 'In2.Cu': continue
            q = t.GetPosition(); x, y = MM(q.x), MM(q.y)
            if X0 <= x <= X1 and Y0 <= y <= Y1:
                rows.append(f"VIA {t.GetNetname()} d={MM(t.GetWidth()):.2f} ({x:.3f},{y:.3f})")
            continue
        if b.GetLayerName(t.GetLayer()) != lay_name: continue
        s, e = t.GetStart(), t.GetEnd()
        pts = [(MM(s.x), MM(s.y)), (MM(e.x), MM(e.y))]
        if any(X0 <= p[0] <= X1 and Y0 <= p[1] <= Y1 for p in pts):
            rows.append(f"TRK {t.GetNetname()} w={MM(t.GetWidth()):.2f} ({pts[0][0]:.3f},{pts[0][1]:.3f})->({pts[1][0]:.3f},{pts[1][1]:.3f})")
    for r in sorted(rows): print(r)
