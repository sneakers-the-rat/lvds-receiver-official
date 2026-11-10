import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard("hw/pdlvds_rx.exp82.kicad_pcb")
MM = pcbnew.ToMM
for ref in ("D9", "D10"):
    fp = b.FindFootprintByReference(ref)
    for p in fp.Pads():
        pos = p.GetPosition()
        print(f"{ref}.{p.GetNumber()} net={p.GetNetname()} at ({MM(pos.x):.2f},{MM(pos.y):.2f}) size=({MM(p.GetSize().x):.2f}x{MM(p.GetSize().y):.2f})")
n = 0
for z in b.Zones():
    if z.GetNetname() == "" and z.GetIsKeepout() if hasattr(z, 'GetIsKeepout') else z.GetNetname() == "":
        bb = z.GetBoundingBox()
        print(f"unnamed zone L{z.GetLayer()} keepout={z.GetIsKeepout() if hasattr(z,'GetIsKeepout') else '?'} bbox x[{MM(bb.GetLeft()):.1f},{MM(bb.GetRight()):.1f}] y[{MM(bb.GetTop()):.1f},{MM(bb.GetBottom()):.1f}] noTrack={z.GetDoNotAllowTracks()} noVia={z.GetDoNotAllowVias()} noPour={z.GetDoNotAllowZoneFills() if hasattr(z,'GetDoNotAllowZoneFills') else '?'}")
        n += 1
        if n >= 6: break
