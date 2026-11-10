import sys, math
sys.path.insert(0, 'hw')
import pcbnew, check_pcb
from hand_stub import build_items
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM

b = pcbnew.LoadBoard('hw/pdlvds_rx.fr11.kicad_pcb')
items = build_items(b)
net, desc = sys.argv[1], sys.argv[2]
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if f"{fp.GetReference()}.{pad.GetNumber()}" == desc:
            px, py = pcbnew.ToMM(pad.GetPosition())
            bb = pad.GetBoundingBox()
            hx, hy = pcbnew.ToMM(bb.GetWidth())/2, pcbnew.ToMM(bb.GetHeight())/2
print(f'{desc} net {net} at ({px},{py}) half ({hx},{hy})')
def blockers(shape, layers, safety=0.0):
    out = []
    for kind, n2, l2, s2, d2 in items:
        if n2 == net: continue
        shared = layers & l2
        if not shared: continue
        need = need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001 + safety)):
            out.append(f'{n2}({d2},need{need:.2f})')
    return out
for k in range(16):
    a = k * math.pi / 8
    ca, sa = math.cos(a), math.sin(a)
    ext = hx * abs(ca) + hy * abs(sa)
    sx, sy = px + (ext - 0.02) * ca, py + (ext - 0.02) * sa
    res = []
    for ln in (0.5, 0.8, 1.1, 1.4):
        ex, ey = px + (ext + ln) * ca, py + (ext + ln) * sa
        seg = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(sx), MM(sy)),
                                   pcbnew.VECTOR2I(MM(ex), MM(ey)), MM(0.25))
        bl = blockers(seg, {pcbnew.F_Cu})
        res.append(f'L{ln}:{"OK" if not bl else ",".join(bl[:2])}')
    print(f'dir {k:2d} ({ca:5.2f},{sa:5.2f}) ' + ' | '.join(res))
