import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard("hw/pdlvds_rx.exp82.kicad_pcb")
MM = pcbnew.ToMM
from collections import defaultdict
occ = defaultdict(list)
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition(); x, y = MM(p.x), MM(p.y)
        if -2 <= x <= 38 and -29 <= y <= -6:
            occ[t.GetNetname()].append(f"VIA({x:.1f},{y:.1f})")
    elif t.GetLayer() == pcbnew.In2_Cu:
        s, e = t.GetStart(), t.GetEnd()
        x1, y1, x2, y2 = MM(s.x), MM(s.y), MM(e.x), MM(e.y)
        if max(x1, x2) >= -2 and min(x1, x2) <= 38 and max(y1, y2) >= -29 and min(y1, y2) <= -6:
            occ[t.GetNetname()].append(f"({x1:.1f},{y1:.1f})->({x2:.1f},{y2:.1f})")
for net in sorted(occ):
    if net in ("HV_RAW", ""): continue
    print(net, len(occ[net]), occ[net][:14])
