import json, os
ROOT = "/home/hatch/workspace/pdlvds-cifix"
idx = {e["short_hash"]: e for e in json.load(open(os.path.join(ROOT, "history/index.json")))}

def from_index(h, **over):
    e = idx[h]
    st = dict(e["stats"]); st.update(over)
    return {"timestamp": e["timestamp"], "hash": e["hash"], "short_hash": e["short_hash"],
            "dir": e["dir"], "renders": e["renders"], "layers": e.get("layers"),
            "stats": st}

NR = {"nets_routed": None, "nets_total": None, "pins_failed": None,
      "clearance_violations": None, "unconnected_nets": None, "audit_verdict": None}

passes = []

p = from_index("d0c0bca", pins_failed=None)
p.update(board_file="hw/pdlvds_rx.kicad_pcb",
  description="Placement only: 144 footprints placed, GND zones and the HV isolation slot drawn, saved unrouted \u2014 the routing run was interrupted by a VM replacement. First committed board state; 0 of 112 nets routed.",
  note="Snapshot renders were made later from the board as committed at d0c0bca.")
passes.append(p)

p = from_index("3ac1a43")
p.update(board_file="hw/pdlvds_rx.kicad_pcb",
  description="First committed routed board. Router gains neck-down where wide tracks meet fine-pitch pads and power-first net ordering (HV > power > LVDS > signals) \u2014 the fixes for the uncommitted v1/v2 failures (see gaps). 57 of 112 nets fully routed, 90 pins failed; no audit file was committed with this pass, so clearance violations and unconnected nets are not recorded.",
  note="")
passes.append(p)

p = from_index("41d7196")
p.update(board_file="hw/pdlvds_rx.kicad_pcb",
  description="Goal-cell exemption fix: a net's own target cells no longer count as blocked for it. 67 of 112 nets fully routed, 59 pins failed. The clearance figure (454) is the audit's violating-pair count as recorded in commit f8b9d1c \u2014 no audit file was committed with the pass itself \u2014 and the unconnected-net count was not recorded.",
  note="")
passes.append(p)

p = from_index("fb2acf7")
p.update(board_file="hw/pdlvds_rx.kicad_pcb",
  description="Stricter clearance model in the router: vias never exempt, segment-midpoint tests, layer-aware HV clearance. Traded connections for correctness \u2014 58 of 112 nets fully routed, 74 pins failed. First pass with a full audit committed: 98 unconnected nets, 341 clearance violations.",
  note="")
passes.append(p)

passes.append({
  "timestamp": "2026-11-04T00:18:21Z",
  "hash": "162cc8762f15b8b432861d5dcaf89ba4ce13a7c0", "short_hash": "162cc87",
  "board_file": "hw/pdlvds_rx.repaired.kicad_pcb", "dir": None,
  "renders": None, "layers": None,
  "stats": {**NR, "unconnected_nets": 95, "clearance_violations": 445, "audit_verdict": "FAIL"},
  "description": "Repair pass over the pass-4 board \u2014 the first repair run to survive to a commit (attempts 1\u20133 were lost; see gaps). 82 isolated groups connected across 2 sweeps, but clearance violations rose 341 \u2192 445, so it was NOT adopted as the main board; the board is kept as the attempt artifact. Its verdict drove the next rewrite: the router's clearance model (grid-node + segment-midpoint tests) systematically under-protects against the audit's exact shape geometry.",
  "note": "Audit: results/audit-repair-attempt4.txt, committed with the pass (copper items 2,208). No renders were committed for this pass."})

p = from_index("b805fc3")
p.update(board_file="hw/pdlvds_rx.kicad_pcb",
  description="Router rewritten with an exact clearance model \u2014 per-segment shape-distance tests in blocked(), zero slack, parity with the audit \u2014 and run full-board from the placed board: 30 of 112 nets fully routed, 144 pins failed, 83 unconnected nets, 64 clearance violations, none of them involving router-emitted geometry (46 known placement pad pairs + 18 zone-involved). Model proven; connectivity is what remains. Adopted as the main board.",
  note="Audit: results/audit-v6-attempt1.txt (copper items 1,588).")
passes.append(p)

p = from_index("67722e0", pins_failed=None)
p.update(board_file="hw/pdlvds_rx.repaired6.kicad_pcb",
  description="Repair over the pass-6 board, with two-segment fanout escapes for pads sitting on grid boundaries: 45 groups connected, unconnected nets 83 \u2192 62, clearance violations unchanged at 64. Board kept as hw/pdlvds_rx.repaired6.kicad_pcb.",
  note="Audit: results/audit-repair6-attempt1.txt, committed with the pass (copper items 2,115). Pins-failed is recorded as not recorded: no figure exists in this pass's own records (the old gallery index carried 74, parsed from a stale build log, not from this pass).")
passes.append(p)

