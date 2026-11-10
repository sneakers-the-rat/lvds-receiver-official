"""build_xi v1: the user's XI design, built and refereed (no scans).

exp256 -> exp257:
- ULPI_NXT escape re-laid bowed west, passing EAST then south of
  the DIR stub fan: F (75.25,16.875) -> (75.55,17.85) ->
  (74.55,18.70) -> kept dive via (74.5,19.25).
- ULPI_DIR via nudged west along its row to (74.90,17.521)
  (waist to STP dive = 1.245); F stub re-laid with a short east
  step; B seg re-laid straight to (71.375,19.125).
- XI bent ride on B: arc via (75.625,18.625) -> waist -> east lane
  x75.60 -> west jog -> lane x74.98 -> NE jog -> PV (75.82,10.30).
Judge: KiCad DRC + check_pcb on the built board only.
"""
import sys
sys.path.insert(0, 'hw')
import build_lib as BL

S = BL.Surgery('hw/pdlvds_rx.exp256.kicad_pcb',
               'hw/pdlvds_rx.exp257.kicad_pcb',
               nets=('ULPI_NXT', 'ULPI_DIR', 'XI', 'ULPI_STP'))

# ---- find ALL victims first, then remove (SWIG-safe order) ----
victims = []
victims += S.find_seg('ULPI_NXT', BL.F, (75.25, 16.875), (74.65, 17.8))
victims += S.find_seg('ULPI_NXT', BL.F, (74.65, 17.8), (74.5, 19.25))
w_nxt = S.width_of_last_rip()
victims += S.find_seg('ULPI_DIR', BL.F, (75.75, 16.875), (75.5, 17.521))
w_dir = S.width_of_last_rip()
victims += S.find_seg('ULPI_DIR', BL.B, (75.5, 17.521), (71.375, 19.125))
victims += S.find_via('ULPI_DIR', (75.5, 17.521))
S.remove(victims)

# ---- NXT escape, bowed west (underpass of the DIR stub fan) ----
S.add_polyline('ULPI_NXT', BL.F,
               [(75.25, 16.875), (75.55, 17.85), (74.55, 18.70),
                (74.5, 19.25)], w_nxt)

# ---- DIR via west + stub + B journey head ----
S.add_via('ULPI_DIR', 74.90, 17.521)
S.add_polyline('ULPI_DIR', BL.F,
               [(75.75, 16.875), (75.72, 17.30), (74.90, 17.521)], w_dir)
S.add_track('ULPI_DIR', BL.B, (74.90, 17.521), (71.375, 19.125), w_dir)

# ---- XI bent ride on B into PV ----
S.add_polyline('XI', BL.B,
               [(75.625, 18.625), (75.42, 18.15), (75.48, 17.74),
                (75.60, 16.95), (75.60, 16.30), (74.98, 15.95),
                (74.98, 13.40), (75.32, 12.75), (75.82, 10.30)], 0.2)

S.finish()
