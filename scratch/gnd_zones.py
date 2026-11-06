import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp182.kicad_pcb')
mm = lambda v: v/1e6
LN = {pcbnew.F_Cu:'F', pcbnew.In1_Cu:'In1', pcbnew.In2_Cu:'In2', pcbnew.B_Cu:'B'}
for z in b.Zones():
    net = z.GetNetname()
    if net != 'GND': continue
    print('ZONE', z.GetZoneName() or '(unnamed)', 'layers:', [LN.get(l,l) for l in z.GetLayerSet().Seq() if l in LN], 'filled:', z.IsFilled())
    for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        if not z.IsOnLayer(l): continue
        polys = z.GetFilledPolysList(l)
        n = polys.OutlineCount()
        print(f'  layer {LN[l]}: {n} filled outlines')
        for i in range(n):
            o = polys.Outline(i)
            xs = [mm(o.CPoint(j).x) for j in range(o.PointCount())]
            ys = [mm(o.CPoint(j).y) for j in range(o.PointCount())]
            print(f'    outline {i}: x[{min(xs):.1f},{max(xs):.1f}] y[{min(ys):.1f},{max(ys):.1f}] pts={o.PointCount()}')
