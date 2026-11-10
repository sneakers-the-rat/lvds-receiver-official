"""t_ba64: re-make STP's through-connection compactly.
Delete the wrong seg (76.0,13.55)->(76.05,13.45).
Add ONE B seg (76.05,16.7)->(76.05,13.45) w0.2 joining the
legs chain end to the descent head point, straight through
the freed corridor. Zone refill, save exp254."""
import wx
_app = wx.App(False)
import pcbnew

F = 'hw/pdlvds_rx.exp254.kicad_pcb'
b = pcbnew.LoadBoard(F)
MM = pcbnew.FromMM


def mm(v):
    return v / 1e6


nc = b.GetNetcodeFromNetname('ULPI_STP')
kill = []
for t in b.GetTracks():
    if t.GetNetCode() != nc or t.Type() != pcbnew.PCB_TRACE_T:
        continue
    if t.GetLayer() != pcbnew.B_Cu:
        continue
    s, e = t.GetStart(), t.GetEnd()
    sp = (round(mm(s.x), 2), round(mm(s.y), 2))
    ep = (round(mm(e.x), 2), round(mm(e.y), 2))
    if (sp == (76.0, 13.55) and ep == (76.05, 13.45)) or \
       (sp == (76.05, 13.45) and ep == (76.0, 13.55)):
        kill.append(t)
print('wrong seg found:', len(kill))
for t in kill:
    b.Remove(t)

t = pcbnew.PCB_TRACK(b)
t.SetNetCode(nc)
t.SetLayer(pcbnew.B_Cu)
t.SetStart(pcbnew.VECTOR2I(MM(76.05), MM(16.7)))
t.SetEnd(pcbnew.VECTOR2I(MM(76.05), MM(13.45)))
t.SetWidth(MM(0.2))
b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(F)
print('saved', F)
print('=== done ===')
