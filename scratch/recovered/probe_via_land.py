import sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'hw/tests')
import wx
_app = wx.App(False)
import pcbnew
import thread_far
from hand_stub import build_items
from test_thread_via_rip import make_board
TM = pcbnew.ToMM

board = make_board()
items = build_items(board)
for (x, y) in [(20.0, 20.0), (20.0, 20.5), (19.5, 20.5), (20.5, 20.5),
               (20.0, 21.0), (19.0, 20.5), (21.0, 20.5)]:
    bl = thread_far.via_blockers(items, 'TGT', x, y)
    print(f'via_blockers at ({x},{y}):',
          [(items[i][0], items[i][1]) for i in bl])
res = thread_far.thread_one(board, items, 'TGT')
print(res)
for t in board.GetTracks():
    if t.GetNetname() == 'TGT':
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            print('VIA at', round(TM(p.x), 2), round(TM(p.y), 2))
        else:
            s, e = t.GetStart(), t.GetEnd()
            print('TRK L', t.GetLayer(), (round(TM(s.x), 2), round(TM(s.y), 2)),
                  (round(TM(e.x), 2), round(TM(e.y), 2)))
