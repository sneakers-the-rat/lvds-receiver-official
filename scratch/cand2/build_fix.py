import sys
sys.path.insert(0, 'hw')
import pcbnew
from build_lib import Surgery

SRC = 'scratch/cand2/pdlvds_rx.kicad_pcb'
s = Surgery(SRC, SRC, nets=('APD_K', 'HV_R29M', 'GND'))
F, B, I2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu

# ---- find all victims first (house pattern) ----
victims = []
# E1: APD_K staircase NE end + vertical at x=21.88 (passes 0.072 mm from CL1 pad 1)
for a, b in [((20.88, 29.88), (21.12, 30.12)), ((21.12, 30.12), (21.38, 30.38)),
             ((21.38, 30.38), (21.62, 30.62)), ((21.62, 30.62), (21.88, 30.88)),
             ((21.88, 30.88), (21.88, 38.62))]:
    victims += s.find_seg('APD_K', F, a, b)
# E2: APD_K via at D1 + its In2 feed track (via sits 0.320 mm from D1 anode pad 6)
victims += s.find_via('APD_K', (9.50, 39.75))
victims += s.find_seg('APD_K', I2, (10.50, 29.38), (9.50, 39.75))
# E3: HV_R29M B.Cu staircase hugging the HV_VC2 via (0.222 mm at ~253 V vs a 2 V net)
for a, b in [((23.12, -1.88), (23.38, -2.12)), ((23.38, -2.12), (23.62, -2.38)),
             ((23.62, -2.38), (23.88, -2.62)), ((23.88, -2.62), (24.12, -2.88)),
             ((24.12, -2.88), (24.38, -3.12)), ((24.38, -3.12), (24.38, -3.62)),
             ((24.38, -3.62), (24.62, -3.88))]:
    victims += s.find_seg('HV_R29M', B, a, b)
s.remove(victims)

# ---- additions ----
# E1: vertical at x=20.88 (0.47 mm clear of CL1 pad 1) + top horizontal
s.add_track('APD_K', F, (20.88, 29.88), (20.88, 38.62), 0.40)
s.add_track('APD_K', F, (20.88, 38.62), (21.88, 38.62), 0.40)
# E2: via moved east/north (0.57 mm clear of D1 pad 6), In2 feed re-ended
s.add_via('APD_K', 9.85, 39.85, dia=0.5, drill=0.3)
s.add_track('APD_K', I2, (10.50, 29.38), (9.85, 39.85), 0.40)
# E3: staircase re-laid ~0.35 mm east of the HV_VC2 via
s.add_polyline('HV_R29M', B, [(23.12, -1.88), (23.90, -2.30), (24.20, -2.60),
                              (24.50, -2.90), (24.70, -3.15), (24.70, -3.62),
                              (24.62, -3.88)], 0.40)
# E4a: stitch via for the floating C7/C44 ground pocket
s.add_via('GND', 38.45, 43.62, dia=0.6, drill=0.3)
# E4b: bridge track from U2 pin 2 west to the main pour (trial)
s.add_track('GND', F, (23.86, 40.00), (22.95, 40.00), 0.30)

s.finish()
