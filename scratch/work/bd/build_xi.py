"""build_xi v3 (family C): NXT leaves F early; DIR via goes south.

Referee history: v1 (drc257.json) connected XI but the F-layer
scissor (DIR stub vs NXT F escape) cost 14; v2 (drc257_v2.json)
cut it to 3 items, all the same scissor + CAP_DATA graze. The
strip south of the U7 pad row cannot hold both F dives plus the
DIR via at waist >= 1.10 from the STP dive. So:

exp256 -> exp257:
- ULPI_NXT: short F stub (75.25,16.875) -> new via NV
  (75.0,17.3); In2 (74.42,17.75) -> kept dive via (74.5,19.25).
- ULPI_DIR: via DV south at (74.8,17.96) (waist to STP dive
  1.241); F stub threads east of NV then dives; B journey bends
  at (73.8,18.65) to the kept joint (71.375,19.125).
- XI bent ride on B: unchanged from v1/v2 (connected clean
  twice): arc (75.625,18.625) -> waist -> east lane x75.60 ->
  west jog -> lane x74.98 -> NE jog -> PV (75.82,10.30).
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

# ---- NXT: F stub to NV, In2 escape to the kept dive via ----
S.add_track('ULPI_NXT', BL.F, (75.25, 16.875), (75.0, 17.3), w_nxt)
S.add_via('ULPI_NXT', 75.0, 17.3)
S.add_polyline('ULPI_NXT', BL.IN2,
               [(75.0, 17.3), (74.42, 17.75), (74.5, 19.25)], w_nxt)

# ---- DIR: stub thread + south via + bent B journey ----
S.add_via('ULPI_DIR', 74.8, 17.96)
S.add_polyline('ULPI_DIR', BL.F,
               [(75.75, 16.875), (75.65, 17.32), (75.45, 17.85),
                (74.8, 17.96)], w_dir)
S.add_polyline('ULPI_DIR', BL.B,
               [(74.8, 17.96), (73.8, 18.65), (71.375, 19.125)], w_dir)

# ---- XI bent ride on B into PV ----
S.add_polyline('XI', BL.B,
               [(75.625, 18.625), (75.42, 18.15), (75.48, 17.74),
                (75.60, 16.95), (75.60, 16.30), (74.98, 15.95),
                (74.98, 13.40), (75.32, 12.75), (75.82, 10.30)], 0.2)

S.finish()
