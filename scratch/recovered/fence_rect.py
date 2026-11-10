#!/usr/bin/env python3
"""Sacrificial fence over an arbitrary rectangle: lay SLOTFENCE-net
tracks filling the rect (lines along its long axis, 0.55 mm pitch, all
copper layers) so the heal router is forced around it, or remove them.
Generalizes scratch/fence_slot.py (the creepage-slot band).

Usage: python3 scratch/fence_rect.py BOARD add X0 Y0 X1 Y1
       python3 scratch/fence_rect.py BOARD remove
Never commit a board with the fence on it."""
import sys
import pcbnew

MM = 1_000_000
path, mode = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(path)
if mode == 'remove':
    kill = [t for t in board.GetTracks() if t.GetNetname() == 'SLOTFENCE']
    for t in kill:
        board.Remove(t)
    print(f'removed {len(kill)} fence tracks')
else:
    x0, y0, x1, y1 = (float(v) for v in sys.argv[3:7])
    step = float(sys.argv[7]) if len(sys.argv) > 7 else 0.55
    net = pcbnew.NETINFO_ITEM(board, 'SLOTFENCE')
    board.Add(net)
    code = net.GetNetCode()
    layers = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
    n = 0
    for layer in layers:
        if (x1 - x0) >= (y1 - y0):
            y = y0
            while y <= y1 + 1e-9:
                t = pcbnew.PCB_TRACK(board)
                t.SetNetCode(code)
                t.SetLayer(layer)
                t.SetWidth(int(0.25 * MM))
                t.SetStart(pcbnew.VECTOR2I(int(x0 * MM), int(y * MM)))
                t.SetEnd(pcbnew.VECTOR2I(int(x1 * MM), int(y * MM)))
                board.Add(t)
                n += 1
                y += 0.55
        else:
            x = x0
            while x <= x1 + 1e-9:
                t = pcbnew.PCB_TRACK(board)
                t.SetNetCode(code)
                t.SetLayer(layer)
                t.SetWidth(int(0.25 * MM))
                t.SetStart(pcbnew.VECTOR2I(int(x * MM), int(y0 * MM)))
                t.SetEnd(pcbnew.VECTOR2I(int(x * MM), int(y1 * MM)))
                board.Add(t)
                n += 1
                x += 0.55
    print(f'added {n} fence tracks')
board.Save(path)
print(f'saved {path}')
