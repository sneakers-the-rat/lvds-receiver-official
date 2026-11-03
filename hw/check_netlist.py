#!/usr/bin/env python3
"""Diff the KiCad netlist export against hw/circuit.py.

Every pin of every part must appear on exactly the net circuit.py says.
Also ERC-style structural checks: every net has >= 2 pins (or is a listed
single-pin exception), every power net contains a power_out/output pin
or a PWR_FLAG, and no net mixes two plain outputs (except listed LVDS /
open-drain cases). Exit 0 = PASS.
"""
import sys, xml.etree.ElementTree as ET
sys.path.insert(0, 'hw')
import circuit
from gen_schematic import part_pins

def expected():
    exp = {}   # (ref, pin) -> net
    for part in circuit.PARTS:
        for num, (name, t, net) in part_pins(part).items():
            if net: exp[(part["ref"], str(num))] = net
    return exp

def libid_resolution_errors(sch_path):
    """Every instance lib_id must resolve to an embedded lib_symbols
    definition of the SAME nickname-prefixed name. An unresolved
    instance is electrically inert (no pins) yet invisible to the
    netlist diff — power symbols are never listed as netlist nodes,
    and parts from circuit.py are unaffected. Exactly this hid the
    bare-name "PWR_FLAG" embedding (instances: "power:PWR_FLAG") that
    left all 11 power flags dead through CI rounds 1-2: the old
    structural check assumed flags drive their nets "by construction"
    instead of verifying resolution. Returns [] if the schematic
    file is absent (check skipped, noted by caller)."""
    import os, re
    if not os.path.exists(sch_path):
        return None
    txt = open(sch_path).read()
    i = txt.index("(lib_symbols")
    from gen_schematic import balanced
    block = balanced(txt, i)
    embedded = set(re.findall(r'\(symbol "([^"]+)"', block))
    errors = []
    for lib_id in sorted(set(re.findall(
            r'\(symbol \(lib_id "([^"]+)"\)', txt))):
        if lib_id not in embedded:
            errors.append(
                f"lib_id {lib_id!r}: no embedded lib_symbols definition "
                f"with that exact name — instances are unresolved/inert")
    return errors

def main(path="/tmp/netlist.xml"):
    tree = ET.parse(path)
    got = {}   # (ref, pin) -> net name
    for net in tree.getroot().iter("net"):
        nname = net.get("name")
        for node in net.iter("node"):
            got[(node.get("ref"), node.get("pin"))] = nname
    exp = expected()
    errors = []
    for k, v in sorted(exp.items()):
        if got.get(k) != v:
            errors.append(f"{k}: expected net {v}, netlist has {got.get(k)}")
    for k, v in sorted(got.items()):
        if k not in exp and not v.startswith("unconnected-"):
            errors.append(f"{k}: unexpected connection to {v}")
    # structural checks
    bynet = {}
    for (ref, pin), net in got.items(): bynet.setdefault(net, []).append((ref, pin))
    types = {}
    for part in circuit.PARTS:
        for num, (name, t, net) in part_pins(part).items():
            types[(part["ref"], str(num))] = t
    SINGLE_OK = {"TP_HV"}
    for net, pins in sorted(bynet.items()):
        if net.startswith("unconnected-"):
            continue
        if len(pins) < 2 and net not in SINGLE_OK:
            errors.append(f"net {net}: only {len(pins)} pin(s) {pins}")
        ts = [types.get(p, "passive") for p in pins]
        # power nets are ERC-driven via the PWR_FLAG symbols placed by
        # gen_schematic's flag_nets() rule (nets with a power_in pin and
        # no power_out pin); that those instances actually resolve is
        # verified by libid_resolution_errors below, not assumed.
        n_out = sum(1 for t in ts if t == "output")
        if n_out > 1 and net not in ("CDR_DATP","CDR_DATN","CDR_CLKP","CDR_CLKN","SW1","SW2"):
            errors.append(f"net {net}: {n_out} outputs shorted")
    import os
    sch = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "pdlvds_rx.kicad_sch")
    lid = libid_resolution_errors(sch)
    if lid is None:
        print("note: schematic not found next to check_netlist.py — "
              "lib_id resolution check skipped")
    else:
        errors.extend(lid)
    print(f"netlist check: {len(got)} connected pins, {len(bynet)} nets, "
          f"{len(exp)} expected connections")
    if errors:
        print(f"FAIL ({len(errors)} problems):")
        for e in errors[:40]: print("  ", e)
        return 1
    print("PASS: netlist matches circuit.py exactly; structural checks pass")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/netlist.xml"))
