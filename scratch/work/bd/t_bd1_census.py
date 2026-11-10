"""t_bd1: census for the XI mouth redesign on exp256.

Dumps (a) full board-wide copper topology of ULPI_NXT, ULPI_DIR,
ULPI_STP, XI; (b) every item in the mouth box x[73.0,77.5] y[15.0,20.5]
on all layers; (c) U7/U6 pad rects intersecting that box, so the NXT
escape re-lay + DIR via move can be gated against rect truth.
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp256.kicad_pcb')
items, _pc = repair.build_items(board)
LAYN = ['F', 'In2', 'B']
FOCUS = {'ULPI_NXT', 'ULPI_DIR', 'ULPI_STP', 'XI'}

print('== full topology of focus nets (all layers) ==')
for li in range(3):
    seen = set()
    for key, lst in items[li].buckets.items():
        if key[0] != li:
            continue
        for it in lst:
            if id(it) in seen or it[1] not in FOCUS:
                continue
            seen.add(id(it))
            print(LAYN[li], it[0], it[1], tuple(round(v, 3) for v in it[2]),
                  'clr', it[3])

X0, X1, Y0, Y1 = 73.0, 77.5, 15.0, 20.5
def inb(x, y):
    return X0 <= x <= X1 and Y0 <= y <= Y1

print('\n== all items in mouth box ==')
for li in range(3):
    seen = set()
    for key, lst in items[li].buckets.items():
        if key[0] != li:
            continue
        for it in lst:
            if id(it) in seen:
                continue
            k, net, d = it[0], it[1], it[2]
            hit = (inb(d[0], d[1]) or inb(d[2], d[3])) if k == 'seg' else inb(d[0], d[1])
            if hit:
                seen.add(id(it))
                print(LAYN[li], k, net, tuple(round(v, 3) for v in d), 'clr', it[3])

print('\n== pads in/near mouth box (rect truth, mm) ==')
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        p = pad.GetPosition()
        x, y = p.x / 1e6, p.y / 1e6
        if X0 - 1 <= x <= X1 + 1 and Y0 - 1 <= y <= Y1 + 1:
            sz = pad.GetSize()
            net = pad.GetNetname()
            print(f'{ref}.{pad.GetNumber()} net={net} centre=({x:.3f},{y:.3f}) '
                  f'size=({sz.x/1e6:.3f}x{sz.y/1e6:.3f}) rot={fp.GetOrientationDegrees():.0f}')
