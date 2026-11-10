import wx
_app = wx.App(False)
import pcbnew, sys
sys.path.insert(0, 'hw')
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp262.kicad_pcb')
def mm(v): return v/1e6
for t in b.GetTracks():
    n = t.GetNetname()
    if n not in ('+3V3D', '+3V3A', 'PHY_1V8'): continue
    lay = {0:'F',31:'B',2:'In2'}.get(t.GetLayer(), str(t.GetLayer()))
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        if 77.5 < mm(p.x) < 80.5 and 15.5 < mm(p.y) < 19.5:
            print('VIA', n, lay, round(mm(p.x),3), round(mm(p.y),3), round(mm(t.GetWidth()),2))
    else:
        s, e = t.GetStart(), t.GetEnd()
        cx, cy = (mm(s.x)+mm(e.x))/2, (mm(s.y)+mm(e.y))/2
        if 77.5 < cx < 80.5 and 15.5 < cy < 19.5:
            print('TRK', n, lay, (round(mm(s.x),3), round(mm(s.y),3)), (round(mm(e.x),3), round(mm(e.y),3)), round(mm(t.GetWidth()),3))
