"""build_xi v4 (family C, referee-tuned): NXT leaves F early.

Referee history: v1/v2 F-scissor (drc257{,_v2}.json); v3
(drc257_v3.json) killed the scissor but named family C's fences:
In2 leg passed 0.37 from the DIR via, NV-DV vias 0.011 short,
the kept NXT dive via dangled on F, the DIR B journey grazed
DM_PHY via (73.625,19.125) r0.30 and CAP_DATA via (72.600,19.300)
r0.25 (centres from facts_vias.py), stub leg1 grazed the STP
column. v4 answers each from those built-state numbers:

- NV (74.94,17.36); In2 bows west via (74.10,17.70) around
  DV (74.82,18.10) (NV-DV 0.750, waist DV-dive 1.253).
- Dive via gets a short F stub east to (75.0,19.25).
- DIR F stub bends (75.60,17.30) (0.45 from STP column) and
  (75.42,17.95) (0.62 from NV).
- DIR B journey bends (73.3,18.42): GND via 0.69, DM via 0.76,
  CAP_DATA via 0.59-0.72 perpendicular.
- XI ride unchanged (connected clean in v1-v3).
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

# ---- NXT: F stub to NV, In2 escape west-bowed to the dive via,
# ---- plus a short F stub off the dive via (kills its dangling)
S.add_track('ULPI_NXT', BL.F, (75.25, 16.875), (74.94, 17.36), w_nxt)
S.add_via('ULPI_NXT', 74.94, 17.36)
S.add_polyline('ULPI_NXT', BL.IN2,
               [(74.94, 17.36), (74.10, 17.70), (74.5, 19.25)], w_nxt)
S.add_track('ULPI_NXT', BL.F, (74.5, 19.25), (75.0, 19.25), w_nxt)

# ---- DIR: stub thread + south via + bent B journey ----
S.add_via('ULPI_DIR', 74.82, 18.10)
S.add_polyline('ULPI_DIR', BL.F,
               [(75.75, 16.875), (75.60, 17.30), (75.42, 17.95),
                (74.82, 18.10)], w_dir)
S.add_polyline('ULPI_DIR', BL.B,
               [(74.82, 18.10), (73.3, 18.42), (71.375, 19.125)], w_dir)

# ---- XI bent ride on B into PV ----
S.add_polyline('XI', BL.B,
               [(75.625, 18.625), (75.42, 18.15), (75.48, 17.74),
                (75.60, 16.95), (75.60, 16.30), (74.98, 15.95),
                (74.98, 13.40), (75.32, 12.75), (75.82, 10.30)], 0.2)

S.finish()
