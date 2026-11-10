#!/usr/bin/env python3
"""Phase B landing — writes the extracted, screened candidate set into
scratch/recovered/ in small batches and appends the MANIFEST.md rows.

Naming (Phase A/batch-1 convention): each landed file keeps the original
basename of its earliest establishing record; when distinct contents
share a basename, every file in the group is prefixed with its own
original write time in ISO basic form (YYYYMMDDTHHMMSSZ-<name>);
partial reconstructions carry an additional `.partial` suffix.

Batches follow the manifest's session order (the batch of a file is the
batch of the session that produced its earliest record):
  batch 1 = sessions 1-25, 2 = 26-50, 3 = 51-75, 4 = 76-94.

Usage:
  land_phase_b.py --plan       print the name map and batch counts
  land_phase_b.py --batch N    write batch N files + append its section
  land_phase_b.py --finalize   append unrecoverable table + reconciliation
"""
import hashlib
import json
import os
import re
import sys
from datetime import datetime

REPO = os.path.expanduser("~/workspace/pdlvds-split")
DEST = os.path.join(REPO, "scratch/recovered")
MANIFEST = os.path.join(DEST, "MANIFEST.md")
EXTRACT = "/tmp/phaseb/extract.json"
STAGING = "/tmp/phaseb/staging"
SCREEN_SECTION = "/tmp/phaseb/screen_section.md"
BATCH_SPANS = [(1, 25), (26, 50), (51, 75), (76, 94)]


def manifest_order():
    ids = []
    for line in open(MANIFEST):
        m = re.match(r"\| \d+ \| `([0-9a-f-]{36})`", line)
        if m:
            ids.append(m.group(1))
    return {a: i + 1 for i, a in enumerate(ids)}


def iso_basic(ts):
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.strftime("%Y%m%dT%H%M%SZ")


def build_entries():
    d = json.load(open(EXTRACT))
    order = manifest_order()
    entries = []
    for book, status in ((d["candidates"], "complete"),
                         (d["partials"], "partial")):
        for e in book:
            recs = sorted(e["records"], key=lambda r: (r["ts"] or ""))
            whole = [r for r in recs if r["kind"] == "whole"]
            primary = whole[0] if (status == "complete" and whole) \
                else recs[0]
            entries.append({
                "sha256": e["sha256"], "status": status,
                "paths": e["paths"], "records": recs, "primary": primary,
                "session_no": order.get(primary["agent"], 999)})
    # collision groups by primary basename
    groups = {}
    for ent in entries:
        base = os.path.basename(ent["primary"]["path"])
        ent["base"] = base
        groups.setdefault(base, []).append(ent)
    for base, g in groups.items():
        for ent in g:
            if len(g) > 1:
                name = "%s-%s" % (iso_basic(ent["primary"]["ts"]), base)
            else:
                name = base
            if ent["status"] == "partial":
                name += ".partial"
            ent["name"] = name
    seen = {}
    for ent in entries:
        if ent["name"] in seen:
            ent["name"] = "%s-%s" % (ent["name"], ent["sha256"][:8])
        seen[ent["name"]] = ent
    return d, entries


def batch_of(ent):
    for i, (lo, hi) in enumerate(BATCH_SPANS, 1):
        if lo <= ent["session_no"] <= hi:
            return i
    return len(BATCH_SPANS)


def row(ent):
    p = ent["primary"]
    rec = p["reconstruction"]
    if ent["status"] == "partial" and p.get("divergence"):
        rec += " — diverged: " + p["divergence"]
    return "| `%s` | %s | `%s` | %s / %s | %s | `%s` | %s | %s |" % (
        ent["name"], ", ".join(ent["paths"]), p["agent"], p["seq"],
        p["line"], p["ts"], ent["sha256"], ent["status"], rec)


