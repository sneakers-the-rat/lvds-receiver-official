# Schematic redraw — evidence package (2026-11-08)

The generated schematic (`hw/pdlvds_rx.kicad_sch`, produced by
`hw/gen_schematic.py` from `hw/circuit.py`) was redrawn in a
human style — one framed, titled region per subsystem group,
drawn wires inside a region, local power symbols at pins, net
labels only where a net leaves its region — **without changing
the logical structure by a single pin**. This directory is the
proof and the before/after record.

## Logical identity (the hard constraint)

Method: canonical snapshot of the exported netlist
(`hw/schematic_snapshot.py`): every component as
`ref | value | footprint`, every net as
`name :: sorted ref.pin members` (`unconnected-*` nets
canonicalised to `NC`, pin membership kept exact).

- `snapshot-baseline.txt` — from the pre-redraw schematic
  (152 components, 223 nets: 120 named + 103 single-pin
  unconnected, 545 pins on named nets, 648 connected pins total).
- `snapshot-final.txt` — from the redrawn schematic.
- `snapshot-diff.txt` — `diff` of the two: **0 bytes (identical)**.
- `hw/check_netlist.py` on the redrawn netlist: **PASS**
  (648 connected pins, 223 nets, 545 expected connections).

Reproduce:

```
python3 hw/gen_schematic.py
kicad-cli sch export netlist --format kicadxml -o /tmp/n.xml hw/pdlvds_rx.kicad_sch
python3 hw/check_netlist.py /tmp/n.xml
python3 hw/schematic_snapshot.py /tmp/n.xml > /tmp/snap.txt
python3 hw/schematic_snapshot.py --compare \
    results/schematic-redraw-2026-11-08/snapshot-baseline.txt /tmp/snap.txt
```

## ERC

- `erc-baseline.txt`: 0 errors, 8 warnings (all
  `lib_symbol_issues` on PWR_FLAG).
- `erc-final.txt`: **0 errors, 0 warnings**.

## What the redraw does (generator, not hand edits)

- One framed region per `group` in circuit.py (afe, hv, pwr,
  cdr, mcu, usb, mech, cap, dac, misc), titled, shelf-packed in
  declaration order on an A0 sheet; all geometry on the 1.27 mm
  grid, derived from the real symbol pin coordinates (multi-pin
  symbols keep their library pin geometry; the STM32 pin map is
  unchanged).
- Pin connections classified per pin: **wire** (net contained
  in one region → drawn), **power** (global rails GND/+5V/+3V3D/
  +3V3A/+VA/−VA/NEG_RAW → local power symbol at the pin),
  **label** (net leaves the region → short stub + global label).
  Rails local to one region (+3V3D_CDR, PHY_1V8, PHY_1V8A) are
  drawn as wires. APD_K is deliberately a signal (a power symbol
  would add a driven power_in pin and change ERC).
- Intra-region wires are routed orthogonally per region (A* on
  the grid; bodies are obstacles, text zones are costs) and
  **subdivided at every self-touch** before emission: KiCad 8's
  file-based netlist extraction connects wires only at shared
  endpoints — a T-join, with or without a junction dot, does not
  join (proven with minimal probe schematics during the work).
  Junction dots are emitted at degree ≥ 3 vertices as the visual
  marker only.
- Each drawn net carries exactly one global label anchored on
  its longest segment, naming it (a wire alone would get a
  generated `Net-(...)` name; a local label would name it
  `/NAME`). The anchor is kept off foreign-wire crossings — a
  label anchored on a crossing attaches to the wrong graph
  (found live: DP_PHY).
- PWR_FLAGs for the 8 driven nets are homed in their regions as
  a small flag strip (power symbol — wire — PWR_FLAG), not
  exiled to a corner.
- 2-pin parts stand vertically when one pin is GND (rail symbol
  above, ground below); their long spec-note values run
  left-justified in a 1.0 mm font so adjacent values in a row
  (the HV divider chain) stay legible.

## Wire-vs-label statistics (final generator run)

- 545 connected pins total:
  - **203 pins (37%)** on drawn wires — 75 intra-region nets,
    461 wire segments, 23 junction dots, 75 on-wire naming labels;
  - **243 pins (45%)** on local power symbols (global rails);
  - **99 pins (18%)** on stub + global label — every one a net
    that leaves its region (by construction: a pin is only
    labelled when its net has pins in another region or is a
    2-pin inter-region link).
- 12 no-connect markers, as before.

## Renders

- `schematic-before.pdf` / `schematic-before.svg` — exported
  from the pre-redraw schematic (git HEAD at the time).
- `schematic-after.pdf` / `schematic-after.svg` — exported from
  the redrawn schematic committed alongside this package.
