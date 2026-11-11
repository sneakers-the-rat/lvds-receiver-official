#!/usr/bin/env bash
# Fabrication outputs into hw/fab/ from the CURRENT board: the
# newest hw/pdlvds_rx.exp<N>.kicad_pcb, selected by the pass
# system's own rule (scripts/commit_pass.py resolve_board — the
# same selection scripts/site_data.py uses for the site's board
# renders). This script used to fab hw/pdlvds_rx.kicad_pcb, the
# pre-expansion BASE board, so the fab package — and, through the
# fab-outputs artefact, the project site — silently described a
# board dozens of passes old. resolve_board refuses when no exp
# board exists; with `set -e` that refusal fails this script
# loudly rather than fabbing the wrong board. An explicit board
# can still be forced with MAKE_FAB_BOARD=<path>.
set -eu
cd "$(dirname "$0")/.."
mkdir -p hw/fab
if [ -n "${MAKE_FAB_BOARD:-}" ]; then
  B="$MAKE_FAB_BOARD"
else
  B=$(python3 - <<'PYEOF'
import contextlib, os, sys
sys.path.insert(0, "scripts")
from commit_pass import resolve_board
with contextlib.redirect_stdout(sys.stderr):
    path = resolve_board(None, "hw")
print(os.path.relpath(path))
PYEOF
)
fi
echo "make_fab: board = $B"
kicad-cli pcb export gerbers -o hw/fab/ "$B"
kicad-cli pcb export drill --format excellon -o hw/fab/ "$B"
kicad-cli pcb export pos --format csv --units mm -o hw/fab/cpl.csv "$B"
# SVG exports are board-cropped (--page-size-mode 2
# --exclude-drawing-sheet: no A4 drawing sheet / title block, the
# viewBox is the board's own extent) — the same flags the pass
# renders use (scripts/snapshot_route.py), so a fab SVG is the
# board itself and can be sent around as a single file.
kicad-cli pcb export svg --layers F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,B.SilkS,Edge.Cuts \
    --page-size-mode 2 --exclude-drawing-sheet \
    -o hw/fab/board-layers.svg "$B"
kicad-cli pcb export pdf --layers F.Cu,In1.Cu,In2.Cu,B.Cu \
    -o hw/fab/board-layers.pdf "$B"
# per-layer SVGs for the site
for L in F.Cu In1.Cu In2.Cu B.Cu F.SilkS Edge.Cuts; do
  kicad-cli pcb export svg --layers "$L" \
    --page-size-mode 2 --exclude-drawing-sheet \
    -o "hw/fab/layer-$L.svg" "$B"
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
# Schematic PDF + SVG ride along in the fab package: CI's
# build-site job has no KiCad, so these exports from the current
# schematic are how /schematic/ stays current there (site_data.py
# stages them from hw/fab/ when it cannot export them itself).
kicad-cli sch export pdf -o hw/fab/schematic.pdf hw/pdlvds_rx.kicad_sch
mkdir -p hw/fab/.sch-svg
kicad-cli sch export svg -o hw/fab/.sch-svg hw/pdlvds_rx.kicad_sch
mv hw/fab/.sch-svg/*.svg hw/fab/schematic.svg
rmdir hw/fab/.sch-svg
# top/bottom assembly renders as SVG -> PNG if a converter exists
kicad-cli pcb export svg --layers F.Cu,F.SilkS,Edge.Cuts \
    --page-size-mode 2 --exclude-drawing-sheet -o hw/fab/board-top.svg "$B"
kicad-cli pcb export svg --layers B.Cu,B.SilkS,Edge.Cuts \
    --page-size-mode 2 --exclude-drawing-sheet -o hw/fab/board-bottom.svg "$B"
( cd hw/fab && zip -q -r gerbers.zip . -i "*.gbr" "*.gbrjob" "*.drl" 2>/dev/null || \
  zip -q -r gerbers.zip . -i "*.gtl" "*.gbl" "*.gts" "*.gbs" "*.gto" "*.gbo" "*.drl" ) || true
# Interactive 3D model for the website (not a fab input; rides along
# in the package so CI's build-site job can stage it). Best-effort:
# a GLB failure must never sink the gerbers.
bash scripts/export_glb.sh "$B" hw/fab/board-3d.glb || \
  echo "make_fab: WARNING — board-3d.glb export failed, continuing"
ls hw/fab/
