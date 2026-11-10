import sys, math
sys.path.insert(0, 'hw')
import pcbnew, check_pcb
from hand_stub import build_items
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}

b = pcbnew.LoadBoard('hw/pdlvds_rx.fr11.kicad_pcb')
items = build_items(b)
net, pos, half = 'CDR_VREF', (49.562, 51.25), None
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if f"{fp.GetReference()}.{pad.GetNumber()}" == 'U4.3':
            bb = pad.GetBoundingBox()
            half = (pcbnew.ToMM(bb.GetWidth())/2, pcbnew.ToMM(bb.GetHeight())/2)
px, py = pos; hx, hy = half
print('half', half)
def blockers(shape, layers, safety=0.005):
    out = []
    for kind, n2, l2, s2, desc in items:
        if n2 == net: continue
        shared = layers & l2
        if not shared: continue
        need = need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001 + safety)):
            out.append((n2, desc, round(need, 2)))
    return out
for k in range(16):
    a = k * math.pi / 8
    ca, sa = math.cos(a), math.sin(a)
    ext = hx * abs(ca) + hy * abs(sa)
    sx, sy = px + (ext - 0.02) * ca, py + (ext - 0.02) * sa
    vx, vy = px + 0.7 * ca, py + 0.7 * sa
    neck = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(sx), MM(sy)),
                                pcbnew.VECTOR2I(MM(vx), MM(vy)), MM(0.25))
    nb = blockers(neck, {pcbnew.F_Cu})
    vh = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(vx-0.3), MM(vy)),
                              pcbnew.VECTOR2I(MM(vx+0.3), MM(vy)), MM(0.6))
    vb = blockers(vh, ALL)
    print(f'dir {k:2d} ({ca:5.2f},{sa:5.2f}) neck_block={nb[:3]} via_block={vb[:3]}')
