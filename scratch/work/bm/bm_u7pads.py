import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp262.kicad_pcb')
for fp in b.GetFootprints():
    if fp.GetReference() == 'U7':
        print('U7 at', fp.GetPosition().x/1e6, fp.GetPosition().y/1e6, 'rot', fp.GetOrientationDegrees())
        for p in fp.Pads():
            sz = p.GetSize()
            print(f"  pad {p.GetNumber()} net={p.GetNetname() or '<none>'} "
                  f"({p.GetPosition().x/1e6:.3f},{p.GetPosition().y/1e6:.3f}) "
                  f"{sz.x/1e6:.2f}x{sz.y/1e6:.2f} drill={p.GetDrillSize().x/1e6:.2f}")
