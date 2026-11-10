import sys, wx
_app = wx.App(False)
import pcbnew
from collections import Counter
b = pcbnew.LoadBoard(sys.argv[1])
c = Counter(t.GetNetname() for t in b.GetTracks())
for n in ('XO','PHY_1V8A','+3V3A','+3V3D','I2C_SCL','PHY_1V8','GND'):
    print(f'{n}: {c[n]}')
