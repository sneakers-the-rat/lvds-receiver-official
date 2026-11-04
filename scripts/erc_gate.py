#!/usr/bin/env python3
"""ERC hard gate on the PARSED REPORT (scripts/ci.sh step 10).

Why this exists (round 2 of the CI signal fix): ERC has always been
a hard gate — any error fails, always. Round 1 implemented it by
trusting `kicad-cli sch erc --exit-code-violations`'s exit code.
The first live run (41750532660) showed what that flag actually
does in KiCad 8: it exits non-zero on WARNINGS too. The step
failed while its own report said 0 errors / 8 warnings — a clean
ERC wearing a red step, the same invisibility disease as the old
DRC step, one job over.

So the verdict now comes from the report itself, never from the
kicad-cli exit code (ci.sh invokes ERC without
--exit-code-violations and ignores the exit code entirely):

  * FAIL (exit 1) iff the report's summary line
    '** ERC messages: N  Errors E  Warnings W' has E > 0.
  * TOOL-HEALTH FAIL (exit 2) if the report is missing, empty,
    unparseable, or internally inconsistent (N != E + W): a
    silently broken ERC is exactly the failure mode this gate
    exists to catch; it is never waved through.
  * PASS (exit 0) when E == 0, printing the counts — currently
    'ERC: 0 errors, 8 warnings (known lib_symbol_issues,
    justified in docs/00-status.md)'.

Every run writes a JSON status file (default
results/erc-status.json), prints the verdict prominently to the
job log, and appends a markdown block to $GITHUB_STEP_SUMMARY
when that variable is set.
"""
import argparse
import json
import os
import re
import sys

RE_ERC_SUMMARY = re.compile(
    r"\*\* ERC messages: (\d+)\s+Errors\s+(\d+)\s+Warnings\s+(\d+)")


def parse_report(path):
    """Return (total, errors, warnings) or raise ValueError."""
    if not os.path.exists(path):
        raise ValueError(f"ERC report not produced: {path} does not exist")
    with open(path, errors="replace") as f:
        text = f.read()
    if not text.strip():
        raise ValueError(f"ERC report is empty: {path}")
    m = RE_ERC_SUMMARY.search(text)
    if m is None:
        raise ValueError(
            "ERC report unparseable: missing summary line "
            f"'** ERC messages: N  Errors E  Warnings W' in {path}")
    total, errors, warnings = (int(g) for g in m.groups())
    if total != errors + warnings:
        raise ValueError(
            f"ERC report internally inconsistent: summary attests "
            f"{total} messages but {errors} errors + {warnings} "
            "warnings — the report is not trustworthy")
    return total, errors, warnings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", default="results/erc-report.txt")
    ap.add_argument("--out", default="results/erc-status.json")
    args = ap.parse_args(argv)

    status = {
        "report": args.report,
        "tool_health": "unknown",
        "verdict": "unknown",
        "board_state": "",
    }

    def finish(code):
        line = status["board_state"] or f"ERC: {status['verdict']}"
        print()
        print("=" * 72)
        print(line)
        print(f"ERC tool health: {status['tool_health']}; "
              f"verdict: {status['verdict']}")
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
                f.write(f"### KiCad ERC — hard gate\n\n{line}\n\n"
                        f"Tool health: {status['tool_health']} · "
                        f"verdict: {status['verdict']}\n")
        return code

    try:
        total, errors, warnings = parse_report(args.report)
    except Exception as e:
        status["tool_health"] = "FAIL"
        status["verdict"] = "TOOL FAILURE"
        status["board_state"] = f"ERC TOOL FAILURE: {e}"
        return finish(2)
    status["tool_health"] = "ok"
    status["messages"] = total
    status["errors"] = errors
    status["warnings"] = warnings

    if errors > 0:
        status["verdict"] = "FAIL"
        status["board_state"] = (
            f"ERC: {errors} errors, {warnings} warnings — HARD GATE FAIL")
        return finish(1)

    status["verdict"] = "PASS"
    if warnings > 0:
        status["board_state"] = (
            f"ERC: 0 errors, {warnings} warnings "
            "(known lib_symbol_issues, justified in docs/00-status.md)")
    else:
        status["board_state"] = "ERC: 0 errors, 0 warnings"
    return finish(0)


if __name__ == "__main__":
    sys.exit(main())
