import sys, pcbnew, math
sys.path.insert(0, 'hw')
import importlib.util
spec = importlib.util.spec_from_file_location('repair', 'scratch/repair.py')
repair = importlib.util.module_from_spec(spec); spec.loader.exec_module(repair)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp185.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
items = repair.build_items(b)
# extend with In1 items (build_items models F/In2/B only)
layname = {pcbnew.F_Cu:'F', pcbnew.In2_Cu:'In2', pcbnew.B_Cu:'B'}
extra = []
def segd(px,py,ax,ay,bx,by):
    dx,dy = bx-ax,by-ay; L2 = dx*dx+dy*dy
    t = 0 if L2==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))
for t in b.GetTracks():
    if t.GetLayer() != pcbnew.In1_Cu: continue
    s,e = t.GetStart(), t.GetEnd()
    if t.Type() == pcbnew.PCB_VIA_T:
        extra.append(('CAP', t.GetNetname(), mm(s.x), mm(s.y), mm(t.GetWidth())/2))
    else:
        extra.append(('SEG', t.GetNetname(), mm(s.x), mm(s.y), mm(e.x), mm(e.y), mm(t.GetWidth())/2))
for fp in b.GetFootprints():
    for p in fp.Pads():
        if not p.IsOnLayer(pcbnew.In1_Cu): continue
        pos = p.GetPosition(); sz = p.GetSize()
        extra.append(('PAD', p.GetNetname(), mm(pos.x), mm(pos.y), mm(sz.x), mm(sz.y)))
print('base items', len(items), 'In1 extra', len(extra))
# F GND outlines
out = {}
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(pcbnew.F_Cu): continue
    ps = z.GetFilledPolysList(pcbnew.F_Cu)
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        out[i] = [(mm(o.CPoint(j).x), mm(o.CPoint(j).y)) for j in range(o.PointCount())]
def inpoly(x, y, pts):
    inside = False; n = len(pts)
    for i in range(n):
        x1,y1 = pts[i]; x2,y2 = pts[(i+1)%n]
        if (y1 > y) != (y2 > y):
            if x < (x2-x1)*(y-y1)/(y2-y1)+x1: inside = not inside
    return inside
def clearance_ok(x, y, r, net='GND'):
    need = {}
    for it in items:
        kind, inet = it[0], it[1]
        if inet == net: continue
        clr = 1.0 if inet.startswith('HV_') or inet in ('APD_K','APD_A') else 0.2
        if kind == 'CAP':
            _,_,cx,cy,cr = it
            if math.hypot(x-cx,y-cy) - cr - r < clr - 1e-9: return False
        elif kind == 'SEG':
            _,_,ax,ay,bx,by,hr = it
            if segd(x,y,ax,ay,bx,by) - hr - r < clr - 1e-9: return False
        elif kind == 'PAD':
            _,_,cx,cy,w,h = it
            dx = max(abs(x-cx)-w/2, 0); dy = max(abs(y-cy)-h/2, 0)
            if math.hypot(dx,dy) - r < clr - 1e-9: return False
        elif kind == 'ZONE':
            pass
    for it in extra:
        kind, inet = it[0], it[1]
        if inet == net: continue
        clr = 1.0 if inet.startswith('HV_') or inet in ('APD_K','APD_A') else 0.2
        if kind == 'CAP':
            _,_,cx,cy,cr = it
            if math.hypot(x-cx,y-cy) - cr - r < clr - 1e-9: return False
        elif kind == 'SEG':
            _,_,ax,ay,bx,by,hr = it
            if segd(x,y,ax,ay,bx,by) - hr - r < clr - 1e-9: return False
        elif kind == 'PAD':
            _,_,cx,cy,w,h = it
            dx = max(abs(x-cx)-w/2, 0); dy = max(abs(y-cy)-h/2, 0)
            if math.hypot(dx,dy) - r < clr - 1e-9: return False
    return True
oi = int(sys.argv[1]); r = float(sys.argv[2])
poly = out[oi]
xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
spots = []
gx = min(xs)
while gx <= max(xs):
    gy = min(ys)
    while gy <= max(ys):
        if inpoly(gx, gy, poly) and clearance_ok(gx, gy, r):
            spots.append((round(gx,3), round(gy,3)))
        gy += 0.125
    gx += 0.125
print(f'outline {oi} via r={r}: {len(spots)} spots')
for s in spots[:60]: print('  ', s)
