import sys
sys.path.insert(0, '/tmp/hw-prefix')
sys.path.insert(0, '/tmp')
import wx
_app = wx.App(False)
import thread_far_dbg as mod
print('module file:', mod.__file__, '| rip_targets:', hasattr(mod, 'rip_targets'))
sys.path.insert(0, 'hw/tests')
from hand_stub import build_items
from test_thread_via_rip import make_board
board = make_board()
items = build_items(board)
print('VIC item layers:', [it[2] for it in items if it[1] == 'VIC'])
res = mod.thread_one(board, items, 'TGT')
print('->', res)
print('VIC left:', sum(1 for t in board.GetTracks() if t.GetNetname() == 'VIC'))
