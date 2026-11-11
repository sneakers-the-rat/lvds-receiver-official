#!/usr/bin/env python3
"""SH1 census 2 (read-only): precise pad rects for the AFE row
and every track/via crossing the candidate wall lines."""
import wx
_app = wx.App(False)
import pcbnew

board = pcbnew.LoadBoard('hw/pdlvds_rx.kicad_pcb')

def BB(item):
    b = item.GetBoundingBox()
    return (b.GetLeft() / 1e6, b.GetTop() / 1e6,
            b.GetRight() / 1e6, b.GetBottom() / 1e6)

print('=== pad rects: D1 U1 U2 U3 ===')
for fp in board.GetFootprints():
    if fp.GetReference() not in ('D1', 'U1', 'U2', 'U3'):
        continue
    print(' %s at (%.2f,%.2f) rot %d' % (
        fp.GetReference(), fp.GetPosition().x / 1e6,
        fp.GetPosition().y / 1e6, int(fp.GetOrientationDegrees())))
    for p in fp.Pads():
        b = BB(p)
        print('   pad %-3s %-10s x[%.2f,%.2f] y[%.2f,%.2f]' % (
            p.GetNumber(), p.GetNetname(), b[0], b[2], b[1], b[3]))

def crossings(axis, at, lo, hi):
    print('=== copper crossing %s=%.2f, %s in [%.1f,%.1f] ===' % (
        axis, at, 'y' if axis == 'x' else 'x', lo, hi))
    out = []
    for t in board.GetTracks():
        b = BB(t)
        if axis == 'x':
            if b[0] <= at <= b[2]:
                s, e = max(b[1], lo), min(b[3], hi)
                if s < e:
                    out.append((s, e, t))
        else:
            if b[1] <= at <= b[3]:
                s, e = max(b[0], lo), min(b[2], hi)
                if s < e:
                    out.append((s, e, t))
    for (s, e, t) in sorted(out):
        kind = 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk'
        print('   %s %-10s [%.2f, %.2f] L%s' % (
            kind, t.GetNetname(), s, e,
            'F' if t.GetLayer() == pcbnew.F_Cu else
            ('In2' if t.GetLayer() == pcbnew.In2_Cu else t.GetLayer())))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            b = BB(p)
            if axis == 'x' and b[0] <= at <= b[2] and b[1] < hi and b[3] > lo:
                print('   pad %s.%s %s y[%.2f,%.2f]' % (
                    fp.GetReference(), p.GetNumber(), p.GetNetname(),
                    b[1], b[3]))
            if axis == 'y' and b[1] <= at <= b[3] and b[0] < hi and b[2] > lo:
                print('   pad %s.%s %s x[%.2f,%.2f]' % (
                    fp.GetReference(), p.GetNumber(), p.GetNetname(),
                    b[0], b[2]))

crossings('x', 11.3, 29.0, 51.0)
crossings('x', 34.0, 29.0, 51.0)
crossings('x', 35.0, 29.0, 51.0)
crossings('y', 30.0, 9.0, 38.0)
crossings('y', 50.0, 9.0, 38.0)
print('done')
