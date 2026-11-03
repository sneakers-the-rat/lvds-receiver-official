#!/usr/bin/env python3
"""Snapshot one routing attempt into history/ for the site gallery.

Creates history/<UTC-timestamp>_<short-hash>/ containing:
  - board-top.svg / board-bottom.svg  (kicad-cli pcb export svg renders)
  - stats.txt                         (label, timestamps, hashes, stats)
and adds/updates the attempt's entry in history/index.json.

Stats are taken, in priority order, from explicit --flags, then parsed
from the audit file (results/pcb-audit.txt) and build log
(results/pcb_build.log). Anything not found is recorded as
"not recorded" — numbers are NEVER invented.

Idempotent per commit hash: re-running for a hash that already has an
entry replaces that entry (and its snapshot directory) instead of
duplicating it.

Usage:
  python3 scripts/snapshot_route.py --label "router v6"
  python3 scripts/snapshot_route.py --board /tmp/old.kicad_pcb \\
      --label "router v3" --hash 3ac1a43... --timestamp 2026-11-03T20:52:25Z \\
      --nets-routed 57 --nets-total 112 --pins-failed 90
  python3 scripts/snapshot_route.py --label "router v1" --no-board \\
      --hash dc6a010... --pins-failed 125 \\
      --note "no board was committed for this attempt"
"""
import argparse, json, os, re, shutil, subprocess, sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP_LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS"
BOTTOM_LAYERS = "B.Cu,In2.Cu,In1.Cu,F.Cu,B.SilkS"


