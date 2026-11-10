import sys
sys.path.insert(0, 'scratch/work/ax')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp252.kicad_pcb')
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == 'ULPI_STP':
            pos = p.GetPosition()
            print('PAD', fp.GetReference(), p.GetPadName(),
                  'at (%.3f, %.3f)' % (pos.x / 1e6, -pos.y / 1e6))
# STP southern items: vias with y<8
for t in b.GetTracks():
    if t.GetNetname() == 'ULPI_STP' and t.Type() == pcbnew.PCB_VIA_T:
        pos = t.GetPosition()
        print('VIA at (%.2f, %.2f)' % (pos.x / 1e6, -pos.y / 1e6))
