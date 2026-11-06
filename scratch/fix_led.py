#!/usr/bin/env python3
"""Surgical LED fix on exp167: delete LED_STAT's two shorting vias
(87.875,8.125) in X1.2's field and (95.375,0.875) crossing NRST's In1
run, plus the two 0.3536 F.Cu stubs at (88.125,7.875)/(88.375,7.625)
that clip XO; hand-lay D7.2's fanout (F.Cu stub south from the pad
centre to open field at (92.0375,16.3) + a via) so heal's sealed-pad
search has a freed ray to start from.
Usage: python3 scratch/fix_led.py IN OUT"""
import sys
import pcbnew

MM = 1_000_000
board = pcbnew.LoadBoard(sys.argv[1])

def near(p, x, y, tol=0.01):
    return abs(p.x / MM - x) < tol and abs(p.y / MM - y) < tol

kill = []
for t in board.GetTracks():
    if t.GetNetname() != 'LED_STAT':
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        if near(p, 87.875, 8.125) or near(p, 95.375, 0.875):
            kill.append(t)
    elif t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == pcbnew.F_Cu:
        a, e = t.GetStart(), t.GetEnd()
        for (x, y) in ((88.125, 7.875), (88.375, 7.625)):
            if near(a, x, y) or near(e, x, y):
                kill.append(t)
for t in kill:
    board.Remove(t)
print(f'deleted {len(kill)} LED_STAT items')

# hand fanout for D7.2 (LED_STAT_A): stub south + via in open field
net = board.FindNet('LED_STAT_A')
seg = pcbnew.PCB_TRACK(board)
seg.SetNet(net)
seg.SetLayer(pcbnew.F_Cu)
seg.SetStart(pcbnew.VECTOR2I(int(92.0375 * MM), int(14.5 * MM)))
seg.SetEnd(pcbnew.VECTOR2I(int(92.0375 * MM), int(16.3 * MM)))
seg.SetWidth(int(0.15 * MM))
board.Add(seg)
via = pcbnew.PCB_VIA(board)
via.SetNet(net)
via.SetPosition(pcbnew.VECTOR2I(int(92.0375 * MM), int(16.3 * MM)))
via.SetWidth(int(0.6 * MM))
via.SetDrill(int(0.3 * MM))
via.SetViaType(pcbnew.VIATYPE_THROUGH)
board.Add(via)
print('added LED_STAT_A fanout stub + via at (92.0375,16.3)')
board.Save(sys.argv[2])
print('saved', sys.argv[2])
