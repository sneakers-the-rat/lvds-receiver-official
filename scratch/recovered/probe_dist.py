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

mine = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(54.75), MMf(-13.40)),
                            pcbnew.VECTOR2I(MMf(56.80), MMf(-13.45)), MMf(0.2))
for t in b.GetTracks():
    if t.GetNetname() not in ('REFCLK', 'REFCLKN'):
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    if t.GetLayer() != 2:
        continue
    g = gap(mine, t.GetEffectiveShape())
    s, e = t.GetStart(), t.GetEnd()
    print(t.GetNetname(), 'In2',
          (round(MMt(s.x),2), round(MMt(s.y),2)), '->', (round(MMt(e.x),2), round(MMt(e.y),2)),
          'gap', None if g is None else round(g, 3))
