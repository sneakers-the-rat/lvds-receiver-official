"""t_bc4: dump ULPI_NXT copper + all F items in the DIR-via box on exp256.

Why: t_bc3 stage 1 showed every westward DIR-via landing on y=17.521
fails its F-layer gate against an ULPI_NXT seg (margin -0.240 at
x=75.200, worsening westward at ~0.84/mm). Need that seg's geometry
before a 2D via scan.
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp256.kicad_pcb')
items, _pc = repair.build_items(board)
X0, X1, Y0, Y1 = 73.0, 77.0, 15.5, 20.5

def inb(x, y):
    return X0 <= x <= X1 and Y0 <= y <= Y1

seen = set()
for li, ln in ((0, 'F'), (1, 'In2'), (2, 'B')):
    for key, lst in items[li].buckets.items():
        if key[0] != li:
            continue
        for it in lst:
            if id(it) in seen:
                continue
            k, net, d = it[0], it[1], it[2]
            hit = False
            if k == 'seg':
                hit = inb(d[0], d[1]) or inb(d[2], d[3])
            else:
                hit = inb(d[0], d[1])
            if hit:
                seen.add(id(it))
                if net == 'ULPI_NXT' or li == 0:
                    print(ln, k, net, tuple(round(v, 3) for v in d))
