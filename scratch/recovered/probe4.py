#!/usr/bin/env python3
"""Probe 4: which joining forms does KiCad's netlist extraction honour?
 F: main wire SPLIT at join point (shared endpoints), branch ends there, no dot
 G: branch crosses main mid-segment, junction dot diameter 0.9144 at crossing
 H: T-join with junction dot diameter 0.9144
 I: T-join, junction present but main wire also split (belt and braces)"""
import uuid

def U():
    return str(uuid.uuid4())

SID = U()

def boxdef(name):
    return f'''(symbol "pdlvds:{name}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
  (property "Reference" "R" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
  (property "Value" "10k" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol "{name}_0_1" (rectangle (start -5.08 -2.54) (end 5.08 2.54) (stroke (width 0.254) (type default)) (fill (type background))))
  (symbol "{name}_1_1"
    (pin passive line (at -7.62 0 0) (length 2.54) (name "P" (effects (font (size 1.0 1.0)))) (number "1" (effects (font (size 1.0 1.0))))))
)'''

def inst(name, ref, x, y):
    return f'''(symbol (lib_id "pdlvds:{name}") (at {x} {y} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {U()})
  (property "Reference" "{ref}" (at {x-5.08} {y-5.08} 0) (effects (font (size 1.27 1.27))))
  (property "Value" "10k" (at {x} {y+5.08} 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at {x} {y} 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (instances (project "probe4" (path "/{SID}" (reference "{ref}") (unit 1)))))'''

def wire(x1, y1, x2, y2):
    return f'(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid {U()}))'

def junc(x, y, d):
    return f'(junction (at {x} {y}) (diameter {d}) (color 0 0 0 0) (uuid {U()}))'

# Four independent groups at different y rows. Each: main pair A-B on y, branch from above.
groups = [
    # (y, refA, refB, refC, wires_builder, junctions)
    (50.8, "FA", "FB", "FC", "split"),
    (101.6, "GA", "GB", "GC", "crossdot"),
    (152.4, "HA", "HB", "HC", "tdot"),
    (203.2, "IA", "IB", "IC", "splitdot"),
]
defs, parts, wires, juncs = [], [], [], []
for (y, ra, rb, rc, mode) in groups:
    for ref in (ra, rb, rc):
        defs.append(boxdef(f"PD_{ref}"))
    parts.append(inst(f"PD_{ra}", ra, 50.8, y))          # pin (43.18, y)
    parts.append(inst(f"PD_{rb}", rb, 101.6, y))         # pin (93.98, y)
    parts.append(inst(f"PD_{rc}", rc, 76.2, y - 25.4))   # pin (68.58, y-25.4)
    mid = 68.58
    if mode == "split":
        wires.append(wire(43.18, y, mid, y))
        wires.append(wire(mid, y, 93.98, y))
        wires.append(wire(mid, y - 25.4, mid, y))
    elif mode == "crossdot":
        wires.append(wire(43.18, y, 93.98, y))
        wires.append(wire(mid, y - 25.4, mid, y + 12.7))  # crosses main
        juncs.append(junc(mid, y, 0.9144))
    elif mode == "tdot":
        wires.append(wire(43.18, y, 93.98, y))
        wires.append(wire(mid, y - 25.4, mid, y))
        juncs.append(junc(mid, y, 0.9144))
    elif mode == "splitdot":
        wires.append(wire(43.18, y, mid, y))
        wires.append(wire(mid, y, 93.98, y))
        wires.append(wire(mid, y - 25.4, mid, y))
        juncs.append(junc(mid, y, 0.9144))
out = ['(kicad_sch (version 20230121) (generator "probe")', f'(uuid {SID})',
       '(paper "A3")', '(lib_symbols'] + defs + [')'] + parts + wires + juncs + \
      ['(sheet_instances (path "/" (page "1")))', ')']
open('/tmp/schwork/probe4.kicad_sch', 'w').write("\n".join(out) + "\n")
print("written")
