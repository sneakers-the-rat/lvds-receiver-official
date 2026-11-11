import sys
sys.path.insert(0, 'hw')
import pcbnew
from build_lib import Surgery

SRC = 'scratch/cand2/pdlvds_rx.kicad_pcb'
s = Surgery(SRC, SRC, nets=('APD_K', 'GND'))
F, I2 = pcbnew.F_Cu, pcbnew.In2_Cu

victims = []
victims += s.find_via('GND', (38.45, 43.62))                       # stitch via too close to CMP_QN on In2
victims += s.find_seg('GND', F, (23.86, 40.00), (22.95, 40.00))    # bridge end 0.325 from RJ2 APD_K pad
victims += s.find_seg('APD_K', I2, (10.50, 29.38), (9.85, 39.85))  # In2 run swung to 0.255 from CL4 GND via
s.remove(victims)

s.add_via('GND', 37.30, 41.75, dia=0.5, drill=0.3)                 # stitch via, north part of the pocket
s.add_track('GND', F, (23.86, 40.00), (23.10, 40.00), 0.30)        # bridge: still crosses frag-4 fill edge, 0.475 clear of RJ2 pad
s.add_track('APD_K', F, (9.85, 39.85), (9.35, 40.05), 0.40)        # F.Cu stub: via -> D1 pad 5
s.add_polyline('APD_K', I2, [(10.50, 29.38), (9.90, 34.50), (9.85, 39.85)], 0.40)  # west jog restores 0.39 to CL4 via

s.finish()
