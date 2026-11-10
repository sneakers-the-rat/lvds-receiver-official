import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp82.kicad_pcb')
want = {('U4','7'), ('C13','2'), ('U13','7'), ('U4','12'), ('U4','1')}
for fp in b.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        if (ref, pad.GetNumber()) in want:
            p = pad.GetPosition()
            print(ref, pad.GetNumber(), pad.GetNetname(), round(pcbnew.ToMM(p.x),3), round(pcbnew.ToMM(p.y),3), 'size', round(pcbnew.ToMM(pad.GetSize().x),2), round(pcbnew.ToMM(pad.GetSize().y),2), 'layers', pad.GetLayerSet().FmtHex() if hasattr(pad.GetLayerSet(),'FmtHex') else '')
