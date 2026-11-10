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
        if k not in exp:
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
        if len(pins) < 2 and net not in SINGLE_OK:
            errors.append(f"net {net}: only {len(pins)} pin(s) {pins}")
        ts = [types.get(p, "passive") for p in pins]
        if net in circuit.POWER_NETS and not any(
                t in ("power_out", "output", "open_collector") for t in ts):
            errors.append(f"power net {net}: no driver pin and rely on PWR_FLAG only")
        n_out = sum(1 for t in ts if t == "output")
        if n_out > 1 and net not in ("CDR_DATP","CDR_DATN","CDR_CLKP","CDR_CLKN"):
            errors.append(f"net {net}: {n_out} outputs shorted")
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
