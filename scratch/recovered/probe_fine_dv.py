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
MM, TM = pcbnew.FromMM, pcbnew.ToMM
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

for target in ('U10.7', 'U10.8'):
    net, (px, py), (hx, hy) = pads[target]
    w = 0.25
    print(f'== {target} {net} east escape, fine dv scan (ang 0):')
    for dv in (1.02, 1.05, 1.08, 1.10, 1.12, 1.15, 1.18, 1.22):
        vx, vy = px + dv, py
        ext = hx
        startd = max(ext - 0.08, 0.25 * ext)
        neck = pcbnew.SHAPE_SEGMENT(
            pcbnew.VECTOR2I(MM(px + startd), MM(py)),
            pcbnew.VECTOR2I(MM(vx), MM(vy)), MM(w))
        nb = blockers(net, neck, {pcbnew.F_Cu})
        disc = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(vx), MM(vy)),
                                    pcbnew.VECTOR2I(MM(vx), MM(vy)), MM(0.6))
        db = blockers(net, disc, ALL)
        print(f'   dv={dv:.2f} site=({vx:.2f},{vy:.2f}) neck={nb} disc={db}')
