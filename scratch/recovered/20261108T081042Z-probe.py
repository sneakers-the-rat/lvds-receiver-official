import wx
_app = wx.App(False)
import pcbnew
print([n for n in dir(pcbnew) if 'SHAPE' in n or 'TEXT' in n][:40])
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp229.kicad_pcb')
for fp in b.GetFootprints():
    if fp.GetReference() == 'SH1':
        for gi in fp.GraphicalItems():
            print(type(gi), type(gi).__name__)
        break
