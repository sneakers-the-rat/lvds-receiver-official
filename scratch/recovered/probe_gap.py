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

for (a, c) in [((54.75, -13.40), (55.30, -14.50)),
               ((54.75, -13.40), (55.62, -14.12)),
               ((54.75, -13.30), (55.30, -14.50))]:
    mine = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(a[0]), MMf(a[1])),
                                pcbnew.VECTOR2I(MMf(c[0]), MMf(c[1])), MMf(0.2))
    print('seg', a, '->', c)
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() != 2:
            continue
        bb = t.GetBoundingBox()
        if pcbnew.ToMM(bb.GetRight()) < 54.0 or pcbnew.ToMM(bb.GetLeft()) > 56.2:
            continue
        if pcbnew.ToMM(bb.GetBottom()) < -15.2 or pcbnew.ToMM(bb.GetTop()) > -12.9:
            continue
        g = gap(mine, t.GetEffectiveShape())
        s, e = t.GetStart(), t.GetEnd()
        print('   ', t.GetNetname(), (round(MMt(s.x),2), round(MMt(s.y),2)), '->',
              (round(MMt(e.x),2), round(MMt(e.y),2)), 'gap', None if g is None else round(g,3))
