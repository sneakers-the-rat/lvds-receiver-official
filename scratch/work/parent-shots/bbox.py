import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp252.kicad_pcb')
bb = b.GetBoardEdgesBoundingBox()
print('BBOX_MM', bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6)
