import sys
sys.path.insert(0, 'hw')
import wx
_a = wx.App(False)
import pcbnew, check_pcb, repair6
from hand_stub import build_items
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
MM = pcbnew.FromMM
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}
b = pcbnew.LoadBoard('hw/pdlvds_rx.fr18.kicad_pcb')
items = build_items(b)
d15 = [s for k, n, l, s, d in items if d == 'D1.5'][0]

def seg(x1, y1, x2, y2, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x1), MM(y1)),
                                pcbnew.VECTOR2I(MM(x2), MM(y2)), MM(w))

def gap_to_d15(shape):
    lo, hi = 0.0, 2.0
    for _ in range(20):
        mid = (lo + hi) / 2
        if shape.Collide(d15, MM(mid)):
            hi = mid
        else:
            lo = mid
    return hi

def blockers(net, shape, layers, allow=()):
    out = []
    for kind, n2, l2, s2, d2 in items:
        if n2 == net or d2 in allow:
            continue
        shared = layers & l2
        if not shared:
            continue
        need = check_pcb.need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001)):
            out.append(d2)
    return out

best = None
for vx in (9.9, 10.05, 10.2, 10.35, 10.5):
    for vy in (41.9, 42.05, 42.2, 42.4, 42.6, 42.9):
        for (sx, sy) in ((9.15, 41.4), (9.0, 41.38), (9.3, 41.4),
                         (8.85, 41.35), (9.45, 41.38)):
            s = seg(sx, sy, vx, vy, 0.25)
            if blockers('APD_A', s, {pcbnew.F_Cu}, allow=('D1.5',)):
                continue
            dv = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(vx), MM(vy)),
                                      pcbnew.VECTOR2I(MM(vx), MM(vy)),
                                      MM(0.6))
            if blockers('APD_A', dv, ALL):
                continue
            g = gap_to_d15(s)
            if best is None or g > best[0]:
                best = (g, sx, sy, vx, vy)
print('best D1.4 candidate (gap to D1.5, start, via):', best)
if best:
    g, sx, sy, vx, vy = best
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(MM(sx), MM(sy)))
    t.SetEnd(pcbnew.VECTOR2I(MM(vx), MM(vy)))
    t.SetWidth(MM(0.25)); t.SetLayer(pcbnew.F_Cu)
    t.SetNet(b.FindNet('APD_A')); b.Add(t)
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy)))
    v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3))
    v.SetNet(b.FindNet('APD_A')); b.Add(v)
    items = build_items(b)
    for (ex, ey) in ((9.0, 43.4), (10.9, 43.4), (vx, 44.4), (8.4, 42.8)):
        if not blockers('APD_A', seg(vx, vy, ex, ey, 0.25),
                        {pcbnew.In2_Cu}):
            t2 = pcbnew.PCB_TRACK(b)
            t2.SetStart(pcbnew.VECTOR2I(MM(vx), MM(vy)))
            t2.SetEnd(pcbnew.VECTOR2I(MM(ex), MM(ey)))
            t2.SetWidth(MM(0.25)); t2.SetLayer(pcbnew.In2_Cu)
            t2.SetNet(b.FindNet('APD_A')); b.Add(t2)
            print('tail ->', (ex, ey))
            break
    repair6.save_checkpoint(b, 'hw/pdlvds_rx.fr18.kicad_pcb')
    print('saved fr18 with D1.4 escape')
