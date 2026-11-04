import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
want = {}   # ref -> set of pad numbers or None=all
for spec in sys.argv[2].split(","):
    if "." in spec:
        r, p = spec.split(".", 1); want.setdefault(r, set()).add(p)
    else:
        want[spec] = None
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if ref not in want: continue
    pos = fp.GetPosition()
    print(f"== {ref} at ({pcbnew.ToMM(pos.x):.2f},{pcbnew.ToMM(pos.y):.2f}) rot={fp.GetOrientationDegrees():.0f}")
    for pad in fp.Pads():
        if want[ref] is not None and pad.GetNumber() not in want[ref]: continue
        pp = pad.GetPosition(); sz = pad.GetSize()
        layers = [l for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if pad.IsOnLayer(l)]
        lname = {0:'F',1:'In1',2:'In2',31:'B'}
        print(f"   {ref}.{pad.GetNumber():>3s} net={pad.GetNetname():12s} at ({pcbnew.ToMM(pp.x):6.2f},{pcbnew.ToMM(pp.y):6.2f}) size {pcbnew.ToMM(sz.x):.2f}x{pcbnew.ToMM(sz.y):.2f} layers={[lname.get(l,l) for l in layers]} drill={pcbnew.ToMM(pad.GetDrillSize().x):.2f}")
