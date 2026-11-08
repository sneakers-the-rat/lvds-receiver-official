"""t_ap24: survey dumps for the six long-haul single endpoints on
exp234 (CAP_CLK, CAP_DATA, CDR_LOS, SPI_SCK, SPI_MOSI, +3V3D U11.14).
Prints pads + all copper within 3.5 mm of each endpoint pad."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp234.kicad_pcb')
items = load_items(b)
ENDPOINTS = {
    'CAP_CLK': [(71.338, 1.75), (76.525, 13.75)],
    'CAP_DATA': [(71.338, 2.25), (76.525, 14.25)],
    'CDR_LOS': [(92.662, 1.75), (68.688, 36.5)],
    'SPI_SCK': [(70.7, 6.75), None],
    'SPI_MOSI': [(70.7, 7.25), None],
    '+3V3D_U11': [(56.75, 24.812), (66.55, 22.75)],
}
for net, pts in ENDPOINTS.items():
    for pt in pts:
        if pt is None:
            continue
        print(f'=== {net} near {pt}')
        for li in range(3):
            for it in items[li]:
                k, n, d, clr = it
                if k == 'pad':
                    cx, cy = d[0], d[1]
                elif k == 'via':
                    cx, cy = d[0], d[1]
                else:
                    cx, cy = (d[0] + d[2]) / 2, (d[1] + d[3]) / 2
                if abs(cx - pt[0]) <= 3.5 and abs(cy - pt[1]) <= 3.5:
                    print(f'  L{li} {fmt_it(it)}')
