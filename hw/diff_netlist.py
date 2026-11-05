#!/usr/bin/env python3
"""Diff the live board's pin->net assignment + footprints against
the corrected schematic's netlist map (scratch/netlist_map.json,
extracted from the merged parts-fix netlist: 152 parts / 648 pins /
223 nets). Output: new refs, footprint swaps, pin-net changes.
Usage: xvfb-run -a python3 hw/diff_netlist.py BOARD
"""
import json
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
nmap = json.load(open('scratch/netlist_map.json'))

bfps = {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    pads = {}
    for p in fp.Pads():
        pads[p.GetNumber()] = p.GetNetname()
    bfps[ref] = (str(fp.GetFPID().GetLibItemName()), pads)

new_refs = sorted(set(nmap) - set(bfps))
gone_refs = sorted(set(bfps) - set(nmap))
print(f'board fps: {len(bfps)}  map refs: {len(nmap)}')
print(f'NEW refs (place): {new_refs}')
print(f'GONE refs (remove): {gone_refs}')
print('\nFOOTPRINT SWAPS:')
for ref in sorted(set(nmap) & set(bfps)):
    want = nmap[ref]['footprint'].split(':')[-1]
    have = bfps[ref][0]
    if want != have:
        print(f'  {ref}: {have} -> {want}')
print('\nPIN-NET CHANGES (same footprint or swap):')
nchg = 0
for ref in sorted(set(nmap) & set(bfps)):
    want = nmap[ref]['pins']
    have = bfps[ref][1]
    for pin in sorted(set(want) | set(have)):
        w, h = want.get(pin), have.get(pin)
        if w != h:
            print(f'  {ref}.{pin}: {h} -> {w}')
            nchg += 1
print(f'total pin-net changes: {nchg}')
nets_board = {n.GetNetname() for n in board.GetNetInfo().NetsByNetcode().values()}
nets_map = {v for e in nmap.values() for v in e['pins'].values()}
print(f'\nNETS only in map (create): {sorted(nets_map - nets_board)}')
print(f'NETS only on board (orphan after re-sync): {sorted(nets_board - nets_map)}')
