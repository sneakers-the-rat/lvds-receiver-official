"""t_ac19: refill zones on a board in a FRESH process and save;
print reload track counts for the named nets (save-rename check).

Usage: xvfb-run -a python3 scratch/work/t_ac19_refill.py IN OUT NET [NET...]
"""
import sys
import wx
_app = wx.App(False)
import pcbnew
from collections import Counter

src, out = sys.argv[1], sys.argv[2]
names = sys.argv[3:]
board = pcbnew.LoadBoard(src)
builder = pcbnew.ZONE_FILLER(board)
builder.Fill(board.Zones())
board.Save(out)
b2 = pcbnew.LoadBoard(out)
c = Counter(t.GetNetname() for t in b2.GetTracks())
for n in names:
    print(f'reload {n} tracks:', c[n])
print('saved', out)
