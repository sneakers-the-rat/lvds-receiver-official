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

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp14.kicad_pcb')
items = build_items(board)
pads = {}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        pads[f"{fp.GetReference()}.{pad.GetNumber()}"] = (
            pad.GetNetname(), pcbnew.ToMM(pad.GetPosition()),
            (pcbnew.ToMM(bb.GetWidth()) / 2, pcbnew.ToMM(bb.GetHeight()) / 2))

def blockers(net, shape, layers):
    out = []
    for kind, n2, l2, s2, desc in items:
        if n2 == net:
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001)):
            out.append((kind, n2))
    return out

for target in ('U10.3', 'U10.7', 'U10.8', 'U10.9'):
    net, (px, py), (hx, hy) = pads[target]
    width, clr = netclass(net)
    w = min(width, 0.25)
    print(f'== {target} {net} pos=({px:.2f},{py:.2f}) half=({hx:.2f},{hy:.2f})')
    results = []
    for dv in (0.55, 0.7, 0.85, 1.0, 1.15, 1.3, 1.5):
        for k in range(16):
            a = k * math.pi / 8
            ca, sa = math.cos(a), math.sin(a)
            ext = min(hx / abs(ca) if ca else 1e9, hy / abs(sa) if sa else 1e9)
            startd = max(ext - 0.08, 0.25 * ext)
            sx, sy = px + startd * ca, py + startd * sa
            vx, vy = px + dv * ca, py + dv * sa
            neck = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(sx), MM(sy)),
                                        pcbnew.VECTOR2I(MM(vx), MM(vy)), MM(w))
            nb = blockers(net, neck, {pcbnew.F_Cu})
            if nb:
                results.append((len(nb), dv, k * 22.5, 'neck', nb))
                continue
            disc = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(vx), MM(vy)),
                                        pcbnew.VECTOR2I(MM(vx), MM(vy)), MM(0.6))
            db = blockers(net, disc, ALL)
            if db:
                results.append((len(db), dv, k * 22.5, 'disc', db))
            else:
                results.append((0, dv, k * 22.5, 'CLEAR', []))
    results.sort(key=lambda r: (r[0], r[1]))
    for cnt, dv, ang, stage, bl in results[:6]:
        kinds = {}
        for kind, n2 in bl:
            kinds.setdefault(n2, []).append(kind)
        print(f'   dv={dv} ang={ang:5.1f} {stage:4s} blockers={cnt} {kinds}')