passes.append({
  "timestamp": "2026-11-04T08:21:31Z",
  "hash": "f2b2fbebc1693e7055479a407f3cbc098f60b14d", "short_hash": "f2b2fbe",
  "board_file": "hw/pdlvds_rx.repaired6b.kicad_pcb", "dir": None,
  "renders": None, "layers": None, "stats": dict(NR),
  "description": "Bundled change \u2014 two strategy changes in a single commit, the practice this counter replaces: diagonal moves added to the repair router AND the repair re-run over the pass-7 board. Result: 0 groups connected, no progress, not adopted. The commit's real payload is the per-pin diagnosis of the residue (results/diagnose-repaired6b.txt): of 99 isolated groups, 50 NO_EXIT, 16 POCKET, 20 WIDE_NO_GOAL, 13 REACHES \u2014 pads boxed in by placement, which is what pass 9 changes.",
  "note": "Board saved as hw/pdlvds_rx.repaired6b.kicad_pcb (1,587 tracks per results/repair6-attempt2.log). No audit was committed for this pass, so unconnected nets and clearance violations are not recorded. No renders were committed."})

passes.append({
  "timestamp": "2026-11-04T08:30:34Z",
  "hash": "e8a09549b812b52075500880970cce009af8e59f", "short_hash": "e8a0954",
  "board_file": "hw/pdlvds_rx.moved.kicad_pcb", "dir": None,
  "renders": None, "layers": None,
  "stats": {**NR, "unconnected_nets": 69, "clearance_violations": 64, "audit_verdict": "FAIL"},
  "description": "Placement change, answering pass 8's diagnosis: the U7/U12/L2/X1 cluster is moved on the pass-7 board to unbox pads that had no exit \u2014 24 pad pairs removed, 0 added. Board saved as hw/pdlvds_rx.moved.kicad_pcb.",
  "note": "Audit: results/audit-moved.txt, committed with the pass (copper items 1,392). No renders were committed for this pass."})

p = from_index("d489c78", pins_failed=None)
p.update(board_file="hw/pdlvds_rx.movedr.ckpt1.kicad_pcb",
  description="Repair resumed over the placement-revised board (pass 9) and \u2014 the first pass committed under the sharpened rule \u2014 committed at checkpoint 1 of the run instead of at run end: 111 groups connected, unconnected nets 69 \u2192 49. The audit committed with the checkpoint reads 1,435 clearance violations on 3,424 copper items; checkpoint saves did not refill zones at the time (fixed in cabbebc), and the figure is recorded exactly as the committed audit states it \u2014 a mid-run checkpoint state, not a finished-board audit. The run was still in progress when this was committed.",
  note="Audit: results/audit-repair6-attempt3-ckpt1.txt, committed with the pass. Pins-failed not recorded (the old gallery index's 74 came from the same stale build-log parse as pass 7's).")
passes.append(p)

for i, p in enumerate(passes, 1):
    p["pass"] = i
    p.move_to_end("pass", last=False)

doc = {
  "version": 1,
  "rule": "A pass is a commit that produced a new board state (a routing or placement change to a hw/*.kicad_pcb file). Passes are numbered sequentially in commit order; pass 1 is the first committed board state. Runs whose boards were never committed are not numbered \u2014 they are listed under gaps. Strategy changes live in each entry's description (the changelog), never in the numbering.",
  "passes": passes,
  "gaps": [
    {"label": "router v1 run (commit dc6a010, 2026-11-03T19:39:29Z)",
     "note": "Board routed in memory only; the commit carries router code, no board. Its 125 failed pins are known only from later commit messages (passes 2\u20133). Not numbered."},
    {"label": "router v2 run (commit c79defe, 2026-11-03T20:10:21Z)",
     "note": "Wide-nets-first ordering; board never committed and no result tally recorded. Not numbered."},
    {"label": "repair attempts 1\u20133 over the pass-4 board (commits 2add453, 0c20958, 04c90b4)",
     "note": "Attempt 1's board was lost at save; attempt 2 connected 82 groups in memory, then crashed at the same save (variable `path` shadowing the board path \u2014 root cause proven in 0c20958, which also retro-explains attempt 1); attempt 3 was killed by a VM replacement mid-sweep (04c90b4). The commits carry code and logs but no board. Pass 5 is repair attempt 4, the first to be committed. Not numbered."},
    {"label": "in-flight run state lost to a VM replacement (commit 8d39045)",
     "note": "Both /tmp scratch trees (v6 routing and the Freerouting line), with their logs and checkpoints, were lost; any board states in them were never committed. Scratch state moved into the workspace afterwards. Not numbered."},
    {"label": "Freerouting baseline line",
     "note": "No board produced by Freerouting has ever been committed (the native CLI build is dead \u2014 8d39045; the JVM/AppImage line produced no committed board either), so it holds no pass numbers. If it ever produces a committed board state, it takes the next number like everything else."}
  ]
}
out = os.path.join(ROOT, "history/passes.json")
with open(out, "w") as f:
    json.dump(doc, f, indent=2); f.write("\n")
print("wrote", out, "passes:", len(passes))
for p in passes: print(p["pass"], p["short_hash"], p["timestamp"], p["stats"])
