import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp93.kicad_pcb')
from collections import Counter
c = Counter()
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        c['via'] += 1
    else:
        c[t.GetLayer()] += 1
print('track counts by layer:', dict(c))
print('zones:')
for z in b.Zones():
    print('  ', z.GetNetname(), 'layer', z.GetLayer())
print('stackup layers:', [b.GetLayerName(i) for i in range(4)])
