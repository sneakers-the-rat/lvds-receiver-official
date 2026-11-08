import sys
import wx
_app = wx.App(False)
import pcbnew
def polys(path):
    b = pcbnew.LoadBoard(path)
    out = []
    for z in b.Zones():
        if z.GetNetname() != 'GND':
            continue
        fp = z.GetFilledPolysList(pcbnew.F_Cu)
        for i in range(fp.OutlineCount()):
            ol = fp.Outline(i)
            pts = [(p.x/1e6, p.y/1e6) for p in ol.CPoints()]
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            # shoelace area
            A = abs(sum(pts[k][0]*pts[(k+1) % len(pts)][1] - pts[(k+1) % len(pts)][0]*pts[k][1] for k in range(len(pts))))/2
            out.append((round(A,2), round(min(xs),2), round(max(xs),2), round(min(ys),2), round(max(ys),2)))
    return sorted(out)
a = polys('hw/pdlvds_rx.exp218.kicad_pcb')
c = polys('scratch/work/ah/h8r.kicad_pcb')
print(f"exp218: {len(a)} F GND outlines, total {sum(x[0] for x in a):.1f} mm^2")
print(f"h8r:    {len(c)} F GND outlines, total {sum(x[0] for x in c):.1f} mm^2")
sa, sc = set(a), set(c)
print("only in exp218:", sorted(sa-sc))
print("only in h8r:", sorted(sc-sa))
