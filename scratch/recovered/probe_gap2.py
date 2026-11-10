import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MMf = pcbnew.FromMM
MMt = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp91.kicad_pcb')

def gap(s1, s2):
    if s1.Collide(s2, MMf(0.0)):
        return 0.0
    lo, hi = 0.0, 3.0
    if not s1.Collide(s2, MMf(hi)):
        return None
    for _ in range(16):
        mid = (lo + hi) / 2
        if s1.Collide(s2, MMf(mid)):
            hi = mid
        else:
            lo = mid
    return lo

mine = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(55.70), MMf(-15.30)),
                            pcbnew.VECTOR2I(MMf(58.00), MMf(-15.35)), MMf(0.2))
for t in b.GetTracks():
    if t.GetLayer() != 2:
        continue
    bb = t.GetBoundingBox()
    if pcbnew.ToMM(bb.GetRight()) < 55.0 or pcbnew.ToMM(bb.GetLeft()) > 58.6:
        continue
    if pcbnew.ToMM(bb.GetBottom()) < -16.4 or pcbnew.ToMM(bb.GetTop()) > -14.4:
        continue
    g = gap(mine, t.GetEffectiveShape())
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        print('VIA', t.GetNetname(), (round(MMt(p.x),2), round(MMt(p.y),2)), 'gap', None if g is None else round(g,3))
    else:
        s, e = t.GetStart(), t.GetEnd()
        print('TRK', t.GetNetname(), (round(MMt(s.x),2), round(MMt(s.y),2)), '->',
              (round(MMt(e.x),2), round(MMt(e.y),2)), 'gap', None if g is None else round(g,3))
