#!/usr/bin/env bash
# PDLVDS-RX local CI — the single entry point used by GitHub Actions.
# Runs every validation that can run without hardware. Each step prints
# a header and its own PASS/FAIL; the script exits non-zero if any
# selected step fails.
#
# Step selection: CI_STEPS is a comma-separated list of step numbers
# (default: all). GitHub Actions uses this to split the pipeline into
# jobs, because the KiCad 8 PPA's libngspice-kicad and Ubuntu's
# standalone ngspice package ship the same codemodel files
# (/usr/lib/x86_64-linux-gnu/ngspice/*.cm) without a Conflicts/Replaces
# — installing both in one apt transaction fails in dpkg (observed in
# GH Actions run 41710107325). So the KiCad job installs no standalone
# ngspice, and the simulation job installs no KiCad; each runs its
# subset of these steps. A local run with no CI_STEPS still does
# everything, in order.
#
# KiCad ERC/DRC: if the installed kicad-cli supports `sch erc` /
# `pcb drc` (KiCad >= 8) those run natively; otherwise the scripted
# equivalents (netlist diff, pcb connectivity + clearance audit) run
# instead and say so loudly.
#
# ERC and DRC are separate steps (10 and 11) because they are
# different signals: ERC is a HARD GATE (any error fails, always).
# Since round 2 the ERC verdict is parsed from the report by
# scripts/erc_gate.py, NOT taken from kicad-cli's exit code:
# KiCad 8's --exit-code-violations exits non-zero on warnings too
# (run 41750532660 failed its ERC step with a 0-error report).
# DRC of the still-unfinished board cannot be a hard gate on the raw
# count — that made CI permanently red and hid real breakage — so
# step 11 runs DRC for its report and then applies the tool-health +
# baseline-ratchet gate in scripts/drc_gate.py against
# ci/drc-baseline.json. See docs/00-status.md ("CI signal fix").
set -u
cd "$(dirname "$0")/.."
FAIL=0
step() { echo; echo "=== $1 ==="; }
fail() { echo "STEP FAILED: $1"; FAIL=1; }

step1() {
  step "1/11 python codec unit tests"
  python3 -m pytest host/test_codec.py -q || python3 host/test_codec.py || fail "codec tests"
}

step2() {
  step "2/11 link budget check (R2 must PASS)"
  python3 sim/link_budget.py > results/link_budget.txt 2>&1
  grep -q "R2 VERDICT: PASS" results/link_budget.txt && echo "link budget PASS" || fail "link budget"
}

step3() {
  step "3/11 ngspice TIA simulation check"
  python3 sim/run_tia.py > /tmp/tia_ci.txt 2>&1; tail -5 /tmp/tia_ci.txt
  grep -q "TIA NGSPICE VERDICT: PASS" /tmp/tia_ci.txt || fail "TIA sim"
}

step4() {
  step "4/11 digital simulation (8b/10b / Manchester / PRBS-15)"
  python3 sim/digital_sim.py > /tmp/dig_ci.txt 2>&1; tail -3 /tmp/dig_ci.txt
  grep -q "PASS: digital_sim -- all checks passed" /tmp/dig_ci.txt || fail "digital sim"
}

step5() {
  step "5/11 HV analytical design check"
  python3 sim/hv_design.py > /tmp/hv_ci.txt 2>&1; tail -3 /tmp/hv_ci.txt
  grep -q "FAIL" /tmp/hv_ci.txt && fail "HV design"
  return 0
}

step6() {
  step "6/11 impedance calculation"
  python3 sim/impedance.py > /tmp/z_ci.txt 2>&1; tail -3 /tmp/z_ci.txt
}

step7() {
  step "7/11 firmware host unit tests"
  ( cd firmware && make host-test 2>&1 | tail -3 ) || fail "firmware host tests"
}

step8() {
  step "8/11 firmware ARM cross-compile"
  if [ "${FW_CACHE_HIT:-}" = "true" ]; then
    # Firmware-binary cache hit (CI workflow): these exact sources
    # already cross-compiled cleanly once — the cache key covers
    # every compile input — and the toolchain was deliberately not
    # installed. Verify the restored artifacts instead of
    # rebuilding: both present, non-empty, ELF magic intact.
    if [ -s firmware/build/rxfw.elf ] && [ -s firmware/build/rxfw.bin ] \
       && head -c 4 firmware/build/rxfw.elf | od -An -tx1 | grep -q '7f 45 4c 46'; then
      echo "rxfw.elf + rxfw.bin restored from firmware-binary cache (sources unchanged; rebuild skipped)"
      return 0
    fi
    fail "arm build (cache hit claimed but restored binary missing/invalid)"
    return 0
  fi
  ( cd firmware && make clean >/dev/null 2>&1; make arm 2>&1 | tail -3 ) || fail "arm build"
}

step9() {
  step "9/11 host tool simulation smoke test"
  python3 host/rxhost.py --simulate selftest && \
  python3 host/rxhost.py --simulate ber-test --buffers 20 --ber 1e-5 > /dev/null && \
  echo "rxhost simulate PASS" || fail "rxhost"
}

