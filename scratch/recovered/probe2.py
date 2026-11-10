#!/usr/bin/env python3
"""Probe: custom (power) symbol in a generated lib — does the instance
Value drive the net name? Does an embedded pdlvds: def resolve?"""
import uuid

def U():
    return str(uuid.uuid4())

SID = U()

pwr_def = '''(symbol "pdlvds:PWR_P3V3D" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom no) (on_board no)
  (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) hide))
  (property "Value" "+3V3D" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol "PWR_P3V3D_0_1"
    (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
    (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
    (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none))))
  (symbol "PWR_P3V3D_1_1"
    (pin power_in line (at 0 0 90) (length 0) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27))))))
)'''

test_def = '''(symbol "pdlvds:PD_TEST" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
  (property "Reference" "R" (at 0 -5.08 0) (effects (font (size 1.27 1.27))))
  (property "Value" "10k" (at 0 5.08 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (symbol "PD_TEST_0_1" (rectangle (start -5.08 -2.54) (end 5.08 2.54) (stroke (width 0.254) (type default)) (fill (type background))))
  (symbol "PD_TEST_1_1"
    (pin passive line (at -7.62 0 0) (length 2.54) (name "A" (effects (font (size 1.0 1.0)))) (number "1" (effects (font (size 1.0 1.0)))))
    (pin passive line (at 7.62 0 180) (length 2.54) (name "B" (effects (font (size 1.0 1.0)))) (number "2" (effects (font (size 1.0 1.0))))))
)'''

inst_pwr = f'''(symbol (lib_id "pdlvds:PWR_P3V3D") (at 50.8 50.8 0) (unit 1) (in_bom no) (on_board no) (dnp no) (uuid {U()})
  (property "Reference" "#PWR01" (at 50.8 47.0 0) (effects (font (size 1.27 1.27)) hide))
  (property "Value" "+3V3D" (at 50.8 54.4 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "" (at 50.8 50.8 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at 50.8 50.8 0) (effects (font (size 1.27 1.27)) hide))
  (instances (project "probe2" (path "/{SID}" (reference "#PWR01") (unit 1)))))'''

# resistor instance: pin 1 connection point at (68.58, 50.8) -> place at (76.2, 50.8)
inst_r = f'''(symbol (lib_id "pdlvds:PD_TEST") (at 76.2 50.8 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {U()})
  (property "Reference" "R99" (at 71.12 45.72 0) (effects (font (size 1.27 1.27))))
  (property "Value" "10k" (at 76.2 55.88 0) (effects (font (size 1.27 1.27))))
  (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 76.2 50.8 0) (effects (font (size 1.27 1.27)) hide))
  (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
  (instances (project "probe2" (path "/{SID}" (reference "R99") (unit 1)))))'''

wire = f'(wire (pts (xy 50.8 50.8) (xy 68.58 50.8)) (stroke (width 0) (type default)) (uuid {U()}))'

out = ['(kicad_sch (version 20230121) (generator "probe")', f'(uuid {SID})',
       '(paper "A4")', '(lib_symbols', pwr_def, test_def, ')',
       inst_pwr, inst_r, wire, '(sheet_instances (path "/" (page "1")))', ')']
open('/tmp/schwork/probe2.kicad_sch', 'w').write("\n".join(out) + "\n")
print("probe written")
