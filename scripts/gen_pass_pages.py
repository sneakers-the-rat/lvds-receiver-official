#!/usr/bin/env python3
"""Generate the Jekyll pass pages from history/passes.json.

    python3 scripts/gen_pass_pages.py

One markdown file per layout pass in website/_passes/pass-NNNN.md:
front matter carries the pass number, commit hash, UTC timestamp,
audit stats (unconnected nets, clearance violations, pins failed,
nets routed/total, verdict), the adopted flag and the render file
map; the body is the pass's changelog description. The Jekyll
`passes` collection turns each file into a page; the routing
history index and the sidebar TOC list them with Liquid loops, so
adding a pass is adding one file — no generator edits.

scripts/commit_pass.py calls pass_markdown() from this module so a
pass commit writes its .md in the same step as its passes.json /
PASSES.md entries, from the same data.

The `adopted` flag: a pass counts as adopted when its board became
part of the main-board lineage the next pass built on. It is false
only where the pass's own record says so — passes 5 and 8, whose
descriptions state NOT adopted verbatim. The flag is written into
each generated file explicitly so the site never re-derives it.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASSES_JSON = os.path.join(ROOT, "history", "passes.json")
PASSES_DIR = os.path.join(ROOT, "website", "_passes")

# Passes whose own committed record says the board was NOT adopted.
NOT_ADOPTED = {5, 8}


def _q(v):
    """YAML-safe scalar: JSON double-quoted string, or bare
    number/bool/null."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return json.dumps(str(v))


def pass_markdown(entry):
    """(filename, markdown text) for one passes.json entry."""
    n = entry["pass"]
    st = entry.get("stats") or {}
    adopted = n not in NOT_ADOPTED
    fm = ["---", "layout: pass", f"pass: {n}",
          f"title: {_q(f'Pass {n}')}",
          f"hash: {_q(entry.get('hash'))}",
          f"short_hash: {_q(entry.get('short_hash'))}",
          f"timestamp: {_q(entry.get('timestamp'))}",
          f"board_file: {_q(entry.get('board_file'))}",
          f"dir: {_q(entry.get('dir'))}",
          f"adopted: {_q(adopted)}"]
    for key in ("nets_routed", "nets_total", "pins_failed",
                "clearance_violations", "unconnected_nets",
                "audit_verdict"):
        fm.append(f"{key}: {_q(st.get(key))}")
    for key in ("renders", "layers"):
        m = entry.get(key)
        if m:
            fm.append(f"{key}:")
            for k, v in m.items():
                fm.append(f"  {json.dumps(k)}: {_q(v)}")
        else:
            fm.append(f"{key}: null")
    fm.append(f"note: {_q(entry.get('note') or '')}")
    fm.append(f"description: {_q((entry.get('description') or '').strip())}")
    fm.append("---")
    body = (entry.get("description") or "").strip()
    return f"pass-{n:04d}.md", "\n".join(fm) + "\n\n" + body + "\n"


def main():
    doc = json.load(open(PASSES_JSON))
    os.makedirs(PASSES_DIR, exist_ok=True)
    written = []
    for entry in doc["passes"]:
        name, text = pass_markdown(entry)
        with open(os.path.join(PASSES_DIR, name), "w") as f:
            f.write(text)
        written.append(name)
    print(f"wrote {len(written)} pass pages: "
          f"{', '.join(written)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
