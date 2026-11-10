import sys
sys.path.insert(0, '/tmp/hw-prefix')
import wx
_app = wx.App(False)
import pcbnew
import thread, thread_far
print('thread:', thread.__file__, 'rip_targets:', hasattr(thread, 'rip_targets'))
print('thread_far:', thread_far.__file__, 'rip_targets:', hasattr(thread_far, 'rip_targets'))
sys.path.insert(0, 'hw/tests')
from hand_stub import build_items
print('hand_stub:', sys.modules['hand_stub'].__file__)
from test_thread_via_rip import make_board
import thread as t2, thread_far as tf2
print('after test-module import:')
print('thread:', t2.__file__, 'rip_targets:', hasattr(t2, 'rip_targets'))
print('thread_far:', tf2.__file__, 'rip_targets:', hasattr(tf2, 'rip_targets'))
board = make_board()
items = build_items(board)
res = thread_far.thread_one(board, items, 'TGT')
print('thread_far ->', res)
print('VIC left:', sum(1 for t in board.GetTracks() if t.GetNetname() == 'VIC'))
