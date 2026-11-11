#!/usr/bin/env python3
"""DRC signal gate for the in-progress board (scripts/ci.sh step 11).

Why this exists (user, 2026-11-03): while routing is unfinished, the
board legitimately has DRC violations, so failing CI on the raw count
makes CI permanently red — and a permanently red CI hides genuinely
broken pipeline steps. This gate restores the signal WITHOUT hiding
the board state. It fails the step (exit != 0) when:

  * TOOL HEALTH breaks — the report file is missing, empty,
    unparseable, has implausible/negative counts, or (while the
    baseline says the board is unfinished) reports a zero total item
    census. A silently broken DRC is exactly the failure mode this
    gate exists to catch; it is never waved through.
  * The counts REGRESS — violations or unconnected items rise above
    ci/drc-baseline.json BY MORE THAN the checker's own run-to-run
    jitter tolerance (routing got worse, or the checker changed
    behaviour; either must be seen).

Checker jitter (round 3, 2026-11-03): KiCad 8's DRC is not
perfectly deterministic — run 41751841325 measured 727/190 on the
IDENTICAL board blob (6a377ebc) that run 41750532660 had measured
at 726/190, and the round-2 ratchet fired REGRESSION on jitter
alone. The baseline therefore carries tolerance_violations /
tolerance_unconnected (5 / 2: sized from the observed ±1 with
headroom, far below any real routing regression, which moves
counts by tens). Three healthy outcomes, three wordings:

  * counts at or below baseline — "no regression";
  * above baseline but within tolerance — verdict PASS, reported
    as "within checker jitter tolerance (+N over baseline,
    tolerance +T)" so the drift stays visible in the log, the
    status JSON and the site panel;
  * above baseline + tolerance — REGRESSION, exit 1.

The baseline itself stays the reference measurement (726/190);
the tolerance is the jitter mechanism, never a quiet baseline
raise. Further drift beyond tolerance is real signal.

It exits 0 when the tool is healthy and counts are within
baseline + tolerance. That outcome is reported as BOARD STATE
("DRC (board in progress): ..."), never as "DRC passed".

End state: when routing completes, the baseline is set to 0/0 and the
same ratchet is a hard zero-tolerance gate by construction — the
census check is skipped when the baseline total is 0, and the
tolerances are forced to 0 when the baseline is 0/0, so a genuinely
clean report is the only pass.

Pinned exclusions (2026-11-11): four copper_edge_clearance items at
J1 are the Amphenol 12401610E4-2A manufacturer's own land pattern
(shell stakes and mounting hole at the board edge) — intended
geometry, not defects. They are recorded as DRC exclusions in
hw/pdlvds_rx.kicad_pro (which KiCad's GUI honours but kicad-cli's
count does not apply), and the SAME four strings are pinned in
ci/drc-baseline.json under "drc_exclusions". When --json-report is
given, this gate matches the JSON report's items against the
exclusions by (type, item UUIDs): an item that matches is reported
as excluded, never silently dropped; the verdict runs on the
remaining (effective) counts. The gate FAILS LOUDLY when the .pro
list differs from the pinned baseline list, when an exclusion
matches no report item (board geometry moved under it — re-review),
or when the text and JSON runs disagree beyond checker jitter.

Every run writes a JSON status file (default
results/drc-status.json) for the workflow's site status JSON, prints
the counts prominently to the job log, and appends a markdown block
to $GITHUB_STEP_SUMMARY when that variable is set.

Exit codes: 0 = healthy, no regression; 1 = regression above
baseline; 2 = tool-health failure (missing/empty/unparseable/
implausible report, or unreadable/invalid baseline).
"""
import argparse
import json
import os
import re
import sys

