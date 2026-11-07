import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp211.kicad_pcb')
MM = pcbnew.ToMM
for net in ('CDR_SQUELCH', 'XI', 'GND'):
    print(f"== {net} (district only) ==")
    for t in b.GetTracks():
        if t.GetNetname() != net: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            if 70 <= MM(p.x) <= 82 and 12 <= MM(p.y) <= 24:
                print(f"  VIA ({MM(p.x):.3f},{MM(p.y):.3f}) d={MM(t.GetWidth()):.3f}")
        else:
            s, e = t.GetStart(), t.GetEnd()
            if (70 <= MM(s.x) <= 82 and 12 <= MM(s.y) <= 24) or (70 <= MM(e.x) <= 82 and 12 <= MM(e.y) <= 24):
                print(f"  TRK {b.GetLayerName(t.GetLayer())} w={MM(t.GetWidth()):.3f} ({MM(s.x):.3f},{MM(s.y):.3f})->({MM(e.x):.3f},{MM(e.y):.3f})")
for fp in b.GetFootprints():
    if fp.GetReference() in ('C20', 'U5'):
        p = fp.GetPosition()
        print(f"FP {fp.GetReference()} pos=({MM(p.x):.3f},{MM(p.y):.3f}) rot={fp.GetOrientationDegrees():.0f}")
        for pad in fp.Pads():
            q = pad.GetPosition(); sz = pad.GetSize()
            print(f"  PAD {pad.GetNetname()} {fp.GetReference()}.{pad.GetNumber()} ({MM(q.x):.3f},{MM(q.y):.3f}) {MM(sz.x):.3f}x{MM(sz.y):.3f} drill={MM(pad.GetDrillSize().x):.3f}")
