#!/usr/bin/env python3
"""Probe KiCad wire-joining rules:
 A--B straight wire; C path T-joins AB mid-segment WITH junction dot;
 D path T-joins AB mid-segment WITHOUT dot; E path ends ON AB (endpoint
 on segment, no dot). Which join the net?"""
import uuid, sys

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
  (instances (project "probe3" (path "/{SID}" (reference "{ref}") (unit 1)))))'''

def wire(x1, y1, x2, y2):
    return f'(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid {U()}))'

# pin points: A at (42.42,50) via instance (50,50) pin at -7.62 -> (42.38,50) hmm use clean numbers:
# instance at (50.8, 50.8): pin point (43.18, 50.8). B instance at (101.6, 50.8): pin (93.98, 50.8)
parts = []
defs = []
for i, ref in enumerate(["RA", "RB", "RC", "RD", "RE"]):
    nm = f"PD_{ref}"
    defs.append(boxdef(nm))
xs = {"RA": 50.8, "RB": 101.6, "RC": 76.2, "RD": 63.5, "RE": 88.9}
ys = {"RA": 50.8, "RB": 50.8, "RC": 25.4, "RD": 76.2, "RE": 76.2}
for ref in ["RA", "RB", "RC", "RD", "RE"]:
    parts.append(inst(f"PD_{ref}", ref, xs[ref], ys[ref]))
# pin points: RA (43.18,50.8) RB (93.98,50.8) RC (68.58,25.4) RD (55.88,76.2) RE (81.28,76.2)
w = []
w.append(wire(43.18, 50.8, 93.98, 50.8))            # A-B main
w.append(wire(68.58, 25.4, 68.58, 50.8))            # C down to AB mid (68.58) WITH dot
w.append(wire(55.88, 76.2, 55.88, 50.8))            # D up to AB mid (55.88) NO dot
w.append(wire(81.28, 76.2, 81.28, 57.15))           # E partway...
w.append(wire(81.28, 57.15, 81.28, 50.8))           # E endpoint on AB, no dot (two segs)
j = [f'(junction (at 68.58 50.8) (diameter 0) (color 0 0 0 0) (uuid {U()}))']
out = ['(kicad_sch (version 20230121) (generator "probe")', f'(uuid {SID})',
       '(paper "A4")', '(lib_symbols'] + defs + [')'] + parts + w + j + \
      ['(sheet_instances (path "/" (page "1")))', ')']
open('/tmp/schwork/probe3.kicad_sch', 'w').write("\n".join(out) + "\n")
print("written")
