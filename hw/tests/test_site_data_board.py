#!/usr/bin/env python3
"""Regression tests: the site's current-info pages must derive
from the CURRENT board/schematic at build time.

Defect (found by the project owner, 2026-11-08): /board showed a
board dozens of passes old. scripts/site_data.py staged the board
renders from hw/fab/, which only a manual scripts/make_fab.sh run
regenerates — and make_fab exported hw/pdlvds_rx.kicad_pcb, the
pre-expansion BASE board, not the frontier exp board at all. The
schematic PDF download was a committed results/ file from
2026-11-03 that nothing regenerated, predating the 2026-11-05
schematic changes. The fix, pinned here:

  - site_data.frontier_board() selects the board through
    commit_pass.resolve_board (the pass system's one rule) or the
    SITE_BOARD override — never the base board by default;
  - site_data's board export specs (layer lists) are identical to
    make_fab.sh's, so build-time and fab renders agree;
  - make_fab.sh itself selects the frontier board (text check:
    it must route through resolve_board and must not name the
    base board as its export source);
  - the BOM grouping (parse_bom_netlist) matches make_fab's:
    group by (value, footprint), refs space-joined, groups
    sorted by first ref.

Run: python3 hw/tests/test_site_data_board.py
Pre-fix: FAIL (frontier_board / parse_bom_netlist do not exist;
make_fab.sh names the base board).
"""
import os
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import site_data  # noqa: E402

fails = []


def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


# --- frontier selection: SITE_BOARD override honoured verbatim
with tempfile.TemporaryDirectory() as d:
    fake = os.path.join(d, "pdlvds_rx.exp999.kicad_pcb")
    open(fake, "w").close()
    os.environ["SITE_BOARD"] = fake
    try:
        check("SITE_BOARD override is honoured",
              site_data.frontier_board() == fake)
        os.environ["SITE_BOARD"] = os.path.join(d, "missing.kicad_pcb")
        got = site_data.frontier_board()
        check("missing SITE_BOARD does not come back as the board",
              got != os.environ["SITE_BOARD"])
    finally:
        del os.environ["SITE_BOARD"]

# --- frontier selection: default is an exp board, never the base
got = site_data.frontier_board()
base = os.path.join(ROOT, "hw", "pdlvds_rx.kicad_pcb")
check("default frontier board exists", got is not None
      and os.path.exists(got))
check("default frontier board is not the base board", got != base)
check("default frontier board is an exp board",
      got is not None and ".exp" in os.path.basename(got))

# --- export-spec parity with make_fab.sh (the two exporters of
# the same renders must not drift apart)
fab_src = open(os.path.join(ROOT, "scripts", "make_fab.sh")).read()
for name, spec in site_data.BOARD_SVG_SPECS:
    check(f"make_fab.sh carries the {name} layer spec",
          f"--layers {spec}" in fab_src
          or f'--layers "{spec}"' in fab_src
          or spec in fab_src)
check("make_fab.sh carries the board PDF layer spec",
      site_data.BOARD_PDF_LAYERS in fab_src)
for layer in site_data.BOARD_LAYER_SVGS:
    check(f"make_fab.sh exports layer {layer}", layer in fab_src)

# --- make_fab.sh selects the frontier board via resolve_board
check("make_fab.sh routes board selection through resolve_board",
      "resolve_board" in fab_src)
check("make_fab.sh does not export the base board by default",
      "B=hw/pdlvds_rx.kicad_pcb" not in fab_src)

# --- BOM grouping from a netlist
NETLIST = """<?xml version="1.0"?>
<export version="E">
  <components>
    <comp ref="R2"><value>10k</value><footprint>Resistor_SMD:R_0603</footprint></comp>
    <comp ref="R1"><value>10k</value><footprint>Resistor_SMD:R_0603</footprint></comp>
    <comp ref="C1"><value>100n</value><footprint>Capacitor_SMD:C_0603</footprint></comp>
  </components>
</export>"""
with tempfile.NamedTemporaryFile("w", suffix=".xml",
                                 delete=False) as f:
    f.write(NETLIST)
    nl = f.name
try:
    header, rows = site_data.parse_bom_netlist(nl)
finally:
    os.unlink(nl)
check("BOM header", header == ["Refs", "Qty", "Value", "Footprint"])
check("BOM groups by (value, footprint) in document order",
      ["R2 R1", "2", "10k", "Resistor_SMD:R_0603"] in rows
      and ["C1", "1", "100n", "Capacitor_SMD:C_0603"] in rows
      and len(rows) == 2)
check("BOM groups sorted by first ref",
      rows[0][0].split()[0] < rows[1][0].split()[0])

print()
if fails:
    print(f"{len(fails)} FAILURES")
    sys.exit(1)
print("all checks passed")
