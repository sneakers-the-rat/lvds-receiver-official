import sys, wx
_app = wx.App(False)
import pcbnew
for path in sys.argv[1:]:
    b = pcbnew.LoadBoard(path)
    print("==", path)
    for t in b.GetTracks():
        if t.GetNetname() != "HV_RAW": continue
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition(); print(f"  VIA ({pcbnew.ToMM(p.x):.2f},{pcbnew.ToMM(p.y):.2f})")
        else:
            s, e = t.GetStart(), t.GetEnd()
            print(f"  TRK L{t.GetLayer()} ({pcbnew.ToMM(s.x):.2f},{pcbnew.ToMM(s.y):.2f})->({pcbnew.ToMM(e.x):.2f},{pcbnew.ToMM(e.y):.2f}) w={pcbnew.ToMM(t.GetWidth()):.2f}")
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == "HV_RAW":
                p = pad.GetPosition(); print(f"  PAD {fp.GetReference()}.{pad.GetNumber()} ({pcbnew.ToMM(p.x):.2f},{pcbnew.ToMM(p.y):.2f})")
