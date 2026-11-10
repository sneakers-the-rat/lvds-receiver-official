import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.expanded.kicad_pcb')
zs = list(b.Zones())
print('zone count:', len(zs))
from collections import Counter
c = Counter()
for z in zs:
    for l in z.GetLayerSet().Seq():
        fp = z.GetFilledPolysList(l)
        n = fp.OutlineCount() if fp else 0
        c[(z.GetNetname(), pcbnew.LayerName(l))] += n
for k in sorted(c):
    print('  ', k, 'filled outlines:', c[k])
