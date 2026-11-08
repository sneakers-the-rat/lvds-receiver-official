"""t_aq4: reload census diff between two board files (separate process
per load not needed: loads are sequential but boards must be freed —
pcbnew keeps one board; use two subprocess-free loads via fresh
LoadBoard after deleting the previous board object is unreliable, so
this script takes ONE path and prints counts; caller diffs)."""
import sys, wx
_app = wx.App(False)
import pcbnew

path = sys.argv[1]
bb = pcbnew.LoadBoard(path)
c = {}
for t in bb.GetTracks():
    n = t.GetNetname()
    k = 'via' if isinstance(t, pcbnew.PCB_VIA) else 'seg'
    c[(n, k)] = c.get((n, k), 0) + 1
for (n, k) in sorted(c):
    print(f'{n}\t{k}\t{c[(n, k)]}')
print(f'TOTAL\tall\t{sum(c.values())}')
