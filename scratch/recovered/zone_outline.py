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
    print('layer', pcbnew.LayerName(z.GetFirstLayer()), 'chains:', o.OutlineCount(), 'holes:', o.HoleCount(0))
    ch = o.Outline(0)
    pts = [(round(pcbnew.ToMM(ch.Point(i).x),2), round(pcbnew.ToMM(ch.Point(i).y),2)) for i in range(ch.PointCount())]
    print('  points:', pts)
