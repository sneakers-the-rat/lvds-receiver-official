import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM, TM = pcbnew.FromMM, pcbnew.ToMM
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}
F = {pcbnew.F_Cu}

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp14.kicad_pcb')
items = build_items(board)
pads = {}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        pads[f"{fp.GetReference()}.{pad.GetNumber()}"] = (
            pad.GetNetname(), pcbnew.ToMM(pad.GetPosition()),
            (pcbnew.ToMM(bb.GetWidth()) / 2, pcbnew.ToMM(bb.GetHeight()) / 2))

def seg(x1, y1, x2, y2, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x1), MM(y1)),
                                pcbnew.VECTOR2I(MM(x2), MM(y2)), MM(w))

def blockers(net, shape, layers, extra=()):
    out = []
    for kind, n2, l2, s2, desc in list(items) + list(extra):
        if n2 == net:
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001)):
            out.append((kind, n2, desc))
    return out

def scan(target, extra, label):
    net, (px, py), (hx, hy) = pads[target]
    print(f'== {label}: {target} {net}')
    found = []
    for dv in (1.0, 1.1, 1.2, 1.3, 1.45, 1.6):
        for k in range(16):
            a = k * math.pi / 8
            ca, sa = math.cos(a), math.sin(a)
            ext = min(hx / abs(ca) if ca else 1e9, hy / abs(sa) if sa else 1e9)
            startd = max(ext - 0.08, 0.25 * ext)
            sx, sy = px + startd * ca, py + startd * sa
            vx, vy = px + dv * ca, py + dv * sa
            nb = blockers(net, seg(sx, sy, vx, vy, 0.25), F, extra)
            if nb:
                continue
            db = blockers(net, seg(vx, vy, vx, vy, 0.6), ALL, extra)
            if db:
                continue
            found.append((dv, k * 22.5, vx, vy))
    for dv, ang, vx, vy in found:
        print(f'   CLEAR dv={dv} ang={ang} site=({vx:.2f},{vy:.2f})')
    if not found:
        print('   no clear neck+disc site in scan')
    return found

# hypothetical U10.7 escape at (17.20,-14.50): neck + via as items
n7, (x7, y7), (hx7, hy7) = pads['U10.7']
extra7 = [('track', 'HV_GATE', F, seg(x7 + hx7 - 0.08, y7, 17.20, -14.50, 0.25), 'hyp-neck'),
          ('via', 'HV_GATE', ALL, seg(17.20, -14.50, 17.20, -14.50, 0.6), 'hyp-via')]
scan('U10.8', extra7, 'U10.8 given U10.7 via placed')
# and with both 7+8 placed (8 at its due-east window site 17.23,-15.0
# is impossible pairwise; use first clear found above if any — here
# also test the symmetric case: 8 placed east, scan 7)
n8, (x8, y8), (hx8, hy8) = pads['U10.8']
extra8 = [('track', 'HV_INTVCC', F, seg(x8 + hx8 - 0.08, y8, 17.23, -15.00, 0.25), 'hyp-neck'),
          ('via', 'HV_INTVCC', ALL, seg(17.23, -15.00, 17.23, -15.00, 0.6), 'hyp-via')]
scan('U10.7', extra8, 'U10.7 given U10.8 via placed')
scan('U10.9', extra7 + extra8, 'U10.9 given both placed')
