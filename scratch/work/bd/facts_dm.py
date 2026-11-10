import wx
wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp257.kicad_pcb')
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
for t in b.GetTracks():
    if t.GetNetname() in ('DM_PHY', 'ULPI_DIR', 'CDR_SQUELCH') :
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition(); x, y = p.x/1e6, p.y/1e6
            if 70 < x < 78 and 14 < y < 21:
                print(f"  VIA {t.GetNetname():12s} ({x:.3f},{y:.3f}) d={t.GetWidth()/1e6:.2f}")
        else:
            s, e = t.GetStart(), t.GetEnd()
            pts = [(s.x/1e6, s.y/1e6), (e.x/1e6, e.y/1e6)]
            if all(70 < p[0] < 78 and 14 < p[1] < 21 for p in pts):
                print(f"  {LN[t.GetLayer()]} {t.GetNetname():12s} ({pts[0][0]:.3f},{pts[0][1]:.3f})-({pts[1][0]:.3f},{pts[1][1]:.3f}) w={t.GetWidth()/1e6}")
