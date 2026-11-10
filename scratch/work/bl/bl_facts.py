#!/usr/bin/env python3
"""bl facts: U7 pad census + per-net copper inventory on exp257."""
import wx
_app = wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp257.kicad_pcb')
IU = 1e6
u7 = None
for fp in b.GetFootprints():
    if fp.GetReference() == 'U7':
        u7 = fp
p = u7.GetPosition()
print(f'U7 pos ({p.x/IU:.3f},{p.y/IU:.3f}) rot {u7.GetOrientation().AsDegrees():.1f}')
print('== U7 pads (num, net, x, y, sx, sy):')
nets = set()
for pad in u7.Pads():
    pp = pad.GetPosition()
    s = pad.GetSize()
    print(f'  {pad.GetNumber():>3} {pad.GetNetname():<12} ({pp.x/IU:7.3f},{pp.y/IU:7.3f}) {s.x/IU:.2f}x{s.y/IU:.2f}')
    nets.add(pad.GetNetname())
print('== per-net copper touching box x[68,86] y[0,26] (trk count, via count, x-range, y-range):')
for n in sorted(nets):
    tr = []
    vi = []
    for t in b.GetTracks():
        if t.GetNetname() != n:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            q = t.GetPosition()
            vi.append((q.x / IU, q.y / IU, t.GetWidth() / IU))
        else:
            s, e = t.GetStart(), t.GetEnd()
            tr.append(((s.x / IU, s.y / IU), (e.x / IU, e.y / IU), t.GetLayer()))
    xs = [c for seg in tr for c in (seg[0][0], seg[1][0])] + [v[0] for v in vi]
    ys = [c for seg in tr for c in (seg[0][1], seg[1][1])] + [v[1] for v in vi]
    if xs:
        print(f'  {n:<12} trk {len(tr):3d} via {len(vi)} x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}]')
    else:
        print(f'  {n:<12} NO COPPER')
print('== U7 courtyard bbox:')
bb = u7.GetBoundingBox()
print(f'  x[{bb.GetLeft()/IU:.3f},{bb.GetRight()/IU:.3f}] y[{bb.GetTop()/IU:.3f},{bb.GetBottom()/IU:.3f}]')
