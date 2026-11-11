import pcbnew
_app = pcbnew.wx.App(False) if hasattr(pcbnew, 'wx') else None
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp275.kicad_pcb')
for ref in ('D8', 'R46', 'D7', 'R45'):
    fp = b.FindFootprintByReference(ref)
    if not fp:
        print(ref, 'NOT FOUND'); continue
    p = fp.GetPosition()
    print(ref, 'at (%.2f, %.2f) rot %.0f fp=%s' % (p.x/1e6, p.y/1e6, fp.GetOrientationDegrees(), fp.GetFPID().GetLibItemName()))
    for pad in fp.Pads():
        pp = pad.GetPosition()
        print('   pad %s net %-10s at (%.2f, %.2f) size %.2f x %.2f' % (
            pad.GetNumber(), pad.GetNetname(), pp.x/1e6, pp.y/1e6, pad.GetSize().x/1e6, pad.GetSize().y/1e6))
# tracks touching D8's nets nearby
for t in b.GetTracks():
    if t.GetNetname() in ('BIST_A', 'BIST_DRV'):
        s, e = t.GetStart(), t.GetEnd()
        print('TRK %-8s L%-4s w%.2f (%.2f,%.2f)-(%.2f,%.2f)' % (t.GetNetname(), b.GetLayerName(t.GetLayer()), t.GetWidth()/1e6, s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6))
