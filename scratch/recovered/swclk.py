import sys, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp221.kicad_pcb')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() == 'SWCLK':
            p = pcbnew.ToMM(pad.GetPosition())
            print(f'{fp.GetReference()}.{pad.GetNumber()} SWCLK ({p[0]:.3f},{p[1]:.3f})')
