import sys, pcbnew, math
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp187.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
LAYERS = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
def segd(px,py,ax,ay,bx,by):
    dx,dy = bx-ax,by-ay; L2 = dx*dx+dy*dy
    t = 0 if L2==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))
obs = {l: [] for l in LAYERS}
for t in b.GetTracks():
    net = t.GetNetname()
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        for l in LAYERS:
            if t.IsOnLayer(l):
                obs[l].append((net, 'CAP', mm(p.x), mm(p.y), mm(t.GetWidth())/2))
    else:
        s, e = t.GetStart(), t.GetEnd()
        obs[t.GetLayer()].append((net, 'SEG', mm(s.x), mm(s.y), mm(e.x), mm(e.y), mm(t.GetWidth())/2))
for fp in b.GetFootprints():
    for p in fp.Pads():
        net = p.GetNetname(); pos = p.GetPosition(); sz = p.GetSize()
        ang = math.radians(p.GetOrientationDegrees())
        for l in LAYERS:
            if p.IsOnLayer(l):
                obs[l].append((net, 'PAD', mm(pos.x), mm(pos.y), mm(sz.x)/2, mm(sz.y)/2, ang))
def clr_of(net):
    return 1.0 if (net.startswith('HV_') or net in ('APD_K','APD_A')) else 0.2
def ok(x, y, r, net):
    for l in LAYERS:
        for o in obs[l]:
            if o[0] == net: continue
            clr = clr_of(o[0])
            if o[1] == 'CAP':
                if math.hypot(x-o[2], y-o[3]) - o[4] - r < clr - 1e-9: return False
            elif o[1] == 'SEG':
                if segd(x,y,o[2],o[3],o[4],o[5]) - o[6] - r < clr - 1e-9: return False
            else:
                _,_,cx,cy,hw,hh,ang = o
                dx, dy = x-cx, y-cy
                ca, sa = math.cos(-ang), math.sin(-ang)
                lx, ly = dx*ca-dy*sa, dx*sa+dy*ca
                ex = max(abs(lx)-hw, 0); ey = max(abs(ly)-hh, 0)
                if math.hypot(ex,ey) - r < clr - 1e-9: return False
    return True
net = sys.argv[1]; X0,X1,Y0,Y1 = (float(v) for v in sys.argv[2:6]); r = float(sys.argv[6])
spots = []
gx = X0
while gx <= X1+1e-9:
    gy = Y0
    while gy <= Y1+1e-9:
        if ok(gx, gy, r, net): spots.append((round(gx,3), round(gy,3)))
        gy += 0.125
    gx += 0.125
print(f'{net} via r={r} in x {X0}..{X1} y {Y0}..{Y1}: {len(spots)} spots')
for s in spots[:100]: print('  ', s)
