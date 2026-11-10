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

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp14.kicad_pcb')
items = build_items(board)

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
            out.append((kind, n2, desc))
    return out

def disc(x, y):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x), MM(y)),
                                pcbnew.VECTOR2I(MM(x), MM(y)), MM(0.6))

print('--- U10.7 HV_GATE disc site (17.30,-14.50), all layers:')
for b in blockers('HV_GATE', disc(17.30, -14.50), ALL):
    print('   ', b)
print('--- U10.8 HV_INTVCC disc site (17.30,-15.00), all layers:')
for b in blockers('HV_INTVCC', disc(17.30, -15.00), ALL):
    print('   ', b)
print('--- U10.3 HV_SS disc site west (10.55,-15.00), all layers:')
for b in blockers('HV_SS', disc(10.55, -15.00), ALL):
    print('   ', b)

# board-side: +5V tracks near the two east disc sites
print('--- +5V tracks/vias with bbox within 1.2 mm of (17.3,-14.75):')
for t in board.GetTracks():
    if t.GetNetname() != '+5V':
        continue
    bb = t.GetBoundingBox()
    cx, cy = TM(bb.GetCenter().x), TM(bb.GetCenter().y)
    if abs(cx - 17.3) < 1.6 and abs(cy + 14.75) < 1.6:
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            print(f'    VIA @({TM(p.x):.3f},{TM(p.y):.3f})')
        else:
            s, e = t.GetStart(), t.GetEnd()
            print(f'    TRK L{t.GetLayer()} ({TM(s.x):.3f},{TM(s.y):.3f})'
                  f'->({TM(e.x):.3f},{TM(e.y):.3f}) w={TM(t.GetWidth()):.2f}')
