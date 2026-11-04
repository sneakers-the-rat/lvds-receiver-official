#!/usr/bin/env python3
"""Prepare a Freerouting-ready DSN from KiCad's Specctra export.

KiCad 7 exports every net in one class (kicad_default, 0.2 mm /
0.2 mm) and exports the GND zones as plane polygons on all three
layers they occupy. For this board that is wrong in three ways,
fixed here by text surgery on the DSN (all values in um, the DSN's
own unit):

  1. Split the nets into the project's real classes (names and
     membership from hw/router.py): HV 0.40/1.00, POWER 0.60/0.25,
     LVDS 0.30/0.20, default 0.25/0.20 — widths/clearances in the
     class rules, so Freerouting is judged against the same audit
     rules as the home-grown router.
  2. Delete the F.Cu / B.Cu GND plane polygons: those pours are
     carve-around fills, not solid planes; as DSN planes they
     would forbid all other routing on the surface layers. The
     pours are refilled on the imported board (they carve around
     whatever copper exists, as in the home-grown flow). The
     In1.Cu plane stays: In1 IS a solid GND plane by design.
  3. Mark In1.Cu as a power layer so no signal routing is
     attempted on the plane.

Run: python3 hw/make_dsn.py IN.dsn OUT.dsn
"""
import re, sys
sys.path.insert(0, 'hw')
from router import HV_NETS, POWER_NETS, LVDS_NETS

def block_span(text, start):
    """(end_index) of the balanced-paren block starting at start."""
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced")

def class_block(name, nets, width, clearance):
    netlist = " ".join(sorted(nets))
    return (f'    (class {name} "" {netlist}\n'
            f'      (circuit\n'
            f'        (use_via Via[0-3]_600:300_um)\n'
            f'      )\n'
            f'      (rule\n'
            f'        (width {width})\n'
            f'        (clearance {clearance})\n'
            f'      )\n'
            f'    )\n')

def main():
    src, dst = sys.argv[1], sys.argv[2]
    text = open(src).read()
    # --- 1. split the class ---
    ci = text.index("(class kicad_default")
    cj = block_span(text, ci)
    block = text[ci:cj]
    head = block.index('""') + 2
    tail = block.index("(circuit")
    nets = block[head:tail].split()
    groups = {"kicad_default": [], "fr_power": [], "fr_hv": [],
              "fr_lvds": []}
    for n in nets:
        if n in HV_NETS:
            groups["fr_hv"].append(n)
        elif n in POWER_NETS:
            groups["fr_power"].append(n)
        elif n in LVDS_NETS:
            groups["fr_lvds"].append(n)
        else:
            groups["kicad_default"].append(n)
    new_classes = (
        class_block("kicad_default", groups["kicad_default"], 250, 201) +
        class_block("fr_power", groups["fr_power"], 600, 251) +
        class_block("fr_hv", groups["fr_hv"], 400, 1001) +
        class_block("fr_lvds", groups["fr_lvds"], 300, 201))
    text = text[:ci] + new_classes.rstrip() + text[cj:]
    # --- 2. strip F.Cu / B.Cu planes, keep In1.Cu ---
    for layer in ("F.Cu", "B.Cu"):
        pi = text.index(f"(plane GND (polygon {layer}")
        pj = block_span(text, pi)
        text = text[:pi] + text[pj:]
    # --- 3. In1.Cu -> power layer ---
    text = text.replace("(layer In1.Cu\n      (type signal)",
                        "(layer In1.Cu\n      (type power)", 1)
    open(dst, "w").write(text)
    print(f"{dst}: classes "
          + ", ".join(f"{k}={len(v)}" for k, v in groups.items())
          + f"; total nets {len(nets)}")

if __name__ == "__main__":
    main()
