import pcbnew, math
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp184.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
outlines = {}
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu): continue
    ps = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        outlines[i] = [(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
def segdist(p, a, b):
    ax,ay=a; bx,by=b; px,py=p
    dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy
    t=0 if L2==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy)), (ax+t*dx, ay+t*dy)
for other in (9, 0, 5, 6):
    A = outlines[12]; B = outlines[other]
    segsB = [(B[i], B[(i+1)%len(B)]) for i in range(len(B))]
    best = (1e9, None, None)
    for p in A:
        for a,bb in segsB:
            d, q = segdist(p, a, bb)
            if d < best[0]: best = (d, p, q)
    print(f'outline12 -> outline{other}: min vertex-seg dist {best[0]:.3f} at {best[1]} -> {best[2]}')
# GND pads inside outline 9 bbox region (x 79.8..91.3, y 3.8..16.6)
print('--- GND pads in outline9 region')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() != 'GND': continue
        p = pad.GetPosition(); x,y = mm(p.x), mm(p.y)
        if 79.8<=x<=91.3 and 3.8<=y<=16.6:
            print(f'  {fp.GetReference()}.{pad.GetNumber()} ({x:.2f},{y:.2f})')
print('--- GND vias in region')
for t in b.GetTracks():
    if t.GetNetname()=='GND' and t.Type()==pcbnew.PCB_VIA_T:
        s = t.GetStart(); x,y = mm(s.x), mm(s.y)
        if 79.8<=x<=91.3 and 3.8<=y<=16.6: print(f'  via ({x:.2f},{y:.2f})')
