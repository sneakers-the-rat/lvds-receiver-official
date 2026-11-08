import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard("scratch/work/ah/rip2.kicad_pcb")
LN = {pcbnew.F_Cu:'F', pcbnew.In2_Cu:'In2', pcbnew.B_Cu:'B'}
def mm(v): return round(v/1e6,3)
for fp in b.GetFootprints():
    for pad in fp.Pads():
        x,y = mm(pad.GetPosition().x), mm(pad.GetPosition().y)
        if 63.5 < x < 72.5 and 11.0 < y < 17.5:
            s = pcbnew.ToMM(pad.GetSize())
            print(f"PAD {fp.GetReference()}.{pad.GetNumber()} [{pad.GetNetname()}] ({x},{y}) {round(s[0],2)}x{round(s[1],2)}")
for t in b.GetTracks():
    a = (mm(t.GetStart().x), mm(t.GetStart().y)); c = (mm(t.GetEnd().x), mm(t.GetEnd().y))
    cx, cy = (a[0]+c[0])/2, (a[1]+c[1])/2
    if t.Type() == pcbnew.PCB_VIA_T:
        if 63.5 < a[0] < 72.5 and 11.0 < a[1] < 17.5:
            print(f"via [{t.GetNetname()}] ({a[0]},{a[1]}) d{mm(t.GetWidth())}")
    elif 63.5 < cx < 72.5 and 11.0 < cy < 17.5 and t.GetLayer() in LN:
        print(f"{LN[t.GetLayer()]} [{t.GetNetname()}] {a}->{c} w{mm(t.GetWidth())}")
