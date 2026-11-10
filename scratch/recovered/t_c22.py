import sys
sys.path.insert(0, 'scratch/work/ax')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp252.kicad_pcb')
for fp in b.GetFootprints():
    if fp.GetReference() in ('C22', 'C20', 'C23'):
        print(fp.GetReference(), 'value:', fp.GetValue(), 'fp:', fp.GetFPID().GetLibItemName())
        for p in fp.Pads():
            pos = p.GetPosition()
            print('   pad', p.GetPadName(), 'net', p.GetNetname(),
                  'at (%.3f, %.3f)' % (pos.x / 1e6, -pos.y / 1e6))
