#!/usr/bin/env bash
# Export a 3D GLB of a board with every component model resolved.
#
#   scripts/export_glb.sh <board.kicad_pcb> <out.glb>
#
# Why this exists: the board's footprints reference KiCad library 3D
# models by ${KICAD6_3DMODEL_DIR}-style paths, and the library is not
# installed here or in CI. The repo therefore mirrors every referenced
# model in hw/models3d/ (see hw/models3d/README.md). This script:
#   1. copies the board into a temp dir (the input is never modified),
#   2. binds the project's own models to the custom footprints on the
#      copy (scripts/attach_models.py),
#   3. runs kicad-cli's GLB export with --subst-models (its STEP path
#      is the one that resolves models headlessly) and a throwaway
#      HOME whose KiCad config points the 3D-model variables at the
#      repo mirror.
# Used by scripts/make_fab.sh (fab package) and scripts/site_data.py
# (website build). Best-effort callers should tolerate a non-zero
# exit: without KiCad there is simply no 3D view.
set -eu
cd "$(dirname "$0")/.."
BOARD="$1"
OUT="$2"
MODELS="$PWD/hw/models3d"

TMP=$(mktemp -d)
trap 'find "$TMP" -mindepth 1 -delete; rmdir "$TMP"' EXIT
cp "$BOARD" "$TMP/render.kicad_pcb"
# The project file pairs with the board by basename; give the copy
# the project's real settings file under its own name.
PROJ="$(dirname "$BOARD")/pdlvds_rx.kicad_pro"
[ -f "$PROJ" ] && cp "$PROJ" "$TMP/render.kicad_pro" || true

xvfb-run -a python3 scripts/attach_models.py \
  "$TMP/render.kicad_pcb" "$TMP/render.kicad_pcb"

mkdir -p "$TMP/home/.config/kicad/8.0"
python3 - "$TMP/home/.config/kicad/8.0/kicad_common.json" "$MODELS" <<'PYEOF'
import json, sys
cfg = {"environment": {"vars": {
    "KICAD6_3DMODEL_DIR": sys.argv[2],
    "KICAD7_3DMODEL_DIR": sys.argv[2],
    "KICAD8_3DMODEL_DIR": sys.argv[2]}}}
with open(sys.argv[1], "w") as fh:
    json.dump(cfg, fh)
PYEOF

HOME="$TMP/home" kicad-cli pcb export glb --subst-models --no-dnp \
  -f -o "$OUT" "$TMP/render.kicad_pcb"
echo "export_glb: wrote $OUT"
