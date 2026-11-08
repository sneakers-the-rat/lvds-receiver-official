"""t_aq43: move TP3 refdes (88.446,-22.973) -> (88.75,-19.55): its
glyphs were clipped by R16's GND pad mask opening. Silk-only move."""
import wx
_app = wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp236.kicad_pcb'
MM = pcbnew.FromMM
board = pcbnew.LoadBoard(SRC)
for fp in board.GetFootprints():
    if fp.GetReference() == 'TP3':
        fp.Reference().SetPosition(pcbnew.VECTOR2I(MM(88.75), MM(-19.55)))
        print('TP3 refdes -> (88.75,-19.55)')
board.Save(SRC)
print('saved', SRC)