# Summary-line formats. The REPORT FILE written by KiCad 8 frames
# the lines in '**' and counts unconnected PADS ('** Found 190
# unconnected pads **'); the round-1 gate expected the bare console
# wording with 'items' and failed tool-health on the first real
# report (run 41750532660) — loudly, as designed, but wrong. Accept
# both framings and both nouns; the real captured report is a test
# fixture (ci/fixtures/drc-report-run41750532660.txt).
RE_VIOLATIONS = re.compile(r"(?:\*\*\s*)?Found (\d+) DRC violations(?:\s*\*\*)?")
RE_UNCONNECTED = re.compile(
    r"(?:\*\*\s*)?Found (\d+) unconnected (?:pads|items)(?:\s*\*\*)?")


def load_baseline(path):
    """Return (violations, unconnected, tol_violations,
    tol_unconnected, pinned_exclusions) or raise ValueError.
    Tolerances default to 0 when absent (pre-round-3 baseline files
    keep the strict any-rise-is-a-regression semantics);
    pinned_exclusions defaults to [] (pre-2026-11 baselines)."""
    with open(path) as f:
        data = json.load(f)
    v = data["violations"]
    u = data["unconnected"]
    if not isinstance(v, int) or not isinstance(u, int) or v < 0 or u < 0:
        raise ValueError(f"baseline counts must be non-negative ints, got {v!r}/{u!r}")
    tv = data.get("tolerance_violations", 0)
    tu = data.get("tolerance_unconnected", 0)
    if not isinstance(tv, int) or not isinstance(tu, int) or tv < 0 or tu < 0:
        raise ValueError(
            f"baseline tolerances must be non-negative ints, got {tv!r}/{tu!r}")
    pinned = data.get("drc_exclusions", [])
    if not isinstance(pinned, list) or not all(isinstance(s, str) for s in pinned):
        raise ValueError("baseline drc_exclusions must be a list of strings")
    return v, u, tv, tu, pinned


def _exclusion_key(entry):
    """'type|x|y|uuid1|uuid2' -> (type, frozenset({uuid1, uuid2})).
    The stored position is not part of the match (KiCad's own
    exclusion identity is type + item UUIDs)."""
    parts = entry.split("|")
    if len(parts) != 5:
        raise ValueError(f"malformed DRC exclusion entry: {entry!r}")
    return parts[0], frozenset(parts[3:5])


def apply_exclusions(json_path, pro_path, pinned):
    """Match a JSON DRC report's violations against the pinned
    exclusions. Returns (raw_violations, raw_unconnected,
    excluded_count, effective_violations). Raises ValueError on any
    inconsistency — every failure here is a tool-health failure,
    never a quiet pass."""
    if not os.path.exists(json_path):
        raise ValueError(f"DRC JSON report not produced: {json_path} does not exist")
    with open(json_path) as f:
        report = json.load(f)
    with open(pro_path) as f:
        pro = json.load(f)
    pro_excl = pro.get("board", {}).get("design_settings", {}) \
        .get("drc_exclusions", [])
    if sorted(pro_excl) != sorted(pinned):
        raise ValueError(
            "DRC exclusions in the .kicad_pro differ from the pinned "
            f"list in the baseline ({len(pro_excl)} vs {len(pinned)} "
            "entries) — an exclusion change must be reviewed in both "
            "places in the same commit")
    keys = {}
    for entry in pinned:
        keys.setdefault(_exclusion_key(entry), []).append(entry)
    matched = {k: 0 for k in keys}
    effective = 0
    for v in report.get("violations", []):
        k = (v.get("type"),
             frozenset(i.get("uuid") for i in v.get("items", [])))
        if k in matched:
            matched[k] += 1
        else:
            effective += 1
    unmatched = [e for k, entries in keys.items() if matched[k] == 0
                 for e in entries]
    if unmatched:
        raise ValueError(
            f"{len(unmatched)} pinned DRC exclusion(s) matched no "
            "report item — the board geometry moved under them; "
            f"re-review and update both lists: {unmatched}")
    excluded = sum(matched.values())
    return (len(report.get("violations", [])),
            len(report.get("unconnected_items", [])),
            excluded, effective)


