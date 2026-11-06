#!/usr/bin/env python3
"""Fixture tests for the CI signal gates (scripts/drc_gate.py,
scripts/erc_gate.py). Run: python3 ci/test_gates.py

Two generations of cases:

  * ROUND 1 (synthetic): the cases verified ad hoc in round 1
    against fixture reports in the bare console format
    ('Found N DRC violations' / 'Found N unconnected items'),
    with a temporary 807/175 baseline — the seed values, kept
    here so the ratchet semantics stay pinned even though the
    shipped baseline has since been calibrated.
  * ROUND 2 (real): the gates against the REAL KiCad 8 reports
    captured from run 41750532660 (ci/fixtures/), which broke
    both round-1 implementations on live CI — the DRC parser on
    the '**'-framed 'unconnected pads' wording, and the ERC
    step on --exit-code-violations firing on warnings.
  * ROUND 3 (jitter): run 41751841325 measured 727/190 on the
    IDENTICAL board blob run 41750532660 measured at 726/190 —
    ±1 checker jitter, which the round-2 ratchet flagged as a
    regression. The shipped baseline now carries tolerances
    (5 violations / 2 unconnected): the real fixture doctored
    to 727/190 must pass WITH the jitter wording, 731/192 (the
    tolerance edge) must pass, and 732/190 / 726/193 (beyond
    tolerance) must still fail. The round-2 doctored-727 case
    against a tolerance-less baseline stays: default tolerance
    is 0, so strict semantics are pinned too.

Exit 0 iff every case matches its expected exit code.
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRC_GATE = os.path.join(ROOT, "scripts", "drc_gate.py")
ERC_GATE = os.path.join(ROOT, "scripts", "erc_gate.py")
DRC_FIXTURE = os.path.join(ROOT, "ci", "fixtures",
                           "drc-report-run41750532660.txt")
ERC_FIXTURE = os.path.join(ROOT, "ci", "fixtures",
                           "erc-report-run41750532660.txt")
SHIPPED_BASELINE = os.path.join(ROOT, "ci", "drc-baseline.json")

failures = []


def check(name, got, want):
    ok = got == want
    print(f"{'PASS' if ok else 'FAIL'}  {name}: exit {got} (want {want})")
    if not ok:
        failures.append(name)


def check_bool(name, ok):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        failures.append(name)


def run_gate(script, args):
    return subprocess.run(
        [sys.executable, script] + args,
        capture_output=True, text=True, cwd=ROOT)


def write(path, text):
    with open(path, "w") as f:
        f.write(text)
    return path


def baseline_file(tmp, v, u):
    return write(os.path.join(tmp, f"baseline-{v}-{u}.json"),
                 json.dumps({"violations": v, "unconnected": u}))


def drc(tmp, report, baseline):
    r = run_gate(DRC_GATE, ["--report", report, "--baseline", baseline,
                            "--out", os.path.join(tmp, "drc-status.json")])
    return r


def erc(tmp, report):
    return run_gate(ERC_GATE, ["--report", report,
                               "--out", os.path.join(tmp, "erc-status.json")])


def synthetic_drc(tmp, name, v, u, framed=False):
    if framed:
        text = (f"** Found {v} DRC violations **\n"
                f"** Found {u} unconnected items **\n")
    else:
        text = f"Found {v} DRC violations\nFound {u} unconnected items\n"
    return write(os.path.join(tmp, name), text)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        with open(DRC_FIXTURE) as f:
            real_drc = f.read()
        with open(ERC_FIXTURE) as f:
            real_erc = f.read()

        # ---- DRC, real fixture (726 violations / 190 unconnected) ----
        base726 = baseline_file(tmp, 726, 190)
        check("drc real fixture @ baseline 726/190",
              drc(tmp, DRC_FIXTURE, base726).returncode, 0)
        check("drc real fixture @ shipped baseline",
              drc(tmp, DRC_FIXTURE, SHIPPED_BASELINE).returncode, 0)
        doc = write(os.path.join(tmp, "drc-727.txt"),
                    real_drc.replace("** Found 726 DRC violations **",
                                     "** Found 727 DRC violations **"))
        check("drc real fixture doctored 727/190 @ tolerance-less "
              "baseline (strict)",
              drc(tmp, doc, base726).returncode, 1)

        # ---- DRC, round 3: jitter tolerance (shipped baseline
        # 726/190 + tolerance 5/2) ----
        r = drc(tmp, doc, SHIPPED_BASELINE)
        check("drc round3 doctored 727/190 @ shipped baseline "
              "(jitter)", r.returncode, 0)
        check_bool("drc round3 jitter banner wording",
                   "within checker jitter tolerance" in r.stdout
                   and "+1 violations over baseline" in r.stdout
                   and "tolerance +5/+2" in r.stdout)
        with open(os.path.join(tmp, "drc-status.json")) as f:
            st = json.load(f)
        check_bool("drc round3 status json case + tolerances",
                   st.get("case") == "within_jitter_tolerance"
                   and st.get("verdict") == "WITHIN JITTER TOLERANCE"
                   and st.get("regression") is False
                   and st.get("tolerance_violations") == 5
                   and st.get("tolerance_unconnected") == 2)
        doc = write(os.path.join(tmp, "drc-731-192.txt"),
                    real_drc.replace(
                        "** Found 726 DRC violations **",
                        "** Found 731 DRC violations **").replace(
                        "** Found 190 unconnected pads **",
                        "** Found 192 unconnected pads **"))
        check("drc round3 doctored 731/192 @ shipped (tolerance "
              "edge)", drc(tmp, doc, SHIPPED_BASELINE).returncode, 0)
        doc = write(os.path.join(tmp, "drc-732.txt"),
                    real_drc.replace("** Found 726 DRC violations **",
                                     "** Found 732 DRC violations **"))
        check("drc round3 doctored 732/190 @ shipped (beyond "
              "tolerance)", drc(tmp, doc, SHIPPED_BASELINE).returncode, 1)
        doc = write(os.path.join(tmp, "drc-193.txt"),
                    real_drc.replace("** Found 190 unconnected pads **",
                                     "** Found 193 unconnected pads **"))
        check("drc round3 doctored 726/193 @ shipped (beyond "
              "tolerance)", drc(tmp, doc, SHIPPED_BASELINE).returncode, 1)
        doc = write(os.path.join(tmp, "drc-191.txt"),
                    real_drc.replace("** Found 190 unconnected pads **",
                                     "** Found 191 unconnected pads **"))
        check("drc real fixture doctored 726/191",
              drc(tmp, doc, base726).returncode, 1)
        corrupt = write(os.path.join(tmp, "drc-corrupt.txt"),
                        "this is not a DRC report\n")
        check("drc corrupt report",
              drc(tmp, corrupt, base726).returncode, 2)
        empty = write(os.path.join(tmp, "drc-empty.txt"), "")
        check("drc empty report", drc(tmp, empty, base726).returncode, 2)
        check("drc missing report",
              drc(tmp, os.path.join(tmp, "no-such.txt"),
                  base726).returncode, 2)

        # ---- DRC, round-1 synthetic suite (console format) ----
        base807 = baseline_file(tmp, 807, 175)
        check("drc r1 at baseline 807/175",
              drc(tmp, synthetic_drc(tmp, "r1-at.txt", 807, 175),
                  base807).returncode, 0)
        check("drc r1 below baseline 700/100",
              drc(tmp, synthetic_drc(tmp, "r1-below.txt", 700, 100),
                  base807).returncode, 0)
        check("drc r1 over baseline 808/175",
              drc(tmp, synthetic_drc(tmp, "r1-over-v.txt", 808, 175),
                  base807).returncode, 1)
        check("drc r1 over baseline 807/176",
              drc(tmp, synthetic_drc(tmp, "r1-over-u.txt", 807, 176),
                  base807).returncode, 1)
        check("drc r1 0/0 vs unfinished baseline (census)",
              drc(tmp, synthetic_drc(tmp, "r1-zero.txt", 0, 0),
                  base807).returncode, 2)
        base0 = baseline_file(tmp, 0, 0)
        check("drc r1 0/0 vs 0/0 baseline (finished board)",
              drc(tmp, synthetic_drc(tmp, "r1-zero2.txt", 0, 0),
                  base0).returncode, 0)
        check("drc framed 'unconnected items' variant parses",
              drc(tmp, synthetic_drc(tmp, "r2-framed.txt", 5, 3,
                                     framed=True),
                  base807).returncode, 0)

        # ---- ERC, real fixture (0 errors / 8 warnings) ----
        r = erc(tmp, ERC_FIXTURE)
        check("erc real fixture", r.returncode, 0)
        want_line = ("ERC: 0 errors, 8 warnings (known "
                     "lib_symbol_issues, justified in "
                     "docs/00-status.md)")
        ok = want_line in r.stdout
        print(f"{'PASS' if ok else 'FAIL'}  erc real fixture success line")
        if not ok:
            failures.append("erc success line")
        doc = write(os.path.join(tmp, "erc-1err.txt"),
                    real_erc.replace(
                        "** ERC messages: 8  Errors 0  Warnings 8",
                        "** ERC messages: 8  Errors 1  Warnings 7"))
        check("erc doctored Errors 1", erc(tmp, doc).returncode, 1)
        bad = write(os.path.join(tmp, "erc-inconsistent.txt"),
                    real_erc.replace(
                        "** ERC messages: 8  Errors 0  Warnings 8",
                        "** ERC messages: 9  Errors 0  Warnings 8"))
        check("erc inconsistent total", erc(tmp, bad).returncode, 2)
        corrupt = write(os.path.join(tmp, "erc-corrupt.txt"),
                        "this is not an ERC report\n")
        check("erc corrupt report", erc(tmp, corrupt).returncode, 2)
        empty = write(os.path.join(tmp, "erc-empty.txt"), "")
        check("erc empty report", erc(tmp, empty).returncode, 2)
        check("erc missing report",
              erc(tmp, os.path.join(tmp, "no-such.txt")).returncode, 2)

    print()
    if failures:
        print(f"test_gates: {len(failures)} FAILURE(S): {failures}")
        return 1
    print("test_gates: ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
