import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp83.kicad_pcb')
fp = b.FindFootprintByReference('U13')
p = fp.GetPosition()
print('U13 at', round(pcbnew.ToMM(p.x),3), round(pcbnew.ToMM(p.y),3), 'rot', fp.GetOrientationDegrees())
nets = {}
for pad in fp.Pads():
    pp = pad.GetPosition()
    nets.setdefault(pad.GetNetname(), []).append((pad.GetNumber(), round(pcbnew.ToMM(pp.x),2), round(pcbnew.ToMM(pp.y),2)))
for n, ps in sorted(nets.items()):
    print(n, ps)
