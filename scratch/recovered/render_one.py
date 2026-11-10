#!/usr/bin/env python3
"""Render ONE backfill pass per process (KiCad 7 SWIG LoadBoard
quirk) via commit_pass.render_pass — the exact commit_pass.py
code path. Usage: render_one.py <board> <tag>"""
import json, os, sys

sys.path.insert(0, "/home/hatch/workspace/pdlvds-chartv2/scripts")
import commit_pass as cp

board, tag = sys.argv[1], sys.argv[2]
sdir = os.path.join(cp.HIST, tag)
os.makedirs(sdir, exist_ok=True)
renders, layers, method = cp.render_pass(board, sdir)
print(json.dumps({"tag": tag, "renders": renders, "layers": layers,
                  "method": method,
                  "files": sorted(os.listdir(sdir))}))
