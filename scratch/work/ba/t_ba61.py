import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp254.kicad_pcb')
def mm(v): return v / 1e6
nc = b.GetNetcodeFromNetname('ULPI_STP')
print('--- all STP B segs, centres x[75.7,76.35] y[13.0,14.0] ---')
for t in b.GetTracks():
    if t.GetNetCode() != nc or t.Type() != pcbnew.PCB_TRACE_T:
        continue
    if t.GetLayer() != pcbnew.B_Cu:
        continue
    s, e = t.GetStart(), t.GetEnd()
    sp = (round(mm(s.x), 3), round(mm(s.y), 3))
    ep = (round(mm(e.x), 3), round(mm(e.y), 3))
    cx, cy = (sp[0] + ep[0]) / 2, (sp[1] + ep[1]) / 2
    if 75.7 <= cx <= 76.35 and 13.0 <= cy <= 14.0:
        print(f'  seg {sp}->{ep}')
