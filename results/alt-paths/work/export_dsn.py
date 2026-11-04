import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
ok = pcbnew.ExportSpecctraDSN(b, dst)
print("ExportSpecctraDSN ->", ok)
