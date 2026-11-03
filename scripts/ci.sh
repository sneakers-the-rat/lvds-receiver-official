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
set -u
cd "$(dirname "$0")/.."
FAIL=0
step() { echo; echo "=== $1 ==="; }
fail() { echo "STEP FAILED: $1"; FAIL=1; }

step1() {
  step "1/10 python codec unit tests"
  python3 -m pytest host/test_codec.py -q || python3 host/test_codec.py || fail "codec tests"
}

step2() {
  step "2/10 link budget check (R2 must PASS)"
  python3 sim/link_budget.py > results/link_budget.txt 2>&1
  grep -q "R2 VERDICT: PASS" results/link_budget.txt && echo "link budget PASS" || fail "link budget"
}

step3() {
  step "3/10 ngspice TIA simulation check"
  python3 sim/run_tia.py > /tmp/tia_ci.txt 2>&1; tail -5 /tmp/tia_ci.txt
  grep -q "TIA NGSPICE VERDICT: PASS" /tmp/tia_ci.txt || fail "TIA sim"
}

step4() {
  step "4/10 digital simulation (8b/10b / Manchester / PRBS-15)"
  python3 sim/digital_sim.py > /tmp/dig_ci.txt 2>&1; tail -3 /tmp/dig_ci.txt
  grep -q "PASS: digital_sim -- all checks passed" /tmp/dig_ci.txt || fail "digital sim"
}

step5() {
  step "5/10 HV analytical design check"
  python3 sim/hv_design.py > /tmp/hv_ci.txt 2>&1; tail -3 /tmp/hv_ci.txt
  grep -q "FAIL" /tmp/hv_ci.txt && fail "HV design"
  return 0
}

step6() {
  step "6/10 impedance calculation"
  python3 sim/impedance.py > /tmp/z_ci.txt 2>&1; tail -3 /tmp/z_ci.txt
}

step7() {
  step "7/10 firmware host unit tests"
  ( cd firmware && make host-test 2>&1 | tail -3 ) || fail "firmware host tests"
}

step8() {
  step "8/10 firmware ARM cross-compile"
  ( cd firmware && make clean >/dev/null 2>&1; make arm 2>&1 | tail -3 ) || fail "arm build"
}

step9() {
  step "9/10 host tool simulation smoke test"
  python3 host/rxhost.py --simulate selftest && \
  python3 host/rxhost.py --simulate ber-test --buffers 20 --ber 1e-5 > /dev/null && \
  echo "rxhost simulate PASS" || fail "rxhost"
}

step10() {
  step "10/10 KiCad ERC + netlist/DRC checks"
  # NOTE: `kicad-cli <sub> --help` exit codes are unreliable (a valid
  # subcommand can exit non-zero on --help), so detect native ERC/DRC
  # by grepping the subcommand lists instead.
  if kicad-cli sch --help 2>&1 | grep -qw erc && kicad-cli pcb --help 2>&1 | grep -qw drc; then
    echo "kicad-cli with native ERC/DRC found — running native checks"
    kicad-cli sch erc --severity-all --exit-code-violations \
        -o results/erc-report.txt hw/pdlvds_rx.kicad_sch || fail "native ERC"
    kicad-cli pcb drc --severity-all --exit-code-violations \
        -o results/drc-report.txt hw/pdlvds_rx.kicad_pcb || fail "native DRC"
  else
    echo "NOTE: this kicad-cli has no erc/drc subcommands (KiCad 7.x)."
    echo "Running scripted equivalents: netlist diff + PCB audit."
    kicad-cli sch export netlist --format kicadxml -o results/netlist.xml \
        hw/pdlvds_rx.kicad_sch || fail "netlist export"
    python3 hw/check_netlist.py results/netlist.xml || fail "netlist check"
    xvfb-run -a python3 hw/check_pcb.py hw/pdlvds_rx.kicad_pcb || fail "pcb audit"
  fi
}

CI_STEPS=${CI_STEPS:-1,2,3,4,5,6,7,8,9,10}
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
