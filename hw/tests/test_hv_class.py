#!/usr/bin/env python3
"""Regression test: clearance classes follow carried voltage, in
both directions (regression for the step-1 class-vs-voltage census,
results/class-voltage-census.txt).

Failure history (found 2026-11-04, passes 78-79):
  * The pass-78 U10 diagnosis priced escapes for the LT3757 control
    nets (HV_GATE, HV_INTVCC, HV_SHDN) at a "0.25 HV clearance
    class" that no tool ever applied — check_pcb.py and router.py
    both class those nets at the 0.20 default, correctly: they
    carry 0.12-7.2 V (CONNECTIONS.md). The mispriced arithmetic
    declared U10.9 unroutable in place; a dense retest at the true
    class found its escape (pass 80).
  * In the opposite direction, nets that DO carry high voltage sat
    at the 0.20 default: TP_HV (test point floating to ~APD_K
    potential, <=259.4 V, through R34 10 MOhm) was live on the
    board, and the parts-fix string/OVP midpoint nets arriving
    with the re-sync (HV_R29M ~259 V, HV_R30M ~130 V,
    HV_R31A ~160 V, HV_R31B ~80 V, HV_OVP1/HV_OVP2 zener-stack
    midpoints) would have landed at 0.20 too.

Checks:
  1. every HV-domain net classes at 1.00 mm in check_pcb AND in
     router.netclass;
  2. every LV net with an HV_ name classes at the 0.20 default in
     both (a future prefix-based rule fails here);
  3. the two modules' HV_NETS sets are identical (drift guard).

Run: xvfb-run -a python3 hw/tests/test_hv_class.py [HW_DIR]
(HW_DIR defaults to the repo's hw/; point it at a tree with the
pre-correction check_pcb.py/router.py to watch check 1 fail.)
Exit 0 iff every check passes.
"""
import os
import sys

HW = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else \
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HW)
import wx
_app = wx.App(False)
import check_pcb
import router

HV_DOMAIN = {"APD_K", "HV_RAW", "HV_SEC", "TP_HV", "HV_R29M",
             "HV_R30M", "HV_R31A", "HV_R31B", "HV_OVP1", "HV_OVP2"}
LV_HV_NAMED = {"HV_VC", "HV_VC2", "HV_FBX", "HV_SS", "HV_RT",
               "HV_SENSE", "HV_GATE", "HV_INTVCC", "HV_SHDN",
               "HV_EN", "HV_DAC"}

fails = []
for net in sorted(HV_DOMAIN):
    c1 = check_pcb.clearance_for(net)
    c2 = router.netclass(net)[1]
    if c1 != 1.0:
        fails.append(f"check_pcb.clearance_for({net}) = {c1}, want 1.0")
    if c2 != 1.0:
        fails.append(f"router.netclass({net}) clearance = {c2}, want 1.0")
for net in sorted(LV_HV_NAMED):
    c1 = check_pcb.clearance_for(net)
    c2 = router.netclass(net)[1]
    if c1 != 0.2:
        fails.append(f"check_pcb.clearance_for({net}) = {c1}, want 0.2 (LV)")
    if c2 != 0.2:
        fails.append(f"router.netclass({net}) clearance = {c2}, want 0.2 (LV)")
if check_pcb.HV_NETS != router.HV_NETS:
    fails.append(f"HV_NETS drift: check_pcb {sorted(check_pcb.HV_NETS)} "
                 f"vs router {sorted(router.HV_NETS)}")
if set(check_pcb.HV_NETS) != HV_DOMAIN:
    fails.append(f"check_pcb.HV_NETS = {sorted(check_pcb.HV_NETS)}, "
                 f"want exactly {sorted(HV_DOMAIN)}")

if fails:
    print("FAIL test_hv_class:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print(f"PASS test_hv_class: {len(HV_DOMAIN)} HV-domain nets at 1.00, "
      f"{len(LV_HV_NAMED)} LV HV_-named nets at 0.20, sets in sync")
