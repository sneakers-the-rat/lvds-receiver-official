import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp84.kicad_pcb')
fp = b.FindFootprintByReference('U13')
pad = [p for p in fp.Pads() if p.GetNumber() == '7'][0]
s1 = pad.GetEffectiveShape()
print('s1 bbox x', pcbnew.ToMM(s1.BBox().GetLeft()), pcbnew.ToMM(s1.BBox().GetRight()))
s1.Move(pcbnew.VECTOR2I(pcbnew.FromMM(-4.0), 0))
print('s1 moved bbox x', pcbnew.ToMM(s1.BBox().GetLeft()), pcbnew.ToMM(s1.BBox().GetRight()))
s2 = pad.GetEffectiveShape()
print('s2 fresh bbox x', pcbnew.ToMM(s2.BBox().GetLeft()), pcbnew.ToMM(s2.BBox().GetRight()))
print('same object:', s1 is s2)
