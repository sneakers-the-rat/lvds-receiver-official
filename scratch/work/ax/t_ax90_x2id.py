import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp248.kicad_pcb')
for fp in b.GetFootprints():
    p = fp.GetPosition()
    x, y = p.x / 1e6, p.y / 1e6
    if 69 < x < 76 and 33 < y < 40:
        print(fp.GetReference(), fp.GetFPID().GetLibItemName(),
              f'({x:.2f},{y:.2f}) rot {fp.GetOrientationDegrees()}',
              'courtyard?', flush=True)
        for pad in fp.Pads():
            pp = pad.GetPosition()
            print(f"   pad {pad.GetNumber()} {pad.GetNetname()} "
                  f"({pp.x / 1e6:.3f},{pp.y / 1e6:.3f}) "
                  f"sz {pad.GetSize().x / 1e6:.2f}x"
                  f"{pad.GetSize().y / 1e6:.2f}", flush=True)
        bb = fp.GetCourtyard(0).BBox() if False else None
