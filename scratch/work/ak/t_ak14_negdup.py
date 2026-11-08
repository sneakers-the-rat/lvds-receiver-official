"""t_ak14: delete ONE of the two identical co-located NEG_RAW vias
at (24.875,48.875) (both d0.80/drill0.40 -- a stacked duplicate,
the groute defect class). Keeps uuid 78ed5848..., removes
7c70d28b... . Usage: t_ak14_negdup.py in out"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
n = 0
for t in list(board.GetTracks()):
    if isinstance(t, pcbnew.PCB_VIA) and \
            t.m_Uuid.AsString() == '7c70d28b-f9ae-43e9-80f6-3fa5139b2c34':
        x, y = pcbnew.ToMM(t.GetPosition())
        assert abs(x - 24.875) < 0.01 and abs(y - 48.875) < 0.01
        assert t.GetNetname() == 'NEG_RAW'
        board.Remove(t)
        n += 1
print(f'removed {n} via(s)')
board.Save(sys.argv[2])