# NOTE: `kicad-cli <sub> --help` exit codes are unreliable (a valid
# subcommand can exit non-zero on --help), so steps 10/11 detect
# native ERC/DRC by grepping the subcommand lists instead.
native_kicad() {
  kicad-cli sch --help 2>&1 | grep -qw erc && kicad-cli pcb --help 2>&1 | grep -qw drc
}

step10() {
  step "10/11 KiCad ERC (HARD GATE: 0 errors, gated on the parsed report)"
  if native_kicad; then
    echo "kicad-cli with native ERC/DRC found — running native ERC"
    # The verdict comes from the parsed report (scripts/erc_gate.py),
    # never from the kicad-cli exit code: KiCad 8's
    # --exit-code-violations exits non-zero on WARNINGS too, which
    # failed run 41750532660's ERC step over a 0-error / 8-warning
    # report. So ERC is invoked WITHOUT that flag, its exit code is
    # logged for information only, and the gate decides: FAIL iff
    # the report's Errors count is > 0; a missing, empty,
    # unparseable or internally inconsistent report is a tool-health
    # failure. The stale report is removed first so the gate can
    # never pass on a previous run's file.
    rm -f results/erc-report.txt
    kicad-cli sch erc --severity-all \
        -o results/erc-report.txt hw/pdlvds_rx.kicad_sch
    echo "kicad-cli sch erc exit code: $? (informational only — the gate below decides)"
    python3 scripts/erc_gate.py \
        --report results/erc-report.txt \
        --out results/erc-status.json || {
          fail "ERC gate (errors present, or report missing/unparseable)"
          echo "--- ERC report (results/erc-report.txt, FULL; also in the evidence artifact) ---"
          cat results/erc-report.txt 2>/dev/null || echo "(no ERC report file produced)"
        }
  else
    echo "NOTE: this kicad-cli has no erc/drc subcommands (KiCad 7.x)."
    echo "Running scripted ERC equivalent: netlist diff."
    kicad-cli sch export netlist --format kicadxml -o results/netlist.xml \
        hw/pdlvds_rx.kicad_sch || fail "netlist export"
    python3 hw/check_netlist.py results/netlist.xml || fail "netlist check"
  fi
}

step11() {
  step "11/11 KiCad DRC (tool health + baseline ratchet — board state, not a raw-count gate)"
  if native_kicad; then
    # Tool health, part 1: the checker binary must run and the board
    # file must exist. Either failing is a hard failure here, never
    # a silent skip.
    if ! command -v kicad-cli > /dev/null 2>&1; then
      fail "DRC tool health: kicad-cli not found"
      return
    fi
    if [ ! -f hw/pdlvds_rx.kicad_pcb ]; then
      fail "DRC tool health: board file hw/pdlvds_rx.kicad_pcb missing"
      return
    fi
    # Run DRC WITHOUT --exit-code-violations: the counts of an
    # unfinished board are board state, judged by the ratchet below —
    # not by kicad-cli's exit code. A non-zero exit here means the
    # tool itself failed to run, which is a hard failure.
    rm -f results/drc-report.txt
    if ! kicad-cli pcb drc --severity-all \
        -o results/drc-report.txt hw/pdlvds_rx.kicad_pcb; then
      fail "DRC tool health: kicad-cli pcb drc failed to run"
      echo "--- DRC report (results/drc-report.txt, if any; also in the evidence artifact) ---"
      cat results/drc-report.txt 2>/dev/null || echo "(no DRC report file produced)"
      return
    fi
    # Tool health, part 2 + ratchet: the report must exist, parse,
    # and carry a plausible census, and the counts must not exceed
    # ci/drc-baseline.json. scripts/drc_gate.py prints the counts
    # prominently, writes results/drc-status.json for the site
    # status panel, and appends to $GITHUB_STEP_SUMMARY when set.
    python3 scripts/drc_gate.py \
        --report results/drc-report.txt \
        --baseline ci/drc-baseline.json \
        --out results/drc-status.json || fail "DRC gate (tool health / baseline ratchet)"
  else
    echo "NOTE: this kicad-cli has no erc/drc subcommands (KiCad 7.x)."
    echo "Running scripted DRC equivalent: PCB connectivity + clearance audit (hard gate, as before)."
    xvfb-run -a python3 hw/check_pcb.py hw/pdlvds_rx.kicad_pcb || fail "pcb audit"
  fi
}

CI_STEPS=${CI_STEPS:-1,2,3,4,5,6,7,8,9,10,11}
echo "CI steps selected: $CI_STEPS"
for n in ${CI_STEPS//,/ }; do
  fn="step$n"
  if declare -F "$fn" > /dev/null; then
    "$fn"
  else
    echo "unknown CI step: $n"
    FAIL=1
  fi
done

echo
if [ "$FAIL" = 0 ]; then echo "CI: ALL STEPS PASS"; else echo "CI: FAILURES PRESENT"; fi
exit $FAIL
