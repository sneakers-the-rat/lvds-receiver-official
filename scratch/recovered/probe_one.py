import sys
HW = '/tmp/hw-prefix'
sys.path.insert(0, HW)
sys.path.insert(0, 'hw/tests')
import wx
_app = wx.App(False)
import importlib
mod = importlib.import_module(sys.argv[1])
print('module file:', mod.__file__)
print('has rip_targets (fixed code):', hasattr(mod, 'rip_targets'))
from hand_stub import build_items
from test_thread_via_rip import make_board
board = make_board()
items = build_items(board)
res = mod.thread_one(board, items, 'TGT')
print(sys.argv[1], '->', res)
print('VIC tracks left:', sum(1 for t in board.GetTracks() if t.GetNetname() == 'VIC'))
