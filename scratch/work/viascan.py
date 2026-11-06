import pcbnew, math
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp184.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
LAYERS = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
LN = {pcbnew.F_Cu:'F', pcbnew.In1_Cu:'In1', pcbnew.In2_Cu:'In2', pcbnew.B_Cu:'B'}
# foreign copper per layer: pads as OBB (cx,cy,hw,hh,ang), segs as capsules (a,b,r), vias as circles (c,r)
copper = {l: [] for l in LAYERS}
for fp in b.GetFootprints():
    for pad in fp.Pads():
        net = pad.GetNetname()
        if net == 'GND': continue
        pos = pad.GetPosition(); size = pad.GetSize()
        cx, cy = mm(pos.x), mm(pos.y)
        hw, hh = mm(size.x)/2, mm(size.y)/2
        ang = math.radians(pad.GetOrientationDegrees())
        for l in LAYERS:
            if pad.IsOnLayer(l):
                copper[l].append(('obb', net, (cx, cy, hw, hh, ang)))
for t in b.GetTracks():
    net = t.GetNetname()
    if net == 'GND': continue
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition(); cx, cy = mm(p.x), mm(p.y)
        r = mm(t.GetWidth())/2
        for l in LAYERS: copper[l].append(('circ', net, (cx, cy, r)))
    else:
        s, e = t.GetStart(), t.GetEnd()
        a = (mm(s.x), mm(s.y)); bb = (mm(e.x), mm(e.y))
        copper[t.GetLayer()].append(('seg', net, (a, bb, mm(t.GetWidth())/2)))
def d_obb(px, py, o):
    cx, cy, hw, hh, ang = o
    dx, dy = px-cx, py-cy
    c, s = math.cos(-ang), math.sin(-ang)
    lx, ly = dx*c - dy*s, dx*s + dy*c
    qx = max(abs(lx)-hw, 0); qy = max(abs(ly)-hh, 0)
    return math.hypot(qx, qy)
def d_seg(px, py, o):
    (ax, ay), (bx, by), r = o
    dx, dy = bx-ax, by-ay
    L2 = dx*dx+dy*dy
    t = 0 if L2 == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy)) - r
def d_circ(px, py, o):
    cx, cy, r = o
    return math.hypot(px-cx, py-cy) - r
DIST = {'obb': d_obb, 'seg': d_seg, 'circ': d_circ}
def clr_of(net):
    # HV-class nets carry 1.0 mm; everything else 0.2 (matches DRC netclasses as observed)
    return 1.0 if net.startswith('HV_') or net in ('APD_K','APD_A') else 0.2
VIA_R = 0.30
def via_legal(x, y):
    worst = []
    for l in LAYERS:
        for kind, net, o in copper[l]:
            need = VIA_R + clr_of(net)
            d = DIST[kind](x, y, o)
            if d < need: worst.append((LN[l], net, round(d-need, 3)))
    return worst
targets = {'X2.2': (71.0,73.6,23.4,27.4), 'C16.2': (74.6,78.1,6.8,11.1),
           'U6.51': (78.7,80.55,3.7,6.8), 'U6.38': (73.5,74.1,3.7,5.6)}
for name,(x0,x1,y0,y1) in targets.items():
    hits = []
    x = x0
    while x <= x1:
        y = y0
        while y <= y1:
            bad = via_legal(round(x,3), round(y,3))
            if not bad: hits.append((round(x,2), round(y,2)))
            y += 0.25
        x += 0.25
    print(name, 'legal via spots:', hits if hits else 'NONE')
