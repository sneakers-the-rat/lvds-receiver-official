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
    ci/drc-baseline.json (routing got worse, or the checker changed
    behaviour; either must be seen).

It exits 0 when the tool is healthy and counts are at or below the
baseline. That outcome is reported as BOARD STATE ("DRC (board in
progress): ... — no regression"), never as "DRC passed".

End state: when routing completes, the baseline is set to 0/0 and the
same ratchet is a hard zero-tolerance gate by construction — the
census check is skipped when the baseline total is 0, so a genuinely
clean report passes.

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

RE_VIOLATIONS = re.compile(r"Found (\d+) DRC violations")
RE_UNCONNECTED = re.compile(r"Found (\d+) unconnected items")


def load_baseline(path):
    """Return (violations, unconnected) or raise ValueError."""
    with open(path) as f:
        data = json.load(f)
    v = data["violations"]
    u = data["unconnected"]
    if not isinstance(v, int) or not isinstance(u, int) or v < 0 or u < 0:
        raise ValueError(f"baseline counts must be non-negative ints, got {v!r}/{u!r}")
    return v, u


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
            missing.append("'Found N unconnected items'")
        raise ValueError(
            "DRC report unparseable: missing summary line(s) "
            + ", ".join(missing) + f" in {path}")
    v, u = int(mv.group(1)), int(mu.group(1))
    return v, u, v + u


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", default="results/drc-report.txt")
    ap.add_argument("--baseline", default="ci/drc-baseline.json")
    ap.add_argument("--out", default="results/drc-status.json")
    args = ap.parse_args(argv)

    status = {
        "report": args.report,
        "baseline_file": args.baseline,
        "tool_health": "unknown",
        "regression": None,
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
        bv, bu = load_baseline(args.baseline)
    except Exception as e:
        status["tool_health"] = "FAIL"
        status["verdict"] = "TOOL FAILURE"
        status["board_state"] = f"DRC TOOL FAILURE: baseline unreadable ({e})"
        return finish(2)
    status["baseline_violations"] = bv
    status["baseline_unconnected"] = bu

    try:
        v, u, census = parse_report(args.report)
    except Exception as e:
        status["tool_health"] = "FAIL"
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
        status["verdict"] = "TOOL FAILURE"
        status["board_state"] = (
            f"DRC TOOL FAILURE: report census is {census} items while the "
            f"baseline ({bv} violations, {bu} unconnected) says the board "
            "is unfinished — the DRC report is not trustworthy")
        return finish(2)
    status["tool_health"] = "ok"

    status["regression"] = v > bv or u > bu
    if status["regression"]:
        status["verdict"] = "REGRESSION"
        status["board_state"] = (
            f"DRC REGRESSION: {v} violations, {u} unconnected — "
            f"ABOVE baseline {bv}/{bu} (routing regressed, or the "
            "checker changed behaviour)")
        return finish(1)

    status["verdict"] = "NO REGRESSION"
    if bv == 0 and bu == 0:
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
