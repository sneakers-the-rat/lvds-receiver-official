import wx
wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp257.kicad_pcb')
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
print('--- USB_RST items (all)')
for t in b.GetTracks():
    if t.GetNetname() == 'USB_RST':
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition(); print(f"  via ({p.x/1e6:.3f},{p.y/1e6:.3f})")
        else:
            s, e = t.GetStart(), t.GetEnd()
            print(f"  {LN[t.GetLayer()]} seg ({s.x/1e6:.3f},{s.y/1e6:.3f})-({e.x/1e6:.3f},{e.y/1e6:.3f}) w={t.GetWidth()/1e6}")
print('--- items in corridor x[72.8,76.2] y[3.8,17.6], F and B only')
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition(); x, y = p.x/1e6, p.y/1e6
        if 72.8 < x < 76.2 and 3.8 < y < 17.6:
            print(f"  VIA {t.GetNetname():10s} ({x:.3f},{y:.3f}) d={t.GetWidth()/1e6:.2f}")
    elif t.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu):
        s, e = t.GetStart(), t.GetEnd()
        pts = [(s.x/1e6, s.y/1e6), (e.x/1e6, e.y/1e6)]
        if all(72.8 < p[0] < 76.2 and 3.8 < p[1] < 17.6 for p in pts):
            print(f"  {LN[t.GetLayer()]} {t.GetNetname():10s} ({pts[0][0]:.3f},{pts[0][1]:.3f})-({pts[1][0]:.3f},{pts[1][1]:.3f})")
