import pcbnew, wx
_app = wx.App(False)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp276.kicad_pcb')
X0, X1, Y0, Y1 = 58.0, 76.0, 4.0, 21.0
def inside(x, y): return X0 <= x <= X1 and Y0 <= y <= Y1
for fp in b.GetFootprints():
    p = fp.GetPosition()
    if inside(p.x/1e6, p.y/1e6):
        print('FP %-6s at (%.2f, %.2f) rot %.0f' % (fp.GetReference(), p.x/1e6, p.y/1e6, fp.GetOrientationDegrees()))
for t in b.GetTracks():
    s, e = t.GetStart(), t.GetEnd()
    if inside(s.x/1e6, s.y/1e6) or inside(e.x/1e6, e.y/1e6):
        kind = 'VIA' if t.Type() == pcbnew.PCB_VIA_T else 'TRK'
        print('%s %-9s L%-5s w%.2f (%.2f,%.2f)-(%.2f,%.2f)' % (kind, t.GetNetname(), b.GetLayerName(t.GetLayer()), t.GetWidth()/1e6, s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6))
