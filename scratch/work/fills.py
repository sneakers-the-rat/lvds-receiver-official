import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp184.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
targets = {'X2.2': (72.55,24.575), 'C16.2': (76.775,9.75), 'U6.51': (80.25,4.662), 'U6.38': (73.75,4.662), 'C29.2': (22.275,-1.5)}
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu): continue
    ps = z.GetFilledPolysList(pcbnew.F_Cu)
    print('outlines:', ps.OutlineCount())
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        xs = [mm(o.CPoint(j).x) for j in range(o.PointCount())]
        ys = [mm(o.CPoint(j).y) for j in range(o.PointCount())]
        area = 0
        for j in range(o.PointCount()):
            x1,y1 = xs[j], ys[j]; x2,y2 = xs[(j+1)%len(xs)], ys[(j+1)%len(ys)]
            area += x1*y2 - x2*y1
        area = abs(area)/2
        tag = ''
        for name,(tx,ty) in targets.items():
            if min(xs)-0.01 <= tx <= max(xs)+0.01 and min(ys)-0.01 <= ty <= max(ys)+0.01:
                tag += f' contains?{name}'
        if area < 3000:
            print(f'outline {i}: area {area:.1f} bbox x {min(xs):.2f}..{max(xs):.2f} y {min(ys):.2f}..{max(ys):.2f} pts {o.PointCount()}{tag}')
        else:
            print(f'outline {i}: MAIN area {area:.0f} pts {o.PointCount()}{tag}')
