import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from hand_stub import build_items
MM = pcbnew.FromMM

board = pcbnew.BOARD()
for name in ('A', 'B'):
    net = pcbnew.NETINFO_ITEM(board, name)
    board.Add(net)
na = board.FindNet('A')
t = pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(MM(1.0), MM(2.0)))
t.SetEnd(pcbnew.VECTOR2I(MM(4.0), MM(2.0)))
t.SetWidth(MM(0.25))
t.SetLayer(pcbnew.F_Cu)
t.SetNet(na)
board.Add(t)
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(7.0), MM(3.0)))
v.SetWidth(MM(0.6))
v.SetDrill(MM(0.3))
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNet(na)
board.Add(v)
for kind, net, layers, shape, desc in build_items(board):
    print(kind, net, type(shape).__name__)
    for attr in ('GetStart', 'GetEnd', 'GetWidth', 'GetCenter', 'GetRadius'):
        if hasattr(shape, attr):
            try:
                print('   ', attr, getattr(shape, attr)())
            except Exception as e:
                print('   ', attr, 'ERR', e)
