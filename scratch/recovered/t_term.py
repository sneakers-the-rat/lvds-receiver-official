import sys
sys.path.insert(0, 'scratch/work/ax')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp252.kicad_pcb')
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == 'PHY_1V8A':
            pos = p.GetPosition()
            print('PAD', fp.GetReference(), 'pad', p.GetPadName(),
                  'at (%.3f, %.3f)' % (pos.x / 1e6, -pos.y / 1e6))
