import pcbnew, wx
_app = wx.App(False)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp276.kicad_pcb')
X0, X1, Y0, Y1 = 60.0, 74.0, 7.0, 17.0
def inside(x, y): return X0 <= x <= X1 and Y0 <= y <= Y1
print('--- F.Cu pads in box')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        pp = pad.GetPosition()
        if inside(pp.x/1e6, pp.y/1e6):
            print('PAD %-6s.%-2s %-9s (%.2f,%.2f) %.2fx%.2f' % (fp.GetReference(), pad.GetNumber(), pad.GetNetname(), pp.x/1e6, pp.y/1e6, pad.GetSize().x/1e6, pad.GetSize().y/1e6))
print('--- F.Cu tracks in box')
for t in b.GetTracks():
    if b.GetLayerName(t.GetLayer()) != 'F.Cu': continue
    s, e = t.GetStart(), t.GetEnd()
    if inside(s.x/1e6, s.y/1e6) or inside(e.x/1e6, e.y/1e6):
        kind = 'VIA' if t.Type() == pcbnew.PCB_VIA_T else 'TRK'
        print('%s %-9s w%.2f (%.2f,%.2f)-(%.2f,%.2f)' % (kind, t.GetNetname(), t.GetWidth()/1e6, s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6))
