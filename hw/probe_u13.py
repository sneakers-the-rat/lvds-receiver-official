import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MMt = pcbnew.ToMM
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp42.kicad_pcb')
for ref in ('U13', 'U7'):
    fp = board.FindFootprintByReference(ref)
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        print(f'{ref}.{p.GetNumber()} {p.GetNetname()} bbox x[{MMt(bb.GetX()):.2f},{MMt(bb.GetRight()):.2f}] y[{MMt(bb.GetY()):.2f},{MMt(bb.GetBottom()):.2f}]')
