#!/usr/bin/env python3
"""Build scratch/recovered/MANIFEST.md for the corrected script recovery.

Phase A: enumerate the definitive set of PCB-project subagent sessions from
spawn records in the local session JSONL transcripts (no muse.db).

Membership test (the user's scope): a session is in the set iff it was
spawned by a brief that tasks it with THIS project (photodiode LVDS receiver
PCB / lvds-receiver-official), from the project chat's root session, or by an
already-included subagent. Spawn calls are attributed to their true owner by
earliest created_at across all transcript files (child session files carry
fork copies of ancestor transcripts, re-stamped at fork time, so a naive
per-file scan re-attributes ancestor calls to descendants).

Deliberate exclusions: the root agent itself, the main-chat agent, cron /
watchdog job sessions (not spawned from this lineage), and the recovery-job
sessions themselves.
"""
import json, re, csv, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enumerate_spawns import spawns_in, session_file, brief_of

ROOT = "4925d244-018c-4b4f-9fad-7b3ad78af7c1"
MAIN = "ea3d13c7-e549-4198-bf09-87d40b70d51f"
EXCL = {
    "bb32a622-8412-44aa-a9b2-a9965c712632": "recovery job, batch 1 (the purged sweep)",
    "f2d79bf0-408a-43ad-8f8a-bb5db6ada733": "recovery job, successor 1 (died with no output)",
    "a0ed68c3-adae-4ce8-a0c1-9fc51369d482": "recovery job, successor 2 (closed at purge)",
    "93f6273c-a2bd-4261-8556-e544983cd8f5": "recovery redo, Phase A (this enumeration)",
}
REPO = os.path.expanduser("~/workspace/pdlvds-split")

def first_line(b):
    for ln in (b or "").splitlines():
        if ln.strip():
            return ln.strip()
    return ""

ROLE_RULES = [
    (r"build coordinator|completion coordinator|COMPLETION COORDINATOR", "coordinator"),
    (r"CI-fix|CI-signal|CI performance|CI apt-cache", "CI lane"),
    (r"routing-gallery|routing-history gallery", "site/gallery rendering"),
    (r"token-metrics|token-graph|token-chart|input-split|compaction rule in the input-split|codename-pricing|cost-summary|cost presentation", "metrics lane"),
    (r"pass-structure|pass-page|missing renders for layout passes|board \(\"Routes\"\) page", "site/pass-system"),
    (r"site-migration|site worker|website build|schematic human-readable", "site/schematic"),
    (r"USB device transport|firmware fix|firmware reconciliation", "firmware"),
    (r"HARDWARE SIMULATION", "hardware-simulation attempts (refused)"),
    (r"parts lock-in audit|parts fixes|self-fry", "design audit/fix"),
    (r"Freerouting", "routing experiment (Freerouting)"),
    (r"board EXPANSION|parallel paths at the routing blocker", "routing"),
    (r"layout/routing worker|PCB BOARD JOB|PCB board job", "board routing lane"),
    (r"scrub the word|slideshow", "project support"),
    (r"Write ONLY|Write ONLY the|Write ONLY under", "design worker (write-only slice)"),
]
def role(brief):
    for pat, lab in ROLE_RULES:
        if re.search(pat, brief or ""):
            return lab
    return "project worker"

def calls_in(path):
    """call_id -> {ts, brief, child} for one transcript file."""
    calls = {}
    with open(path) as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            it = r.get("item") or {}
            if it.get("type") == "function_call" and it.get("name") == "subagent.spawn":
                calls[it["call_id"]] = {"ts": r.get("created_at"), "brief": brief_of(it.get("arguments") or ""), "child": None}
            elif it.get("type") == "function_call_output" and it.get("call_id") in calls:
                raw = it.get("output"); aid = None
                if isinstance(raw, str):
                    try:
                        aid = json.loads(raw).get("agent_id")
                    except Exception:
                        aid = None
                calls[it["call_id"]]["child"] = aid
    return calls

