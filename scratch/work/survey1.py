import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp183.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
L = {0:'F',2:'In1',4:'In2',31:'B'}
X0,X1,Y0,Y1 = 8,32,-9,11
print('--- GND tracks/vias intersecting box')
for t in b.GetTracks():
    if t.GetNetname() != 'GND': continue
    s, e = t.GetStart(), t.GetEnd()
    sp, ep = (mm(s.x),mm(s.y)), (mm(e.x),mm(e.y))
    if max(sp[0],ep[0])<X0 or min(sp[0],ep[0])>X1 or max(sp[1],ep[1])<Y0 or min(sp[1],ep[1])>Y1: continue
    ln = L.get(t.GetLayer(), str(t.GetLayer()))
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f'VIA {ln} at ({sp[0]:.3f},{sp[1]:.3f})')
    else:
        print(f'TRK {ln} ({sp[0]:.3f},{sp[1]:.3f})->({ep[0]:.3f},{ep[1]:.3f}) w={mm(t.GetWidth()):.2f}')
print('--- footprints in box')
for fp in b.GetFootprints():
    p = fp.GetPosition(); x,y = mm(p.x), mm(p.y)
    if X0<=x<=X1 and Y0<=y<=Y1:
        print(fp.GetReference(), (round(x,2), round(y,2)), 'rot', fp.GetOrientationDegrees())
print('--- GND zone F fill polygons (bbox) in box')
for z in b.Zones():
    if z.GetNetname() != 'GND': continue
    try:
        ps = z.GetFilledPolysList(pcbnew.F_Cu)
    except Exception as ex:
        print('zone fill err', ex); continue
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        xs = [mm(o.CPoint(j).x) for j in range(o.PointCount())]
        ys = [mm(o.CPoint(j).y) for j in range(o.PointCount())]
        if max(xs)<X0 or min(xs)>X1 or max(ys)<Y0 or min(ys)>Y1: continue
        print(f'fill bbox x {min(xs):.2f}..{max(xs):.2f} y {min(ys):.2f}..{max(ys):.2f} pts {o.PointCount()}')
