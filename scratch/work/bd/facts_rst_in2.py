import wx
wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp257.kicad_pcb')
print('--- In2 items in corridor x[72.6,76.4] y[3.8,19.6]')
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == pcbnew.In2_Cu:
        s, e = t.GetStart(), t.GetEnd()
        pts = [(s.x/1e6, s.y/1e6), (e.x/1e6, e.y/1e6)]
        if all(72.6 < p[0] < 76.4 and 3.8 < p[1] < 19.6 for p in pts):
            print(f"  In2 {t.GetNetname():10s} ({pts[0][0]:.3f},{pts[0][1]:.3f})-({pts[1][0]:.3f},{pts[1][1]:.3f}) w={t.GetWidth()/1e6}")
print('--- In2 items with any endpoint in wider box x[70,78] y[3,21], net summary')
from collections import Counter
c = Counter()
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == pcbnew.In2_Cu:
        s, e = t.GetStart(), t.GetEnd()
        for p in [(s.x/1e6, s.y/1e6), (e.x/1e6, e.y/1e6)]:
            if 70 < p[0] < 78 and 3 < p[1] < 21:
                c[t.GetNetname()] += 1
                break
for n, k in c.most_common():
    print(f"  {n}: {k} segs")
