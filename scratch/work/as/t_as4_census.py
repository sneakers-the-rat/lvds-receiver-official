"""t_as4: per-net track+via census diff between two boards (rename tripwire)."""
import sys, wx
_app = wx.App(False)
import pcbnew
from collections import Counter
def census(path):
    b = pcbnew.LoadBoard(path)
    c = Counter()
    for t in b.GetTracks():
        c[t.GetNetname()] += 1
    return c
a = census(sys.argv[1]); b = census(sys.argv[2])
nets = sorted(set(a) | set(b))
diff = 0
for n in nets:
    if a[n] != b[n]:
        print(f'{n}: {a[n]} -> {b[n]} ({b[n]-a[n]:+d})')
        diff += 1
print(f'{diff} nets changed; total tracks {sum(a.values())} -> {sum(b.values())}')
