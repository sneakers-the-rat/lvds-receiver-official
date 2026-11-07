import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp217.kicad_pcb')
for fp in b.GetFootprints():
    if fp.GetReference() == 'U7':
        for pad in fp.Pads():
            n = pad.GetNumber()
            if n.isdigit() and 20 <= int(n) <= 33:
                p = MM(pad.GetPosition())
                print(f'U7.{n} {pad.GetNetname()} ({p[0]:.3f},{p[1]:.3f})')
