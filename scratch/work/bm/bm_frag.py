import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp266.kicad_pcb')
gnd_vias = []
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'GND':
        p = t.GetPosition(); gnd_vias.append((p.x/1e6, p.y/1e6))
gnd_pads = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == 'GND':
            pp = p.GetPosition(); gnd_pads.append((pp.x/1e6, pp.y/1e6))
for z in b.Zones():
    if z.GetNetname() != 'GND':
        continue
    layer = z.GetLayer()
    if layer not in (pcbnew.F_Cu, pcbnew.B_Cu):
        continue
    polys = z.GetFilledPolysList(layer)
    n = polys.OutlineCount()
    print('zone layer', layer, 'fragments:', n)
    for i in range(n):
        o = polys.Outline(i)
        xs = [o.GetPoint(i2).x/1e6 for i2 in range(o.PointCount())]
        ys = [o.GetPoint(i2).y/1e6 for i2 in range(o.PointCount())]
        bb = (min(xs), min(ys), max(xs), max(ys))
        def inside(p, pad=0.0):
            return bb[0]-pad <= p[0] <= bb[2]+pad and bb[1]-pad <= p[1] <= bb[3]+pad
        nv = sum(1 for p in gnd_vias if inside(p))
        npd = sum(1 for p in gnd_pads if inside(p))
        area = (bb[2]-bb[0]) * (bb[3]-bb[1])
        if area < 400 or nv == 0:
            print(f'  frag{i} bbox x[{bb[0]:.2f},{bb[2]:.2f}] y[{bb[1]:.2f},{bb[3]:.2f}] vias-in-bbox {nv} pads-in-bbox {npd}')
