import sys, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard("hw/pdlvds_rx.exp81.kicad_pcb")
MM = pcbnew.ToMM
for z in b.Zones():
    if z.GetNetname() != "GND": continue
    for layer in (pcbnew.B_Cu, pcbnew.F_Cu):
        if not z.IsOnLayer(layer): continue
        poly = z.GetFilledPolysList(layer)
        pts = set()
        for oi in range(poly.OutlineCount()):
            ch = poly.Outline(oi)
            for i in range(ch.PointCount()):
                p = ch.Point(i)
                x, y = MM(p.x), MM(p.y)
                if -2 <= x <= 38 and -30 <= y <= -6:
                    pts.add((round(x,2), round(y,2)))
        bins = {}
        for (x, y) in pts:
            bins.setdefault(int(x), []).append(y)
        edge = {k: (min(v), max(v)) for k, v in sorted(bins.items())}
        print(f"== layer {layer} outlines={poly.OutlineCount()}")
        print("  x:(minY,maxY)", edge)
