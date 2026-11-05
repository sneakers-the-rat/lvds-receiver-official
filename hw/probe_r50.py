import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MMt = pcbnew.ToMM
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp51.kicad_pcb')
for ref in ('U10', 'C30'):
    fp = board.FindFootprintByReference(ref)
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        print(f'{ref}.{p.GetNumber()} {p.GetNetname()} '
              f'c=({MMt(p.GetPosition().x):.2f},'
              f'{MMt(p.GetPosition().y):.2f}) '
              f'bbox x[{MMt(bb.GetX()):.2f},{MMt(bb.GetRight()):.2f}] '
              f'y[{MMt(bb.GetY()):.2f},{MMt(bb.GetBottom()):.2f}]')
