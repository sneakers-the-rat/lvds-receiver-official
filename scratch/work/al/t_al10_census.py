import sys, wx
_app = wx.App(False)
import pcbnew
from collections import Counter
b = pcbnew.LoadBoard(sys.argv[1])
c = Counter()
for t in b.GetTracks():
    c[t.GetNetname()] += 1
print('census: DAC_SYNC', c['DAC_SYNC'], '| SWCLK', c['SWCLK'], '| total', sum(c.values()))
