import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items
from router import netclass
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp8.kicad_pcb')
items = build_items(board)
target = sys.argv[1]
net = pos = half = None
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if f"{fp.GetReference()}.{pad.GetNumber()}" == target:
            bb = pad.GetBoundingBox()
            net = pad.GetNetname(); pos = pcbnew.ToMM(pad.GetPosition())
            half = (pcbnew.ToMM(bb.GetWidth())/2, pcbnew.ToMM(bb.GetHeight())/2)
print(f"{target} net={net} pos={pos} half={half}")
px, py = pos; hx, hy = half
width, clr = netclass(net)
print("netclass width/clr:", width, clr)

def blockers(shape, layers, safety=0.0):
    out = []
    for kind, n2, l2, s2, desc in items:
        if n2 == net: continue
        shared = layers & l2
        if not shared: continue
        need = need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001 + safety)):
            out.append((kind, n2, desc, round(need,3)))
    return out

best = []
for dv in (0.55, 0.7, 0.85, 1.0, 1.15, 1.3, 1.5, 1.8, 2.2):
    for k in range(16):
        a = k*math.pi/8; ca, sa = math.cos(a), math.sin(a)
        ext = min(hx/abs(ca) if ca else 1e9, hy/abs(sa) if sa else 1e9)
        startd = max(ext-0.08, 0.25*ext)
        sx, sy = px+startd*ca, py+startd*sa
        vx, vy = px+dv*ca, py+dv*sa
        neck = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(sx),MM(sy)), pcbnew.VECTOR2I(MM(vx),MM(vy)), MM(0.2))
        nb = blockers(neck, {pcbnew.F_Cu})
        disc = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(vx),MM(vy)), pcbnew.VECTOR2I(MM(vx),MM(vy)), MM(0.6))
        db = blockers(disc, ALL)
        best.append((len(nb)+len(db), dv, round(math.degrees(a)), [b[1]+':'+b[2] for b in nb], [b[1]+':'+b[2] for b in db]))
best.sort()
for b in best[:6]:
    print(b)

print("--- straight out (angle 0) by dv ---")
for dv in (1.0, 1.15, 1.3, 1.5, 1.8, 2.2, 2.6):
    ca, sa = 1.0, 0.0
    ext = hx
    startd = max(ext-0.08, 0.25*ext)
    sx, sy = px+startd, py
    vx, vy = px+dv, py
    neck = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(sx),MM(sy)), pcbnew.VECTOR2I(MM(vx),MM(vy)), MM(0.2))
    disc = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(vx),MM(vy)), pcbnew.VECTOR2I(MM(vx),MM(vy)), MM(0.6))
    print(dv, "neck:", [b[1]+':'+b[2] for b in blockers(neck, {pcbnew.F_Cu})],
          "disc:", [b[1]+':'+b[2] for b in blockers(disc, ALL)])