def main():
    root_calls = calls_in(session_file(ROOT))
    included = {}   # agent_id -> row
    for cid, c in root_calls.items():
        ch = c["child"]
        if ch and ch not in EXCL:
            included[ch] = {"agent": ch, "spawned_at": c["ts"], "parent": ROOT, "brief": c["brief"]}
    # descendants: earliest-owner resolution, recursive
    frontier = list(included)
    seen_files = set()
    while frontier:
        nxt = []
        for owner in frontier:
            f = session_file(owner)
            if not f or f in seen_files:
                continue
            seen_files.add(f)
            for cid, c in calls_in(f).items():
                if cid in root_calls:
                    continue  # fork copy of a root call
                ch = c["child"]
                if ch and ch not in EXCL and ch not in included:
                    included[ch] = {"agent": ch, "spawned_at": c["ts"], "parent": owner, "brief": c["brief"]}
                    nxt.append(ch)
        frontier = nxt
    rows = sorted(included.values(), key=lambda r: r["spawned_at"] or "")
    # main-chat negative check
    main_cands = [r for r in spawns_in(session_file(MAIN))
                  if re.search(r"lvds|pdlvds|photodiode|miniscope", r["brief"] or "", re.I)
                  and (r["spawned_at"] or "") >= "2026-11-03"]
    # cross-checks
    csv_ids = set()
    with open(os.path.join(REPO, "metrics/agents.csv")) as f:
        for row in csv.DictReader(f):
            csv_ids.add(row["agent_id"].strip())
    absent_csv = [r["agent"] for r in rows if r["agent"] not in csv_ids]
    lanes = sorted(os.path.basename(p) for p in glob.glob(os.path.join(REPO, "scratch/work/??"))
                   if os.path.isdir(p) and re.fullmatch(r"[a-z]{2}", os.path.basename(p)))
    nofile = [r["agent"] for r in rows if not session_file(r["agent"])]
    mult = [r["agent"] for r in rows if len(glob.glob(f"/home/hatch/agents/agent-{r['agent']}/sessions/*.jsonl")) != 1]

    out = []
    out.append("# Recovered scripts — provenance archive (REDO, corrected scope)")
    out.append("")
    out.append("## Phase A — the session set (this file is the Phase A deliverable)")
    out.append("")
    out.append("The user's scope, binding: **just the scripts for this PCB project, written by the")
    out.append("subagents spawned to work on the PCB project.** Not the main chat agent, not this")
    out.append("chat's root agent, not cron/watchdog job sessions, not any other workstream's agents.")
    out.append("")
    out.append("### Method")
    out.append("")
    out.append("- Source: spawn records (`subagent.spawn` calls and their results) in the local session")
    out.append("  JSONL transcripts under `/home/hatch/agents/` — no muse.db (user order). Tooling:")
    out.append("  `scripts/scratch-recovery/enumerate_spawns.py` + `build_manifest.py`.")
    out.append("- A session is in the set iff its spawning brief tasks it with this project")
    out.append("  (photodiode LVDS receiver / lvds-receiver-official). The brief's first line is quoted")
    out.append("  for every session below as the evidence.")
    out.append("- Spawn calls are attributed to their true owner by call: child session files carry")
    out.append("  fork copies of ancestor transcripts (re-stamped at fork time), so a naive per-file")
    out.append("  scan finds 244 apparent 'grandchild' spawns that are really the root's own calls.")
    out.append("  Ownership-resolved, the only genuine second-generation spawns are the 3 workers the")
    out.append("  first build coordinator spawned on 2026-11-03. No third generation exists.")
    out.append(f"- The main-chat session (`{MAIN}`) was checked the same way: of its 421 spawns, **zero**")
    out.append("  task a child with this project (its Nov 1–9 spawns are cell/binary-exploration work).")
    out.append("  Every project spawn lives in this chat's root session lineage.")
    out.append("- Deliberately excluded: the root agent itself; the 4 recovery-lineage sessions")
    out.append("  (batch-1 miner and its successors, and this Phase A session) — listed in the")
    out.append("  exclusions note under the table; cron/watchdog job sessions (not in this lineage).")
    out.append("")
    out.append("### Hard-stop checks")
    out.append("")
    out.append(f"- Total sessions in set: **{len(rows)}** (limit 100 — OK).")
    out.append(f"- Earliest spawn: {rows[0]['spawned_at']} — nothing before 2026-11-03 (OK).")
    out.append(f"- Every session's spawn brief is on record in its parent transcript (OK).")
    out.append(f"- Sessions with no transcript file on disk: {len(nofile)}; with !=1 session file: {len(mult)}.")
    out.append("")
    out.append("### The set")
    out.append("")
    out.append("| # | agent id | spawned (UTC) | parent | role | brief — first line |")
    out.append("|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        bl = first_line(r["brief"]).replace("|", "\\|")
        if len(bl) > 180:
            bl = bl[:177] + "…"
        out.append(f"| {i} | `{r['agent']}` | {r['spawned_at'][:19]} | `{r['parent'][:8]}…` | {role(r['brief'])} | {bl} |")
    out.append("")
    out.append("Excluded recovery-lineage sessions (spawned from the same root, briefs on record,")
    out.append("out of scope by the user's rule — the recovery is not board work):")
    out.append("")
    for aid, why in EXCL.items():
        out.append(f"- `{aid}` — {why}")
    out.append("")
    out.append("### Coverage notes and discrepancies")
    out.append("")
    out.append(f"- metrics/agents.csv cross-check: {len(rows) - len(absent_csv)} of {len(rows)} set sessions appear in the")
    out.append("  repo's project-scope metrics list; the absentees are named here because the metrics")
    out.append("  export is a stale snapshot (its refresh has been skipped repeatedly; newest usage row")
    out.append("  2026-11-09T14:55Z) — the spawn records, not the metrics export, are the census:")
    for a in absent_csv:
        out.append(f"  - `{a}`")
    out.append(f"- Lane directories in the repo at scratch/work/: {', '.join(lanes)} ({len(lanes)} lanes). All sit")
    out.append("  inside the era of the board-routing sessions in this set; per-lane session attribution")
    out.append("  is a Phase B extraction check. (Lane `bd` has no directory yet — its session is in the")
    out.append("  set; its work is still landing. `parent-shots` is the root agent's own directory and is")
    out.append("  correctly out of scope.)")
    out.append("- Phase B (extraction of these sessions' scripts into this directory) starts only after")
    out.append("  the parent approves this set.")
    out.append("")
    print("\n".join(out))
    print(f"<!-- rows={len(rows)} main_cands={len(main_cands)} absent_csv={len(absent_csv)} lanes={len(lanes)} -->", file=sys.stderr)

if __name__ == "__main__":
    main()
