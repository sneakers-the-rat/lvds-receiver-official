import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.expanded.kicad_pcb')
for z in b.Zones():
    if z.GetNetname() != 'GND':
        continue
    o = z.Outline()
    ch = o.Outline(0)
    pts = [(round(pcbnew.ToMM(ch.CPoint(i).x),2), round(pcbnew.ToMM(ch.CPoint(i).y),2)) for i in range(ch.PointCount())]
    print(pcbnew.LayerName(z.GetFirstLayer()), 'npts', ch.PointCount(), 'holes', o.HoleCount(0), pts)
    print('  has SetPoint:', hasattr(ch, 'SetPoint'), '| zone has SetOutline:', hasattr(z, 'SetOutline'))
