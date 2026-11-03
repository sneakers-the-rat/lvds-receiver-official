#!/usr/bin/env bash
# Fabrication outputs into hw/fab/ from hw/pdlvds_rx.kicad_pcb.
set -eu
cd "$(dirname "$0")/.."
mkdir -p hw/fab
B=hw/pdlvds_rx.kicad_pcb
kicad-cli pcb export gerbers -o hw/fab/ "$B"
kicad-cli pcb export drill --format excellon -o hw/fab/ "$B"
kicad-cli pcb export pos --format csv --units mm -o hw/fab/cpl.csv "$B"
kicad-cli pcb export svg --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,B.SilkS,Edge.Cuts \
    -o hw/fab/board-layers.svg "$B"
kicad-cli pcb export pdf --layers F.Cu,In1.Cu,In2.Cu,B.Cu \
    -o hw/fab/board-layers.pdf "$B"
# per-layer SVGs for the site
for L in F.Cu In1.Cu In2.Cu B.Cu F.SilkS Edge.Cuts; do
  kicad-cli pcb export svg --layers "$L" -o "hw/fab/layer-$L.svg" "$B"
done
# BOM from the verified netlist
python3 - << 'PY'
import csv, xml.etree.ElementTree as ET
from collections import defaultdict
tree = ET.parse("results/netlist.xml")
groups = defaultdict(list)
for comp in tree.getroot().iter("comp"):
    fp = comp.findtext("footprint") or ""
    groups[(comp.findtext("value"), fp)].append(comp.get("ref"))
with open("hw/fab/bom.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Refs", "Qty", "Value", "Footprint"])
    for (val, fp), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
        w.writerow([" ".join(refs), len(refs), val, fp])
print("BOM rows:", len(groups))
PY
# top/bottom assembly renders as SVG -> PNG if a converter exists
kicad-cli pcb export svg --layers F.Cu,F.SilkS,Edge.Cuts -o hw/fab/board-top.svg "$B"
kicad-cli pcb export svg --layers B.Cu,B.SilkS,Edge.Cuts -o hw/fab/board-bottom.svg "$B"
( cd hw/fab && zip -q -r gerbers.zip . -i "*.gbr" "*.gbrjob" "*.drl" 2>/dev/null || \
  zip -q -r gerbers.zip . -i "*.gtl" "*.gbl" "*.gts" "*.gbs" "*.gto" "*.gbo" "*.drl" ) || true
ls hw/fab/