def git(*args, cwd=ROOT):
    r = subprocess.run(["git", "-C", cwd, *args],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def parse_audit(path):
    """Pull the summary numbers out of a check_pcb audit file."""
    out = {}
    if not path or not os.path.exists(path):
        return out
    txt = open(path).read()
    m = re.search(r"unconnected nets:\s*(\d+)", txt)
    if m:
        out["unconnected_nets"] = int(m.group(1))
    m = re.search(r"clearance violations:\s*(\d+)", txt)
    if m:
        out["clearance_violations"] = int(m.group(1))
    m = re.search(r"PCB CHECK:\s*(\w+)", txt)
    if m:
        out["audit_verdict"] = m.group(1)
    return out


def parse_build_log(path):
    """Pull routing tallies out of a gen_pcb/router build log."""
    out = {}
    if not path or not os.path.exists(path):
        return out
    txt = open(path).read()
    m = re.findall(r"(\d+)\s*/\s*(\d+)\s+nets fully routed", txt)
    if m:
        out["nets_routed"], out["nets_total"] = (int(m[-1][0]),
                                                  int(m[-1][1]))
    m = re.findall(r"(\d+)\s+(?:pin connections|pins)\s+failed", txt)
    if m:
        out["pins_failed"] = int(m[-1])
    return out


def export_svg(board, out_path, layers, mirror):
    """Render one SVG via kicad-cli; return the layer spec actually
    used, or None on failure. Falls back to kicad-cli defaults."""
    base = ["kicad-cli", "pcb", "export", "svg", "-o", out_path,
            "--page-size-mode", "2", "--exclude-drawing-sheet"]
    if mirror:
        base.append("--mirror")
    for spec in (layers, None):
        cmd = base + (["--layers", spec] if spec else []) + [board]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(out_path):
            return spec or "kicad-cli defaults"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", default=os.path.join(ROOT, "hw",
                                                    "pdlvds_rx.kicad_pcb"))
    ap.add_argument("--no-board", action="store_true",
                    help="record an index entry with no renders "
                         "(attempts whose board was never committed)")
    ap.add_argument("--label", required=True)
    ap.add_argument("--hash", default=None,
                    help="commit hash (default: HEAD of this repo)")
    ap.add_argument("--timestamp", default=None,
                    help="ISO timestamp (default: the commit's own "
                         "timestamp, else now, UTC)")
    ap.add_argument("--history-dir", default=os.path.join(ROOT, "history"))
    ap.add_argument("--audit", default=os.path.join(ROOT, "results",
                                                    "pcb-audit.txt"))
    ap.add_argument("--build-log", default=os.path.join(ROOT, "results",
                                                        "pcb_build.log"))
    ap.add_argument("--no-parse", action="store_true",
                    help="do not parse audit/build-log for stats")
    ap.add_argument("--nets-routed", type=int)
    ap.add_argument("--nets-total", type=int)
    ap.add_argument("--pins-failed", type=int)
    ap.add_argument("--clearance-violations", type=int)
    ap.add_argument("--unconnected-nets", type=int)
    ap.add_argument("--audit-verdict")
    ap.add_argument("--note")
    a = ap.parse_args()

    full_hash = a.hash or git("rev-parse", "HEAD")
    if not full_hash:
        print("error: no commit hash available", file=sys.stderr)
        return 1
    short_hash = full_hash[:7]

    if a.timestamp:
        ts_raw = a.timestamp
    else:
        ts_raw = git("log", "-1", "--format=%cI", full_hash)
    if ts_raw:
        dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        dt = dt.astimezone(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    ts_iso = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    ts_dir = dt.strftime("%Y-%m-%dT%H%M%SZ")

    stats = {}
    if not a.no_parse:
        stats.update(parse_build_log(a.build_log))
        stats.update(parse_audit(a.audit))
    for key, val in [("nets_routed", a.nets_routed),
                     ("nets_total", a.nets_total),
                     ("pins_failed", a.pins_failed),
                     ("clearance_violations", a.clearance_violations),
                     ("unconnected_nets", a.unconnected_nets),
                     ("audit_verdict", a.audit_verdict)]:
        if val is not None:
            stats[key] = val
    for key in ("nets_routed", "nets_total", "pins_failed",
                "clearance_violations", "unconnected_nets",
                "audit_verdict"):
        stats.setdefault(key, None)

    os.makedirs(a.history_dir, exist_ok=True)
    index_path = os.path.join(a.history_dir, "index.json")
    entries = []
    if os.path.exists(index_path):
        entries = json.load(open(index_path))
    # idempotency: drop any previous entry (and dir) for this hash
    kept = []
    for e in entries:
        if e.get("hash") == full_hash:
            old = os.path.join(a.history_dir, e.get("dir", ""))
            if e.get("dir") and os.path.isdir(old):
                shutil.rmtree(old)
        else:
            kept.append(e)
    entries = kept

    dirname = f"{ts_dir}_{short_hash}"
    sdir = os.path.join(a.history_dir, dirname)
    os.makedirs(sdir, exist_ok=True)

    renders = None
    layers_used = None
    if not a.no_board:
        if not os.path.exists(a.board):
            print(f"error: board file not found: {a.board}",
                  file=sys.stderr)
            return 1
        top = export_svg(a.board, os.path.join(sdir, "board-top.svg"),
                         TOP_LAYERS, mirror=False)
        bottom = export_svg(a.board,
                            os.path.join(sdir, "board-bottom.svg"),
                            BOTTOM_LAYERS, mirror=True)
        if top and bottom:
            renders = {"top": "board-top.svg",
                       "bottom": "board-bottom.svg"}
            layers_used = f"top: {top}; bottom: {bottom}"
        else:
            print("warning: kicad-cli SVG export failed; entry will "
                  "carry no renders", file=sys.stderr)

    def fmt(v):
        return "not recorded" if v is None else str(v)

    lines = [
        f"label: {a.label}",
        f"timestamp (UTC): {ts_iso}",
        f"commit: {full_hash}",
        f"commit (short): {short_hash}",
        f"board file: {'none (no board committed)' if a.no_board else a.board}",
        f"renders: {'none' if not renders else 'board-top.svg, board-bottom.svg'}",
        f"render layers: {layers_used or 'not recorded'}",
        f"nets fully routed: {fmt(stats['nets_routed'])}"
        + (f" of {stats['nets_total']}" if stats['nets_total'] else ""),
        f"pins failed: {fmt(stats['pins_failed'])}",
        f"clearance violations: {fmt(stats['clearance_violations'])}",
        f"unconnected nets: {fmt(stats['unconnected_nets'])}",
        f"audit verdict: {fmt(stats['audit_verdict'])}",
        f"note: {a.note or ''}",
    ]
    with open(os.path.join(sdir, "stats.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    entry = {"timestamp": ts_iso, "hash": full_hash,
             "short_hash": short_hash, "label": a.label,
             "dir": dirname, "renders": renders,
             "stats": stats, "note": a.note or ""}
    entries.append(entry)
    entries.sort(key=lambda e: (e["timestamp"], e["hash"]))
    with open(index_path, "w") as f:
        json.dump(entries, f, indent=2)
        f.write("\n")
    print(f"snapshot: history/{dirname} "
          f"({a.label}, {short_hash}, renders="
          f"{'yes' if renders else 'no'})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
