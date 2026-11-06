#!/usr/bin/env python3
"""Sacrificial fence over the creepage slot: lay SLOTFENCE-net tracks
across the slot band on all copper layers so the heal router (which
ignores Edge.Cuts) is forced around the slot ends, or remove them.

Usage: python3 scratch/fence_slot.py BOARD add|remove
Band: x 10.6..47.4, rows every 0.55 mm from y 23.0 to 25.75
(slot x12..46 / y23.6..25.1 plus the 0.5 mm edge-clearance halo).
The fence is temporary: heal between add and remove; never commit a
board with the fence on it."""
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
    net = pcbnew.NETINFO_ITEM(board, 'SLOTFENCE')
    board.Add(net)
    code = net.GetNetCode()
    layers = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
    n = 0
    for layer in layers:
        y = 23.0
        while y <= 25.76:
            t = pcbnew.PCB_TRACK(board)
            t.SetNetCode(code)
            t.SetLayer(layer)
            t.SetWidth(int(0.25 * MM))
            t.SetStart(pcbnew.VECTOR2I(int(10.6 * MM), int(y * MM)))
            t.SetEnd(pcbnew.VECTOR2I(int(47.4 * MM), int(y * MM)))
            board.Add(t)
            n += 1
            y += 0.55
    print(f'added {n} fence tracks')
board.Save(path)
print(f'saved {path}')
