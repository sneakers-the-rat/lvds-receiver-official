"""t_bd8: STP copper census in the DIR-stub box on exp256.
t_bd7 showed the DIR stub bend (75.85,17.35) sits 0.1 from an
ULPI_STP seg edge -- need STP's exact F stub path from U7.13
(76.25,16.438) to the dive via (76.065,17.96), plus all F items in
x[75.3,76.6] y[16.8,18.4]."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp256.kicad_pcb')
items, _pc = repair.build_items(board)
LAYN = ['F', 'In2', 'B']
X0, X1, Y0, Y1 = 75.3, 76.6, 16.8, 18.4

def inb(x, y):
    return X0 <= x <= X1 and Y0 <= y <= Y1

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
            if hit and (li == 0 or net == 'ULPI_STP'):
                seen.add(id(it))
                print(LAYN[li], k, net, tuple(round(v, 3) for v in d), 'clr', it[3])
