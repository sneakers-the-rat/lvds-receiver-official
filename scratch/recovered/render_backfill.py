#!/usr/bin/env python3
"""Backfill renders for passes 5, 8, 9 using commit_pass.render_pass
(the exact code path commit_pass.py uses), on boards extracted from
each pass's own commit."""
import json, os, sys

sys.path.insert(0, "/home/hatch/workspace/pdlvds-chartv2/scripts")
import commit_pass as cp

JOBS = [("/tmp/backfill/p5.kicad_pcb", "pass-0005"),
        ("/tmp/backfill/p8.kicad_pcb", "pass-0008"),
        ("/tmp/backfill/p9.kicad_pcb", "pass-0009")]

out = {}
for board, tag in JOBS:
    sdir = os.path.join(cp.HIST, tag)
    os.makedirs(sdir, exist_ok=True)
    renders, layers, method = cp.render_pass(board, sdir)
    out[tag] = {"renders": renders, "layers": layers, "method": method,
                "files": sorted(os.listdir(sdir))}
    print(tag, "->", out[tag])

with open("/tmp/backfill/render_results.json", "w") as f:
    json.dump(out, f, indent=2)
