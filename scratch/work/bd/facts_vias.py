import wx
wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp256.kicad_pcb')
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        x, y = p.x/1e6, p.y/1e6
        if 71.5 < x < 75.5 and 17.5 < y < 20.5:
            print(f"{t.GetNetname():12s} via centre=({x:.3f},{y:.3f}) dia={t.GetWidth()/1e6:.2f}")
