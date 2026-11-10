import json, os
ROOT = "/home/hatch/workspace/pdlvds-cifix"
doc = json.load(open(os.path.join(ROOT, "history/passes.json")))

def nr(v): return "not recorded" if v is None else str(v)
def stats_line(st):
    nets = nr(st.get("nets_routed"))
    if st.get("nets_routed") is not None and st.get("nets_total"):
        nets = f"{st['nets_routed']} of {st['nets_total']}"
    return (f"Nets fully routed: {nets} · Pins failed: {nr(st.get('pins_failed'))} · "
            f"Clearance violations: {nr(st.get('clearance_violations'))} · "
            f"Unconnected nets: {nr(st.get('unconnected_nets'))} · "
            f"Audit verdict: {nr(st.get('audit_verdict'))}")

L = []
L.append("# Pass log — the layout history")
L.append("")
L.append("One monotonic counter for all layout work: **pass 1, pass 2,")
L.append("pass 3, …** A pass is a commit that produced a new board state")
L.append("(a routing or placement change to a `hw/*.kicad_pcb` file),")
L.append("numbered in commit order; pass 1 is the first committed board")
L.append("state. Strategy changes are described in each pass's changelog")
L.append("line below — never encoded in names. Named families from before")
L.append("the counter (\"router v3\", \"repair6 attempt 1\", \"v6 + diagonals\")")
L.append("survive only inside the descriptions, as history.")
L.append("")
L.append("Machine-readable twin: `history/passes.json` (the site reads it).")
L.append("New passes are added by `scripts/commit_pass.py` — one command")
L.append("that audits, renders, logs and commits. Numbers are never")
L.append("reused or reordered; a number, once committed, is permanent.")
L.append("Anything never measured is written as \"not recorded\" — numbers")
L.append("are never invented.")
L.append("")
L.append("## The passes")
L.append("")
for p in doc["passes"]:
    L.append(f"### Pass {p['pass']} — {p['timestamp']} · commit `{p['short_hash']}`")
    L.append("")
    L.append(f"Board: `{p['board_file']}` · Commit: `{p['hash']}`")
    L.append("")
    L.append(p["description"])
    L.append("")
    L.append(stats_line(p["stats"]))
    if p.get("note"):
        L.append("")
        L.append(p["note"])
    L.append("")
L.append("<!-- next-pass -->")
L.append("")
L.append("## Gaps — runs that were never committed, and so have no number")
L.append("")
L.append("The counter only counts committed board states. These runs")
L.append("happened — the record of them is in the commits and files named")
L.append("— but their boards were never committed, so they hold no pass")
L.append("number. Listing them is the honest accounting of what the")
L.append("sequence misses:")
L.append("")
for g in doc["gaps"]:
    L.append(f"- **{g['label']}** — {g['note']}")
L.append("")
L.append("## Reconciliation with the provisional count in docs/00-status.md")
L.append("")
L.append("Commit `81b2942` (\"Pass numbering\" section of docs/00-status.md)")
L.append("recorded d489c78 provisionally as \"pass 14\", counting the five")
L.append("uncommitted runs in the gaps above (router v1, router v2, repair")
L.append("attempts 1–3) as passes and not counting the placed board.")
L.append("That section states this log is authoritative and later entries")
L.append("reconcile. Under the rule above, d489c78 is **pass 10** (an")
L.append("offset of −4), and the next pass is **pass 11**. Any \"pass 15\"")
L.append("subject written against the provisional count refers to what")
L.append("is pass 11 here.")
L.append("")
open(os.path.join(ROOT, "history/PASSES.md"), "w").write("\n".join(L))
print("PASSES.md written")
