import pcbnew, math
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp184.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
out = {}
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu): continue
    ps = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        out[i] = [(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
frag = out[7]
print('outline7 vertices:', len(frag))
def segdist(p, a, b):
    ax,ay=a; bx,by=b; px,py=p
    dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy
    t=0 if L2==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy)), (ax+t*dx, ay+t*dy)
for other in (0, 6, 2, 5):
    B = out[other]
    segs = [(B[i], B[(i+1)%len(B)]) for i in range(len(B))]
    best = (1e9, None, None)
    for p in frag:
        for a,bb in segs:
            d, q = segdist(p, a, bb)
            if d < best[0]: best = (d, p, q)
    print(f'frag7 -> outline{other}: {best[0]:.3f} at {best[1]} -> {best[2]}')
# all F tracks in the neck region x 70..76, y 25.5..29
print('--- F tracks x 70..76, y 25.5..29.5')
for t in b.GetTracks():
    if t.GetLayer() != pcbnew.F_Cu: continue
    s, e = t.GetStart(), t.GetEnd()
    sp, ep = (mm(s.x),mm(s.y)), (mm(e.x),mm(e.y))
    if max(sp[0],ep[0])<70 or min(sp[0],ep[0])>76 or max(sp[1],ep[1])<25.5 or min(sp[1],ep[1])>29.5: continue
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f'VIA {t.GetNetname()} ({sp[0]:.3f},{sp[1]:.3f}) r={mm(t.GetWidth())/2:.2f}')
    else:
        print(f'TRK {t.GetNetname()} ({sp[0]:.3f},{sp[1]:.3f})->({ep[0]:.3f},{ep[1]:.3f}) w={mm(t.GetWidth()):.2f}')
