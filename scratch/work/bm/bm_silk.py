import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp265.kicad_pcb')
fp = b.FindFootprintByReference('C22')
print('C22 at', fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6, 'rot', fp.GetOrientationDegrees())
for t in fp.GraphicalItems():
    print(type(t).__name__, getattr(t, 'GetText', lambda: '')(), t.GetPosition().x / 1e6, t.GetPosition().y / 1e6, t.GetLayer())
ref = fp.Reference()
print('REF', ref.GetText(), ref.GetPosition().x / 1e6, ref.GetPosition().y / 1e6, ref.GetLayer())
val = fp.Value()
print('VAL', val.GetText(), val.GetPosition().x / 1e6, val.GetPosition().y / 1e6, val.GetLayer())
