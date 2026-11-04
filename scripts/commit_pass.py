#!/usr/bin/env python3
"""Commit one layout pass — the only way passes are added.

    python3 scripts/commit_pass.py "what changed in this pass"

A pass is a new board state (a routing or placement change). The
moment one exists — a finished run, a checkpoint of a long run, a
placement tweak — this command, run from the repo root:

  1. runs the audit (hw/check_pcb.py, under xvfb-run when present)
     on the board and saves its output as
     history/pass-NNNN/audit.txt;
  2. renders the pass's image set into history/pass-NNNN/ using
     snapshot_route.py's route-only machinery (zones deleted from a
     temp copy; light-on-dark palette), plus a stats.txt;
  3. appends the entry — next pass number, timestamp, audit stats,
     the description given on the command line — to
     history/passes.json and history/PASSES.md, and writes the
     pass's Jekyll page website/_passes/pass-NNNN.md from the same
     entry (gen_pass_pages.pass_markdown), so a relayout literally
     creates one new markdown file for the site's passes collection;
  4. stages exactly the pass's files (the board, router code and
     result/log changes under hw/ and results/, the pass directory,
     the two log files) and commits: "pass NNNN: <description>";
  5. writes the pass commit's hash into the log files and makes one
     small bookkeeping commit ("pass NNNN: record commit hash") —
     a commit cannot contain its own hash, so this is the earliest
     moment the hash can be recorded.

After it finishes, the only remaining step is `git push`.

The audit's verdict is recorded, never gated on: a mid-routing
board audits FAIL, and the pass is committed anyway — the evolution
is the record. Numbers the audit does not produce are recorded as
"not recorded", never invented.

Options:
  --board FILE   board to audit/render (default hw/pdlvds_rx.kicad_pcb)
  --note TEXT    extra note appended to the pass entry
  --no-audit     skip the audit (stats recorded as not recorded)
"""
import argparse, json, os, shutil, subprocess, sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snapshot_route as sr
import gen_pass_pages as gpp

ROOT = sr.ROOT
HIST = os.path.join(ROOT, "history")
PASSES_JSON = os.path.join(HIST, "passes.json")
PASSES_MD = os.path.join(HIST, "PASSES.md")
STAT_KEYS = ("nets_routed", "nets_total", "pins_failed",
             "clearance_violations", "unconnected_nets", "audit_verdict")


