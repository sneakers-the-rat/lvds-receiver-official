import pcbnew, wx
from collections import Counter
_app = wx.App(False)
b = pcbnew.LoadBoard('hw/pdlvds_rx.kicad_pcb')
for net in ('DM_PHY', 'DP_PHY'):
    c = Counter()
    for t in b.GetTracks():
        if t.GetNetname() == net and t.Type() != pcbnew.PCB_VIA_T:
            c[(b.GetLayerName(t.GetLayer()), round(t.GetWidth()/1e6, 3))] += 1
    print(net, dict(c))
