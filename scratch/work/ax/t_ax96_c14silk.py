import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp249.kicad_pcb')
for fp in b.GetFootprints():
    if fp.GetReference() == 'C14':
        ref = fp.Reference()
        print('refdes at', ref.GetPosition().x / 1e6,
              ref.GetPosition().y / 1e6, flush=True)
        ref.SetPosition(pcbnew.VECTOR2I(int(76.9 * 1e6),
                                        int(35.8 * 1e6)))
        print('refdes moved to (76.9,35.8)', flush=True)
b.Save('hw/pdlvds_rx.exp249.kicad_pcb')
print('saved', flush=True)
