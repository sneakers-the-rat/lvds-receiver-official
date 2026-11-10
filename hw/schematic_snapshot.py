#!/usr/bin/env python3
"""Canonical snapshot of a KiCad XML netlist export, for proving that a
schematic change is purely cosmetic.

Emits a sorted, deterministic text form:
  COMP <ref> | <value> | <footprint>
  NET <name> :: <ref>.<pin>, <ref>.<pin>, ...
Unnamed nets (KiCad's "unconnected-(...)" generated names) canonicalise
to the name NC, keeping their exact pin membership: an accidental short
between two no-connect pins would merge two NC lines into one and show
up as a diff. Header lines give the canonical counts.

Usage:
  kicad-cli sch export netlist --format kicadxml -o out.xml hw/pdlvds_rx.kicad_sch
  python3 hw/schematic_snapshot.py out.xml > snapshot.txt
  python3 hw/schematic_snapshot.py --compare snapshot-a.txt snapshot-b.txt
--compare exits 0 iff the two snapshots are byte-identical.
"""
import sys
import xml.etree.ElementTree as ET


def snapshot(path):
    root = ET.parse(path).getroot()
    lines = []
    comps = []
    for comp in root.find("components").iter("comp"):
        comps.append((comp.get("ref"), comp.findtext("value") or "",
                      comp.findtext("footprint") or ""))
    for ref, value, fp in sorted(comps):
        lines.append(f"COMP {ref} | {value} | {fp}")
    nets = []
    npins_named = 0
    for net in root.find("nets").iter("net"):
        name = net.get("name")
        members = sorted(f"{n.get('ref')}.{n.get('pin')}"
                         for n in net.iter("node"))
        if name.startswith("unconnected-"):
            nets.append(("NC", members))
        else:
            nets.append((name, members))
            npins_named += len(members)
    for name, members in sorted(nets):
        lines.append(f"NET {name} :: {', '.join(members)}")
    ncomp = len(comps)
    header = [
        f"# components: {ncomp}",
        f"# nets (incl. NC singletons): {len(nets)}",
        f"# pins on named nets: {npins_named}",
    ]
    return "\n".join(header + lines) + "\n"


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--compare":
        a = open(sys.argv[2]).read()
        b = open(sys.argv[3]).read()
        if a == b:
            print("IDENTICAL: snapshots match byte for byte")
            return 0
        import difflib
        diff = list(difflib.unified_diff(
            a.splitlines(), b.splitlines(),
            fromfile=sys.argv[2], tofile=sys.argv[3], lineterm=""))
        print(f"DIFFER ({len(diff)} diff lines):")
        for line in diff[:80]:
            print(" ", line)
        return 1
    sys.stdout.write(snapshot(sys.argv[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
