#!/usr/bin/env python3
"""Write stats.txt into the three backfilled pass dirs and update
their history/passes.json entries (dir, renders, layers, note)."""
import json, os

ROOT = "/home/hatch/workspace/pdlvds-chartv2"
SENTENCE = ("Renders backfilled on 2026-11-04 by rendering the board "
            "file as of this pass's commit; not contemporaneous with "
            "the pass.")
METHOD = ("zones deleted from temp pcbnew copy (3 zones removed; "
          "source board unmodified)")
LABELS = {5: "pass 5 — repair pass over pass 4 (repair attempt 4)",
          8: "pass 8 — repair re-run with diagonal moves over pass 7",
          9: "pass 9 — placement revision (U7/U12/L2/X1 moved)"}
RENDERS = {"top": "board-top.svg", "bottom": "board-bottom.svg"}
LAYERS = {"F.Cu": "layer-FCu.svg", "In1.Cu": "layer-In1Cu.svg",
          "In2.Cu": "layer-In2Cu.svg", "B.Cu": "layer-BCu.svg"}
PALETTE = {"F.Cu": "#FF3B30", "In1.Cu": "#FF9500",
           "In2.Cu": "#34C759", "B.Cu": "#0A84FF"}

pj = os.path.join(ROOT, "history", "passes.json")
doc = json.load(open(pj))


def fmt(v):
    return "not recorded" if v is None else str(v)


for e in doc["passes"]:
    n = e["pass"]
    if n not in LABELS:
        continue
    tag = f"pass-{n:04d}"
    st = e["stats"]
    nets = fmt(st.get("nets_routed"))
    if st.get("nets_routed") is not None and st.get("nets_total"):
        nets += f" of {st['nets_total']}"
    lines = [
        f"label: {LABELS[n]}",
        f"timestamp (UTC): {e['timestamp']}",
        f"commit: {e['hash']}",
        f"commit (short): {e['short_hash']}",
        f"board file: {e['board_file']}",
        "renders: board-top.svg, board-bottom.svg",
        "render layers: top: F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS; "
        "bottom: B.Cu,In2.Cu,In1.Cu,F.Cu,B.SilkS",
        "layer renders: " + ", ".join(
            f"{layer}={LAYERS[layer]} ({PALETTE[layer]})"
            for layer in LAYERS),
        f"route-only renders: {METHOD}",
        f"nets fully routed: {nets}",
        f"pins failed: {fmt(st.get('pins_failed'))}",
        f"clearance violations: {fmt(st.get('clearance_violations'))}",
        f"unconnected nets: {fmt(st.get('unconnected_nets'))}",
        f"audit verdict: {fmt(st.get('audit_verdict'))}",
        f"note: {SENTENCE}",
    ]
    with open(os.path.join(ROOT, "history", tag, "stats.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    e["dir"] = tag
    e["renders"] = dict(RENDERS)
    e["layers"] = dict(LAYERS)
    assert SENTENCE not in e["note"]
    e["note"] = e["note"].rstrip() + " " + SENTENCE
    print(f"pass {n}: dir={tag}, note appended")

with open(pj, "w") as f:
    json.dump(doc, f, indent=2)
    f.write("\n")
print("passes.json rewritten")
