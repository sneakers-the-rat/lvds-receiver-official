import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.kicad_pcb')
want = {'T1','D5','C32','Q1','R28','U9','C4','C33','R29','R47','D1','C35','J5','R27','C31','U10'}
for fp in b.GetFootprints():
    r = fp.GetReference()
    if r in want:
        p = fp.GetPosition()
        print(f"{r:5s} pos=({pcbnew.ToMM(p.x):7.2f},{pcbnew.ToMM(p.y):7.2f}) rot={fp.GetOrientationDegrees():6.1f} fp={fp.GetFPID().GetLibItemName()}")
print('board edges:', [pcbnew.ToMM(v) for v in (b.GetBoardEdgesBoundingBox().GetLeft(), b.GetBoardEdgesBoundingBox().GetTop(), b.GetBoardEdgesBoundingBox().GetRight(), b.GetBoardEdgesBoundingBox().GetBottom())])