def parse_report(path):
    """Return (violations, unconnected, census) or raise ValueError.

    census = violations + unconnected: the total item count the
    report itself attests. Both summary lines must be present —
    a partial parse means the report format changed or the run was
    truncated, which is a tool-health failure, not a pass.
    """
    if not os.path.exists(path):
        raise ValueError(f"DRC report not produced: {path} does not exist")
    with open(path, errors="replace") as f:
        text = f.read()
    if not text.strip():
        raise ValueError(f"DRC report is empty: {path}")
    mv = RE_VIOLATIONS.search(text)
    mu = RE_UNCONNECTED.search(text)
    if mv is None or mu is None:
        missing = []
        if mv is None:
            missing.append("'Found N DRC violations'")
        if mu is None:
            missing.append("'Found N unconnected pads/items'")
        raise ValueError(
            "DRC report unparseable: missing summary line(s) "
            + ", ".join(missing) + f" in {path}")
    v, u = int(mv.group(1)), int(mu.group(1))
    return v, u, v + u


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", default="results/drc-report.txt")
    ap.add_argument("--json-report", default=None,
                    help="JSON DRC report from the same board; when "
                         "given, pinned exclusions are matched by "
                         "UUID and the verdict runs on effective "
                         "counts")
    ap.add_argument("--pro", default="hw/pdlvds_rx.kicad_pro")
    ap.add_argument("--baseline", default="ci/drc-baseline.json")
    ap.add_argument("--out", default="results/drc-status.json")
    args = ap.parse_args(argv)

    status = {
        "report": args.report,
        "baseline_file": args.baseline,
        "tool_health": "unknown",
        "regression": None,
        "case": "unknown",
        "verdict": "unknown",
        "board_state": "",
    }

    def finish(code):
        # Always leave the status JSON + log/summary visibility,
        # whatever the verdict: a failure with no artefact is the
        # invisibility this gate exists to prevent.
        line = status["board_state"] or f"DRC: {status['verdict']}"
        print()
        print("=" * 72)
        print(line)
        print(f"DRC tool health: {status['tool_health']}; "
              f"regression: {status['regression']}; verdict: {status['verdict']}")
        print("=" * 72)
        out_dir = os.path.dirname(args.out)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(status, f, indent=2, sort_keys=True)
            f.write("\n")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a") as f:
                f.write(f"### KiCad DRC — board state\n\n{line}\n\n"
                        f"Tool health: {status['tool_health']} · "
                        f"verdict: {status['verdict']}\n")
        return code

    try:
        bv, bu, tv, tu, pinned = load_baseline(args.baseline)
    except Exception as e:
        status["tool_health"] = "FAIL"
        status["case"] = "tool_failure"
        status["verdict"] = "TOOL FAILURE"
        status["board_state"] = f"DRC TOOL FAILURE: baseline unreadable ({e})"
        return finish(2)
    # End state guard: a 0/0 baseline is the finished-board hard
    # gate — tolerances recorded in the file must not soften it.
    if bv == 0 and bu == 0:
        tv = tu = 0
    status["baseline_violations"] = bv
    status["baseline_unconnected"] = bu
    status["tolerance_violations"] = tv
    status["tolerance_unconnected"] = tu

    try:
        v, u, census = parse_report(args.report)
    except Exception as e:
        status["tool_health"] = "FAIL"
        status["case"] = "tool_failure"
        status["verdict"] = "TOOL FAILURE"
        status["board_state"] = f"DRC TOOL FAILURE: {e}"
        return finish(2)
    status["violations"] = v
    status["unconnected"] = u
    status["census"] = census

    # Plausible-census check: while the baseline says the board is
    # unfinished, a report attesting zero items in total is not
    # credible — the checker, not the board, is what changed.
    # Skipped when the baseline is 0/0 (finished board): a clean
    # report is exactly what health looks like there.
    if bv + bu > 0 and census <= 0:
        status["tool_health"] = "FAIL"
        status["case"] = "tool_failure"
        status["verdict"] = "TOOL FAILURE"
        status["board_state"] = (
            f"DRC TOOL FAILURE: report census is {census} items while the "
            f"baseline ({bv} violations, {bu} unconnected) says the board "
            "is unfinished — the DRC report is not trustworthy")
        return finish(2)
    status["tool_health"] = "ok"

    # Pinned exclusions: match the JSON run's items by UUID. The
    # text and JSON reports come from two kicad-cli runs of the
    # same board; counts must agree within the observed checker
    # jitter (±1), else neither is trustworthy. The verdict below
    # then runs on effective (post-exclusion) counts; the raw
    # counts stay in the status as "violations"/"unconnected" and
    # the excluded count is reported, never hidden.
    status["excluded_items"] = 0
    status["effective_violations"] = v
    if args.json_report:
        try:
            jv, ju, excluded, effective = apply_exclusions(
                args.json_report, args.pro, pinned)
        except Exception as e:
            status["tool_health"] = "FAIL"
            status["case"] = "tool_failure"
            status["verdict"] = "TOOL FAILURE"
            status["board_state"] = f"DRC TOOL FAILURE: {e}"
            return finish(2)
        if abs(jv - v) > 1 or abs(ju - u) > 1:
            status["tool_health"] = "FAIL"
            status["case"] = "tool_failure"
            status["verdict"] = "TOOL FAILURE"
            status["board_state"] = (
                f"DRC TOOL FAILURE: text report ({v} violations, "
                f"{u} unconnected) and JSON report ({jv}, {ju}) "
                "disagree beyond checker jitter — neither is "
                "trustworthy")
            return finish(2)
        status["excluded_items"] = excluded
        status["effective_violations"] = effective
        v, u = effective, ju

    # Three cases (round 3): at/below baseline; above baseline but
    # within the checker-jitter tolerance; above baseline +
    # tolerance. `regression` keeps its CI meaning — the hard
    # failure — and is true only in the third case.
    status["over_violations"] = v - bv
    status["over_unconnected"] = u - bu
    status["regression"] = v > bv + tv or u > bu + tu
    if status["regression"]:
        status["case"] = "regression"
        status["verdict"] = "REGRESSION"
        status["board_state"] = (
            f"DRC REGRESSION: {v} violations, {u} unconnected — "
            f"ABOVE baseline {bv}/{bu} + jitter tolerance +{tv}/+{tu} "
            "(routing regressed, or the checker changed behaviour)")
        return finish(1)

    if v > bv or u > bu:
        status["case"] = "within_jitter_tolerance"
        status["verdict"] = "WITHIN JITTER TOLERANCE"
        over = []
        if v > bv:
            over.append(f"+{v - bv} violations")
        if u > bu:
            over.append(f"+{u - bu} unconnected")
        status["board_state"] = (
            f"DRC (board in progress): {v} violations, {u} unconnected "
            f"— within checker jitter tolerance "
            f"({', '.join(over)} over baseline {bv}/{bu}, "
            f"tolerance +{tv}/+{tu})")
        return finish(0)

    status["case"] = "no_regression"
    status["verdict"] = "NO REGRESSION"
    if bv == 0 and bu == 0 and status["excluded_items"]:
        status["board_state"] = (
            f"DRC: 0 violations, {u} unconnected — baseline 0/0 "
            "(finished board; hard gate). "
            f"{status['excluded_items']} further report item(s) "
            "match the pinned J1 land-pattern exclusions in "
            "ci/drc-baseline.json (reported, not hidden)")
    elif bv == 0 and bu == 0:
        status["board_state"] = (
            f"DRC: {v} violations, {u} unconnected — baseline 0/0 "
            "(finished board; hard gate)")
    else:
        status["board_state"] = (
            f"DRC (board in progress): {v} violations, {u} unconnected "
            f"— baseline {bv}/{bu}, no regression")
    return finish(0)


if __name__ == "__main__":
    sys.exit(main())
