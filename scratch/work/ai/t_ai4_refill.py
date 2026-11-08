"""t_ai4: refill all zones on a board copy and save (in place)."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(sys.argv[1])
print('refilled + saved', sys.argv[1])
