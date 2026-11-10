import wx
_app = wx.App(False)
import pcbnew
F = 'hw/pdlvds_rx.exp254.kicad_pcb'
b = pcbnew.LoadBoard(F)
MM = pcbnew.FromMM
def mm(v): return v / 1e6
nc = b.GetNetcodeFromNetname('ULPI_STP')
kill = []
for t in b.GetTracks():
    if t.GetNetCode() != nc or t.Type() != pcbnew.PCB_TRACE_T:
        continue
    s, e = t.GetStart(), t.GetEnd()
    sp = (round(mm(s.x), 2), round(mm(s.y), 2))
    ep = (round(mm(e.x), 2), round(mm(e.y), 2))
    if (sp == (76.05, 16.7) and ep == (76.05, 13.45)) or \
       (sp == (76.05, 13.45) and ep == (76.05, 16.7)):
        kill.append(t)
print('straight seg found:', len(kill))
for t in kill:
    b.Remove(t)
def seg(a, bb):
    t = pcbnew.PCB_TRACK(b)
    t.SetNetCode(nc)
    t.SetLayer(pcbnew.B_Cu)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(bb[0]), MM(bb[1])))
    t.SetWidth(MM(0.2))
    b.Add(t)
seg((76.05, 16.7), (76.35, 15.6))
seg((76.35, 15.6), (76.35, 13.9))
seg((76.35, 13.9), (76.05, 13.45))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(F)
print('saved')
