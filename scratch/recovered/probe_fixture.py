import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.FromMM
board = pcbnew.BOARD()
net = pcbnew.NETINFO_ITEM(board, 'STRIPNET')
board.Add(net)
def add_pad(ref, x, y):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetLayer(pcbnew.F_Cu)
    board.Add(fp)
    pad = pcbnew.PAD(fp)
    pad.SetNumber('1')
    pad.SetShape(pcbnew.PAD_SHAPE_RECT)
    pad.SetSize(pcbnew.VECTOR2I(MM(1.0), MM(0.5)))
    pad.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    pad.SetLayerSet(ls)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetNet(net)
    fp.Add(pad)
add_pad('A1', 50.0, -20.0)
add_pad('A2', 60.0, -20.0)
board.Save('/tmp/fix.kicad_pcb')
b2 = pcbnew.LoadBoard('/tmp/fix.kicad_pcb')
import repair
items, pad_cells = repair.build_items(b2)
print('pad_cells:', pad_cells)
groups = repair.compute_groups(b2)
print('groups:', {n: [[it.desc for it in g] for g in gs] for n, gs in groups.items()})
