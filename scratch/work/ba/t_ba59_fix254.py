"""t_ba59: inspect + fix exp254's two STP joints.
Dump ULPI_STP B tracks with any endpoint in x[75.8,76.3]
y[13.2,13.8] (south joint) and y[16.4,17.0] (north joint).
Then: delete the 0.0707 dangling micro-segs at both spots
if they are spurs; add explicit B seg (76.05,13.55)->
(76.05,13.45) w0.2 at the south joint. Save as exp254
(in place via SaveBoard to same file after load)."""
import wx
_app = wx.App(False)
import pcbnew

F = 'hw/pdlvds_rx.exp254.kicad_pcb'
b = pcbnew.LoadBoard(F)
MM = pcbnew.FromMM


def mm(v):
    return v / 1e6


nc = b.GetNetcodeFromNetname('ULPI_STP')
for label, (y0, y1) in (('SOUTH', (13.2, 13.8)), ('NORTH', (16.4, 17.0))):
    print(f'--- {label} joint ---')
    for t in b.GetTracks():
        if t.GetNetCode() != nc or t.Type() != pcbnew.PCB_TRACE_T:
            continue
        if t.GetLayer() != pcbnew.B_Cu:
            continue
        s, e = t.GetStart(), t.GetEnd()
        sp = (round(mm(s.x), 3), round(mm(s.y), 3))
        ep = (round(mm(e.x), 3), round(mm(e.y), 3))
        if (75.8 <= sp[0] <= 76.3 and y0 <= sp[1] <= y1) or \
           (75.8 <= ep[0] <= 76.3 and y0 <= ep[1] <= y1):
            print(f'  seg {sp}->{ep} len {t.GetLength() / 1e6:.4f}')
print('=== done dump ===')
