import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp83.kicad_pcb')
for t in b.GetTracks():
    if t.GetNetname() == 'SET_P':
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            print('VIA SET_P', round(pcbnew.ToMM(p.x),3), round(pcbnew.ToMM(p.y),3))
        else:
            s, e = t.GetStart(), t.GetEnd()
            print('TRK SET_P L', t.GetLayer(), 'w', round(pcbnew.ToMM(t.GetWidth()),2),
                  (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
                  (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))
fp = b.FindFootprintByReference('U13')
for pad in fp.Pads():
    if pad.GetNumber() == '11':
        print('U13.11 size', round(pcbnew.ToMM(pad.GetSize().x),2), round(pcbnew.ToMM(pad.GetSize().y),2))
