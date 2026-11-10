import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp253.kicad_pcb')
def mm(v): return v / 1e6
nc = b.GetNetcodeFromNetname('ULPI_STP')
for t in b.GetTracks():
    if t.GetNetCode() != nc or t.Type() != pcbnew.PCB_TRACE_T:
        continue
    if t.GetLayer() != pcbnew.B_Cu:
        continue
    s, e = t.GetStart(), t.GetEnd()
    sp = (round(mm(s.x), 3), round(mm(s.y), 3))
    ep = (round(mm(e.x), 3), round(mm(e.y), 3))
    if (75.85 <= sp[0] <= 76.3 and 13.25 <= sp[1] <= 13.65) or \
       (75.85 <= ep[0] <= 76.3 and 13.25 <= ep[1] <= 13.65):
        print(f'  seg {sp}->{ep}')
print('--- north ---')
for t in b.GetTracks():
    if t.GetNetCode() != nc or t.Type() != pcbnew.PCB_TRACE_T:
        continue
    if t.GetLayer() != pcbnew.B_Cu:
        continue
    s, e = t.GetStart(), t.GetEnd()
    sp = (round(mm(s.x), 3), round(mm(s.y), 3))
    ep = (round(mm(e.x), 3), round(mm(e.y), 3))
    if (75.85 <= sp[0] <= 76.3 and 16.5 <= sp[1] <= 16.9) or \
       (75.85 <= ep[0] <= 76.3 and 16.5 <= ep[1] <= 16.9):
        print(f'  seg {sp}->{ep}')
