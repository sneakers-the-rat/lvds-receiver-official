#!/usr/bin/env python3
"""Probe 5: does a local (label) anchored mid-segment name the whole
connected wire graph? And anchored at a segment endpoint?"""
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
  (instances (project "probe5" (path "/{SID}" (reference "{ref}") (unit 1)))))'''

def wire(x1, y1, x2, y2):
    return f'(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid {U()}))'

def label(name, x, y, rot=0):
    return f'(label "{name}" (at {x} {y} {rot}) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {U()}))'

defs, parts, wires, labels = [], [], [], []
# group 1: y=50.8, A-B wire, label mid-segment at (63.5, 50.8)
for ref in ("LA", "LB"):
    defs.append(boxdef(f"PD_{ref}"))
parts.append(inst("PD_LA", "LA", 50.8, 50.8))
parts.append(inst("PD_LB", "LB", 101.6, 50.8))
wires.append(wire(43.18, 50.8, 93.98, 50.8))
labels.append(label("MIDNET", 63.5, 50.8))
# group 2: y=101.6, label at endpoint (43.18, 101.6)
for ref in ("MA", "MB"):
    defs.append(boxdef(f"PD_{ref}"))
parts.append(inst("PD_MA", "MA", 50.8, 101.6))
parts.append(inst("PD_MB", "MB", 101.6, 101.6))
wires.append(wire(43.18, 101.6, 93.98, 101.6))
labels.append(label("ENDNET", 43.18, 101.6))
out = ['(kicad_sch (version 20230121) (generator "probe")', f'(uuid {SID})',
       '(paper "A4")', '(lib_symbols'] + defs + [')'] + parts + wires + labels + \
      ['(sheet_instances (path "/" (page "1")))', ')']
open('/tmp/schwork/probe5.kicad_sch', 'w').write("\n".join(out) + "\n")
print("written")
