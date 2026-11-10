import sys
sys.path.insert(0, '/tmp/hw-prefix')
import wx
_app = wx.App(False)
import pcbnew
print('F_Cu', pcbnew.F_Cu, 'In1_Cu', pcbnew.In1_Cu, 'In2_Cu', pcbnew.In2_Cu, 'B_Cu', pcbnew.B_Cu)
import thread, thread_far
print('thread LAYERS', thread.LAYERS)
print('thread_far LAYERS', thread_far.LAYERS)
sys.path.insert(0, 'hw/tests')
from hand_stub import build_items
from test_thread_via_rip import make_board
board = make_board()
items = build_items(board)
res = thread_far.thread_one(board, items, 'TGT')
print('thread_far (both imported) ->', res)
for t in board.GetTracks():
    if t.GetNetname() == 'TGT' and t.Type() != pcbnew.PCB_VIA_T:
        print('  TGT track layer', t.GetLayer())
print('VIC left:', sum(1 for t in board.GetTracks() if t.GetNetname() == 'VIC'))