def git(*args, check=True):
    r = subprocess.run(["git", "-C", ROOT, *args],
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def nr(v):
    return "not recorded" if v is None else str(v)


def stats_line(st):
    nets = nr(st.get("nets_routed"))
    if st.get("nets_routed") is not None and st.get("nets_total"):
        nets = f"{st['nets_routed']} of {st['nets_total']}"
    return (f"Nets fully routed: {nets} · Pins failed: "
            f"{nr(st.get('pins_failed'))} · Clearance violations: "
            f"{nr(st.get('clearance_violations'))} · Unconnected nets: "
            f"{nr(st.get('unconnected_nets'))} · Audit verdict: "
            f"{nr(st.get('audit_verdict'))}")


def run_audit(board, out_path):
    """Run hw/check_pcb.py on `board`, save raw output to out_path,
    return the parsed stats dict ({} if the audit did not run)."""
    cmd = []
    if shutil.which("xvfb-run"):
        cmd += ["xvfb-run", "-a"]
    cmd += [sys.executable, os.path.join(ROOT, "hw", "check_pcb.py"),
            board]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=3600)
        out = (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        out = f"audit failed to run: {e}\n"
    with open(out_path, "w") as f:
        f.write(out)
    return sr.parse_audit(out_path)


def render_pass(board, sdir):
    """Render the pass's image set into sdir via snapshot_route's
    machinery. Returns (renders, layers, render_method)."""
    route_board, method = sr.make_route_board(board)
    if route_board is None:
        print(f"warning: {method}", file=sys.stderr)
        route_board = board
    renders = None
    top = sr.export_svg(route_board, os.path.join(sdir, "board-top.svg"),
                        sr.TOP_LAYERS, mirror=False)
    bottom = sr.export_svg(route_board,
                           os.path.join(sdir, "board-bottom.svg"),
                           sr.BOTTOM_LAYERS, mirror=True)
    if top and bottom:
        renders = {"top": "board-top.svg", "bottom": "board-bottom.svg"}
    else:
        print("warning: kicad-cli SVG export failed; pass will carry "
              "no top/bottom renders", file=sys.stderr)
    layers = {}
    for layer in sr.COPPER_LAYERS:
        n = sr.export_layer(route_board,
                            os.path.join(sdir, sr.LAYER_FILES[layer]),
                            layer)
        if n is None:
            print(f"warning: layer export failed for {layer}",
                  file=sys.stderr)
        else:
            layers[layer] = sr.LAYER_FILES[layer]
    if route_board != board:
        shutil.rmtree(os.path.dirname(route_board), ignore_errors=True)
    return renders, (layers or None), method


def write_pass_page(entry):
    """Write the pass's Jekyll page (website/_passes/pass-NNNN.md)
    from its passes.json entry; return its repo-relative path."""
    name, text = gpp.pass_markdown(entry)
    os.makedirs(gpp.PASSES_DIR, exist_ok=True)
    with open(os.path.join(gpp.PASSES_DIR, name), "w") as f:
        f.write(text)
    return f"website/_passes/{name}"


def stage_pass_files(board_rel, sdir_rel, page_rel):
    """Stage exactly the pass's files; return (staged, left) lists."""
    paths = [sdir_rel, "history/passes.json", "history/PASSES.md",
             page_rel, board_rel]
    left = []
    status = git("status", "--porcelain", "--", "hw", "results")
    for line in status.splitlines():
        p = line[3:].strip()
        if " -> " in p:
            p = p.split(" -> ")[-1]
        if p == board_rel or p.startswith(sdir_rel):
            continue
        keep = (p.startswith("hw/") and
                (p.endswith(".py") or p.endswith(".kicad_pcb"))) or \
               (p.startswith("results/") and
                (p.endswith(".txt") or p.endswith(".log")))
        (paths if keep else left).append(p)
    git("add", "--", *sorted(set(paths)))
    staged = git("diff", "--cached", "--name-only").splitlines()
    return staged, left


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("description",
                    help="one-line changelog for this pass: what "
                         "strategy changed vs the previous pass")
    ap.add_argument("--board", default=os.path.join(ROOT, "hw",
                                                    "pdlvds_rx.kicad_pcb"))
    ap.add_argument("--note", default="")
    ap.add_argument("--no-audit", action="store_true")
    a = ap.parse_args()

    board = os.path.abspath(a.board)
    if not os.path.exists(board):
        print(f"error: board file not found: {board}", file=sys.stderr)
        return 1
    board_rel = os.path.relpath(board, ROOT)

    if os.path.exists(PASSES_JSON):
        doc = json.load(open(PASSES_JSON))
    else:
        doc = {"version": 1, "rule": "", "passes": [], "gaps": []}
    n = max([p["pass"] for p in doc["passes"]], default=0) + 1
    tag = f"pass-{n:04d}"
    sdir = os.path.join(HIST, tag)
    os.makedirs(sdir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    stats = {k: None for k in STAT_KEYS}
    if not a.no_audit:
        parsed = run_audit(board, os.path.join(sdir, "audit.txt"))
        stats.update(parsed)
        print(f"audit: unconnected={nr(stats['unconnected_nets'])} "
              f"violations={nr(stats['clearance_violations'])} "
              f"verdict={nr(stats['audit_verdict'])}")
    else:
        with open(os.path.join(sdir, "audit.txt"), "w") as f:
            f.write("audit not run (--no-audit)\n")

    renders, layers, method = render_pass(board, sdir)
    lines = [f"pass: {n}", f"description: {a.description}",
             f"timestamp (UTC): {ts}", "commit: pending",
             f"board file: {board_rel}",
             "renders: " + ("board-top.svg, board-bottom.svg"
                            if renders else "none"),
             f"route-only renders: {method or 'not recorded'}",
             stats_line(stats).replace(" · ", "\n").lower(),
             f"note: {a.note}"]
    with open(os.path.join(sdir, "stats.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    entry = {"pass": n, "timestamp": ts, "hash": None,
             "short_hash": None, "board_file": board_rel, "dir": tag,
             "renders": renders, "layers": layers, "stats": stats,
             "description": a.description, "note": a.note}
    doc["passes"].append(entry)
    with open(PASSES_JSON, "w") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")

    md = open(PASSES_MD).read() if os.path.exists(PASSES_MD) else \
        "# Pass log\n\n<!-- next-pass -->\n"
    block = (f"### Pass {n} — {ts} · commit `pending`\n\n"
             f"Board: `{board_rel}` · Commit: `pending`\n\n"
             f"{a.description}\n\n{stats_line(stats)}\n"
             + (f"\n{a.note}\n" if a.note else ""))
    if "<!-- next-pass -->" in md:
        md = md.replace("<!-- next-pass -->",
                        block + "\n<!-- next-pass -->", 1)
    else:
        md += "\n" + block
    with open(PASSES_MD, "w") as f:
        f.write(md)

    page_rel = write_pass_page(entry)

    staged, left = stage_pass_files(board_rel, f"history/{tag}",
                                    page_rel)
    if left:
        print("not staged (not pass files): " + ", ".join(left))
    git("commit", "-q", "-m", f"pass {n:04d}: {a.description}")
    full = git("rev-parse", "HEAD")
    short = full[:7]
    print(f"committed {short}: pass {n:04d}: {a.description} "
          f"({len(staged)} files)")

    # bookkeeping: record the pass commit's own hash in the log
    doc = json.load(open(PASSES_JSON))
    for p in doc["passes"]:
        if p["pass"] == n:
            p["hash"], p["short_hash"] = full, short
            write_pass_page(p)
    with open(PASSES_JSON, "w") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    md = open(PASSES_MD).read()
    head, sep, tail = md.rpartition(f"### Pass {n} — ")
    assert sep, "pass heading not found in PASSES.md"
    tail = tail.replace("commit `pending`", f"commit `{short}`", 1)
    tail = tail.replace("Commit: `pending`", f"Commit: `{full}`", 1)
    with open(PASSES_MD, "w") as f:
        f.write(head + sep + tail)
    git("add", "--", "history/passes.json", "history/PASSES.md",
        page_rel)
    git("commit", "-q", "-m", f"pass {n:04d}: record commit hash")
    print(f"pass {n} recorded as commit {full}")
    print("only step remaining: git push")
    return 0


if __name__ == "__main__":
    sys.exit(main())
