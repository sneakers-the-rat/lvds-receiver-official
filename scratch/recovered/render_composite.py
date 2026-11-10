#!/usr/bin/env python3
"""Child process: render ONE composite SVG for one extracted board.

Usage: render_composite.py <board.kicad_pcb> <out.svg>
Run once per board in its own process: KiCad 7's pcbnew corrupts
type state on a second LoadBoard in one process (found by the
renders backfill), so the driver never loads two boards itself.
Uses the same machinery commit_pass.render_pass uses for the
composite: snapshot_route.make_route_board + export_svg(ALL_LAYERS).
"""
import os, shutil, sys

sys.path.insert(0, "/home/hatch/workspace/pdlvds-chartv2/scripts")
import snapshot_route as sr

board, out = sys.argv[1], sys.argv[2]
route_board, method = sr.make_route_board(board)
if route_board is None:
    print(f"warning: {method}", file=sys.stderr)
    route_board = board
spec = sr.export_svg(route_board, out, sr.ALL_LAYERS, mirror=False)
if route_board != board:
    shutil.rmtree(os.path.dirname(route_board), ignore_errors=True)
print(f"composite spec: {spec}")
sys.exit(0 if spec else 1)