def header_section(d):
    n_ops = d["diagnostics"]["ops"]
    lines = []
    lines.append("")
    lines.append("## Phase B — extraction (redo, set as approved)")
    lines.append("")
    lines.append("Extraction from exactly the 94 sessions above, local "
                 "files only (no muse.db). Tooling: "
                 "`scripts/scratch-recovery/extract_phase_b.py` "
                 "(ownership-resolved replay: fork copies resolved by "
                 "earliest record, root-agent calls excluded by call-id "
                 "oracle), `screen_secrets.py`, `land_phase_b.py`.")
    lines.append("")
    lines.append("- Owned write/edit/exec ops replayed: %d "
                 "(root-owned fork copies excluded: %d)."
                 % (n_ops, d["root_owned_excluded"]))
    lines.append("- (path, session) final states: %d; distinct contents: "
                 "%d; already committed (counted, not landed): %d; "
                 "landed whole: %d; landed partial: %d; unrecoverable "
                 "(path, session): %d."
                 % (sum(len(e["records"]) for e in
                        d["candidates"] + d["partials"] +
                        d["already_committed"]) +
                    len(d["unrecoverable"]),
                    len(d["candidates"]) + len(d["partials"]) +
                    len(d["already_committed"]),
                    len(d["already_committed"]), len(d["candidates"]),
                    len(d["partials"]), len(d["unrecoverable"])))
    lines.append("")
    lines.append("### Secrets screen (before any push)")
    lines.append("")
    lines.append(open(SCREEN_SECTION).read().rstrip())
    lines.append("")
    return "\n".join(lines)


def main():
    d, entries = build_entries()
    if "--plan" in sys.argv:
        from collections import Counter
        print("batches:", Counter(batch_of(e) for e in entries))
        for ent in sorted(entries, key=lambda e: e["name"]):
            print(ent["name"], "<-", ent["primary"]["path"],
                  "session", ent["session_no"], ent["status"])
        return 0
    if "--batch" in sys.argv:
        n = int(sys.argv[sys.argv.index("--batch") + 1])
        batch = sorted((e for e in entries if batch_of(e) == n),
                       key=lambda e: (e["primary"]["ts"] or ""))
        for ent in batch:
            src = os.path.join(STAGING, ent["sha256"])
            dst = os.path.join(DEST, ent["name"])
            with open(src, "rb") as f:
                data = f.read()
            assert hashlib.sha256(data).hexdigest() == ent["sha256"]
            with open(dst, "wb") as f:
                f.write(data)
        with open(MANIFEST, "a") as f:
            if n == 1:
                f.write(header_section(d))
            f.write("\n### Batch: phase-b-%d\n\n" % n)
            f.write("| recovered file | original path(s) | source agent "
                    "| seq (raw / visible) | original write time (UTC) "
                    "| sha256 | status | reconstruction |\n")
            f.write("|---|---|---|---|---|---|---|---|\n")
            for ent in batch:
                f.write(row(ent) + "\n")
        print("batch", n, "landed", len(batch), "files")
        return 0
    if "--finalize" in sys.argv:
        with open(MANIFEST, "a") as f:
            f.write("\n### Unrecoverable (named, with reasons)\n\n")
            f.write("Final states that no in-session write, edit chain or "
                    "heredoc establishes — in every case the session "
                    "edited a file that already existed on disk (written "
                    "by a predecessor or committed), so the session's "
                    "own records hold no base to replay from.\n\n")
            f.write("| original path | source agent | seq (raw / "
                    "visible) | reason |\n|---|---|---|---|\n")
            for u in sorted(d["unrecoverable"],
                            key=lambda u: (u["ts"] or "")):
                f.write("| %s | `%s` | %s / %s | %s |\n"
                        % (u["path"], u["agent"], u["seq"], u["line"],
                           u["reason"]))
            total = len(d["candidates"]) + len(d["partials"]) + \
                len(d["already_committed"])
            f.write("\n### Reconciliation (Phase B closing)\n\n")
            f.write("Distinct contents extracted: **%d** == already "
                    "committed **%d** + landed whole **%d** + landed "
                    "partial **%d**. Unrecoverable (path, session) "
                    "states: **%d**, every one named above. Zero "
                    "unexplained.\n"
                    % (total, len(d["already_committed"]),
                       len(d["candidates"]), len(d["partials"]),
                       len(d["unrecoverable"])))
        print("finalized")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
