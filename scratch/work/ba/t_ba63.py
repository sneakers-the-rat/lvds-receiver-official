import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp254.kicad_pcb')
def mm(v): return v / 1e6
nc = b.GetNetcodeFromNetname('GND')
print('--- GND B items centres x[74.3,76.7] y[13.8,15.6] ---')
for t in b.GetTracks():
    if t.GetNetCode() != nc:
        continue
    if t.GetLayer() != pcbnew.B_Cu:
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        print(f'  via ({mm(p.x):.2f},{mm(p.y):.2f}) d{mm(t.GetWidth()):.2f}')
        continue
    s, e = t.GetStart(), t.GetEnd()
    sp = (round(mm(s.x), 2), round(mm(s.y), 2))
    ep = (round(mm(e.x), 2), round(mm(e.y), 2))
    cx, cy = (sp[0] + ep[0]) / 2, (sp[1] + ep[1]) / 2
    if 74.3 <= cx <= 76.7 and 13.8 <= cy <= 15.6:
        print(f'  seg {sp}->{ep} w{mm(t.GetWidth()):.2f}')
