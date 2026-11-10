"""build_rst v1: USB_RST, the last net (exp257 -> exp258).

Composition (each fence from the exp257 censuses, facts_rst*.py):
- DM_PHY F loop re-laid west (vertical x74.125 -> x73.42) -- the
  named fence partner; its east edge was flush with U7.9's stub.
- GND stitch via (73.434,17.685) moved to (72.8,18.2) so the DM
  loop can bow west around where it stood.
- ULPI_DIR B journey re-laid as a SOUTH BOW (drop at x75.05,
  westward at y19.6-19.95, up to the kept joint (71.375,19.125))
  -- its v5 westward legs sealed the B pocket south of U7.
- USB_RST: F stub x74.25 to via (74.25,18.55); B west, bow north
  around the moved GND via, dive south at x72.2 (west of the
  PHY_1V8A B column, the +3V3A band west end, the GND via
  (72.9,9.45)); B stub east to via (72.55,5.3); In2 hop over the
  I2C_SCL B staircase (bow north around SPI_MOSI's In2 end);
  via (73.9,5.3); F arrival (74.75,5.3) -> U6.40 (74.75,4.662).
Judge: KiCad DRC + check_pcb on the built board only.
"""
import sys
sys.path.insert(0, 'hw')
import build_lib as BL

S = BL.Surgery('hw/pdlvds_rx.exp257.kicad_pcb',
               'hw/pdlvds_rx.exp258.kicad_pcb',
               nets=('DM_PHY', 'GND', 'ULPI_DIR', 'USB_RST'))

# ---- find ALL victims first, then remove (SWIG-safe order) ----
victims = []
victims += S.find_seg('DM_PHY', BL.F, (73.562, 17.0), (74.125, 17.375))
victims += S.find_seg('DM_PHY', BL.F, (74.125, 17.375), (74.125, 18.625))
victims += S.find_seg('DM_PHY', BL.F, (74.125, 18.625), (73.875, 18.875))
victims += S.find_seg('DM_PHY', BL.F, (73.875, 18.875), (73.625, 19.125))
w_dm = S.width_of_last_rip()
victims += S.find_seg('ULPI_DIR', BL.B, (74.82, 18.10), (73.3, 18.42))
victims += S.find_seg('ULPI_DIR', BL.B, (73.3, 18.42), (71.375, 19.125))
w_dir = S.width_of_last_rip()
gv = S.find_via('GND', (73.434, 17.685))
victims += gv
gnd_dia = gv[0].GetWidth() / 1e6
gnd_drill = gv[0].GetDrill() / 1e6
print(f'GND via dims: dia={gnd_dia} drill={gnd_drill}')
S.remove(victims)

# ---- GND via re-sited ----
S.add_via('GND', 72.8, 18.2, dia=gnd_dia, drill=gnd_drill)

# ---- DM_PHY F loop, bowed west ----
S.add_polyline('DM_PHY', BL.F,
               [(73.562, 17.0), (73.42, 17.5), (73.42, 18.7),
                (73.55, 19.0), (73.625, 19.125)], w_dm)

# ---- ULPI_DIR B journey, south bow ----
S.add_polyline('ULPI_DIR', BL.B,
               [(74.82, 18.10), (75.05, 18.9), (75.05, 19.6),
                (72.35, 19.95), (71.375, 19.125)], w_dir)

# ---- USB_RST ----
S.add_track('USB_RST', BL.F, (74.25, 16.875), (74.25, 18.55), 0.2)
S.add_via('USB_RST', 74.25, 18.55)
S.add_polyline('USB_RST', BL.B,
               [(74.25, 18.55), (73.35, 18.5), (72.95, 18.92),
                (72.2, 18.92), (72.2, 5.3), (72.55, 5.3)], 0.2)
S.add_via('USB_RST', 72.55, 5.3)
S.add_polyline('USB_RST', BL.IN2,
               [(72.55, 5.3), (73.3, 5.75), (73.9, 5.3)], 0.2)
S.add_via('USB_RST', 73.9, 5.3)
S.add_polyline('USB_RST', BL.F,
               [(73.9, 5.3), (74.75, 5.3), (74.75, 4.662)], 0.2)

S.finish()
