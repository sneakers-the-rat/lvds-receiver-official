#!/usr/bin/env python3
"""t_ah9_diff.py -- list tracks/vias added between successive boards,
and flag same-net via pairs closer than 0.7 mm (stacked/near) in the
final board."""
import sys
import wx
_app = wx.App(False)
import pcbnew

def items(path):
    b = pcbnew.LoadBoard(path)
    out = {}
    for t in b.GetTracks():
        a = (round(t.GetStart().x / 1e6, 4), round(t.GetStart().y / 1e6, 4))
        c = (round(t.GetEnd().x / 1e6, 4), round(t.GetEnd().y / 1e6, 4))
        if t.Type() == pcbnew.PCB_VIA_T:
            key = ('via', t.GetNetname(), a, round(t.GetWidth() / 1e6, 3))
        else:
            key = ('seg', t.GetNetname(), t.GetLayer(), a, c,
                   round(t.GetWidth() / 1e6, 3))
        out[key] = out.get(key, 0) + 1
    return out

paths = sys.argv[1:]
prev = items(paths[0])
print(f'== {paths[0]}: {sum(prev.values())} items')
for p in paths[1:]:
    cur = items(p)
    adds = []
    for k, n in cur.items():
        extra = n - prev.get(k, 0)
        adds += [k] * max(extra, 0)
    dels = []
    for k, n in prev.items():
        extra = n - cur.get(k, 0)
        dels += [k] * max(extra, 0)
    print(f'== {p}: +{len(adds)} -{len(dels)}')
    for k in sorted(adds, key=str):
        print('   ADD', k)
    for k in sorted(dels, key=str):
        print('   DEL', k)
    prev = cur

# stacked via check on the final board
b = pcbnew.LoadBoard(paths[-1])
vias = []
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        vias.append((t.GetNetname(),
                     round(t.GetPosition().x / 1e6, 4),
                     round(t.GetPosition().y / 1e6, 4),
                     round(t.GetWidth() / 1e6, 3)))
print(f'== stacked/near via pairs (<0.75 mm) in {paths[-1]}:')
for i in range(len(vias)):
    for j in range(i + 1, len(vias)):
        n1, x1, y1, w1 = vias[i]
        n2, x2, y2, w2 = vias[j]
        d = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
        if d < 0.75:
            print(f'   {n1} ({x1},{y1}) d{w1}  <->  {n2} ({x2},{y2}) '
                  f'd{w2}  dist {d:.3f}')
