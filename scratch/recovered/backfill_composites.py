#!/usr/bin/env python3
"""Backfill board-all-layers.svg composites for passes 1-10.

Each pass's board is extracted AS OF its own commit
(git show <hash>:<board_file>) and rendered in a child process.
The composite is verified (no <image>, all four palette colours,
viewBox identical to the pass's existing layer render), copied
into history/<dir>/, registered in passes.json renders as
"all_layers", and the provenance sentence is appended to the
pass's note in passes.json, history/PASSES.md and stats.txt.
"""
import json, os, re, subprocess, sys, tempfile

ROOT = "/home/hatch/workspace/pdlvds-chartv2"
SENTENCE = ("Composite render backfilled on 2026-11-04 by rendering "
            "the board file as of this pass's commit; not "
            "contemporaneous with the pass.")
PALETTE = {"F.Cu": "#FF3B30", "In1.Cu": "#FF9500",
           "In2.Cu": "#34C759", "B.Cu": "#0A84FF"}

doc = json.load(open(os.path.join(ROOT, "history", "passes.json")))
results = []
for e in doc["passes"]:
    n, h, bf, d = e["pass"], e["hash"], e["board_file"], e["dir"]
    sdir = os.path.join(ROOT, "history", d)
    out = os.path.join(sdir, "board-all-layers.svg")
    with tempfile.TemporaryDirectory() as td:
        board = os.path.join(td, "board.kicad_pcb")
        with open(board, "wb") as f:
            r = subprocess.run(["git", "-C", ROOT, "show", f"{h}:{bf}"],
                               capture_output=True)
            assert r.returncode == 0, f"pass {n}: git show failed"
            f.write(r.stdout)
        tmp_out = os.path.join(td, "board-all-layers.svg")
        r = subprocess.run([sys.executable, "/tmp/render_composite.py",
                            board, tmp_out],
                           capture_output=True, text=True)
        assert r.returncode == 0, f"pass {n}: render failed: {r.stderr}"
        svg = open(tmp_out).read()
    # ---- verification against the pass's own existing layer render
    layer_svg = open(os.path.join(sdir, e["layers"]["F.Cu"])).read()
    vb = lambda t: re.search(r'viewBox="([^"]+)"', t).group(1)
    checks = {
        "no <image>": "<image" not in svg,
        "viewBox == layer viewBox": vb(svg) == vb(layer_svg),
        "viewBox": vb(svg),
        "size": len(svg),
    }
    for layer, colour in PALETTE.items():
        checks[f"{layer} colour present"] = svg.count(colour) > 0
    assert all(v for k, v in checks.items() if isinstance(v, bool)), \
        f"pass {n}: verification failed: {checks}"
    with open(out, "w") as f:
        f.write(svg)
    # ---- record: renders map + note provenance
    e.setdefault("renders", {})["all_layers"] = "board-all-layers.svg"
    note = (e.get("note") or "").strip()
    e["note"] = (note + " " + SENTENCE) if note else SENTENCE
    st = os.path.join(sdir, "stats.txt")
    with open(st, "a") as f:
        f.write(f"note: {SENTENCE}\n")
    results.append((n, checks["viewBox"], checks["size"]))
    print(f"pass {n}: OK viewBox={checks['viewBox']} size={checks['size']}")

with open(os.path.join(ROOT, "history", "passes.json"), "w") as f:
    json.dump(doc, f, indent=2)
    f.write("\n")

# ---- PASSES.md: append the sentence at the end of each pass section
md_path = os.path.join(ROOT, "history", "PASSES.md")
md = open(md_path).read()
parts = re.split(r"(?m)^(### Pass \d+ .*)$", md)
# parts: [prefix, heading, body, heading, body, ...]
for i in range(1, len(parts), 2):
    body = parts[i + 1].rstrip("\n")
    paras = body.split("\n\n")
    # last paragraph: the note paragraph if it follows the stats line,
    # else append a new paragraph.
    if len(paras) >= 4:  # board line, description, stats, note
        paras[-1] = paras[-1].rstrip() + " " + SENTENCE
    else:
        paras.append(SENTENCE)
    parts[i + 1] = "\n\n".join(paras) + "\n\n"
open(md_path, "w").write("".join(parts))
print("passes.json + PASSES.md updated for", len(results), "passes")
