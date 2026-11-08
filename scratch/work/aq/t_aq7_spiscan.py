"""t_aq7: SPI U8-end dive scan on exp235.
Scan (SCK via, MOSI via) d0.5 pairs in the east pocket
x[71.55,73.30], y[5.65,7.25] under three rip scenarios:
  S0: no rips
  S1: rip +3V3D w0.6 trunk tip (73.625,6.625)->(72.2,5.75) chain
  S2: S1 + rip DAC_SYNC via (72.125,6.875) + its F stub + In2 head
A via is feasible if pt_margin >= 0 on all 3 layers and a straight
F stub from the pad east edge (71.425, y) clears (seg_margin >= 0).
Pairs must clear each other by >= 0.20 (centre dist >= 0.70).
Also scan DAC_SYNC replacement via positions under S2 in
x[68.6,70.2], y[6.7,7.6] (west dive) with stub from (69.975,7.25).
"""
import sys, math, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import (load_items, pt_margin, seg_margin, in_box_pool,
                      fmt_it, apply_rip)

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp235.kicad_pcb')
items = load_items(b)

RIP_3V3D = [('seg', '+3V3D', 73.625, 6.625), ('seg', '+3V3D', 73.375, 6.625),
            ('seg', '+3V3D', 73.125, 6.375), ('seg', '+3V3D', 72.875, 6.375),
            ('seg', '+3V3D', 72.625, 6.125)]
RIP_DAC = [('via', 'DAC_SYNC', 72.125, 6.875),
           ('seg', 'DAC_SYNC', 71.700, 7.250), ('seg', 'DAC_SYNC', 72.375, 6.625)]


def feas(statics, net, x, y, stub_from):
    pool = {li: in_box_pool(statics, (x - 2.5, x + 2.5, y - 2.5, y + 2.5),
                             pad=1.2)[li] for li in range(3)}
    for li in range(3):
        m, _w = pt_margin(li, x, y, net, 0.25, pool[li])
        if m < -0.001:
            return None
    m, w = seg_margin(0, stub_from, (x, y), net, 0.1, pool[0], step=0.01)
    if m < -0.001:
        return None
    return m


def scan(statics, net, box, stub_from, step=0.05):
    out = []
    x = box[0]
    while x <= box[1] + 1e-9:
        y = box[2]
        while y <= box[3] + 1e-9:
            m = feas(statics, net, x, y, stub_from)
            if m is not None:
                mm = 9.9
                pool = in_box_pool(statics, (x - 2.5, x + 2.5, y - 2.5, y + 2.5), pad=1.2)
                for li in range(3):
                    mv, _ = pt_margin(li, x, y, net, 0.25, pool[li])
                    mm = min(mm, mv)
                out.append((round(x, 3), round(y, 3), round(mm, 3)))
            y += step
        x += step
    return out


BOX = (71.55, 73.30, 5.65, 7.25)
for name, rips in (('S0', []), ('S1', RIP_3V3D), ('S2', RIP_3V3D + RIP_DAC)):
    statics, n = apply_rip(items, rips)
    print(f'--- {name}: ripped {n} items')
    sck = scan(statics, 'SPI_SCK', BOX, (71.425, 6.750))
    mosi = scan(statics, 'SPI_MOSI', BOX, (71.425, 6.250))
    print(f'  SCK feasible: {len(sck)}  e.g. {sck[:6]}')
    print(f'  MOSI feasible: {len(mosi)}  e.g. {mosi[:6]}')
    pairs = 0
    best = None
    for (ax, ay, am) in sck:
        for (bx, by, bm) in mosi:
            if math.hypot(ax - bx, ay - by) >= 0.70:
                pairs += 1
                sc = min(am, bm)
                if best is None or sc > best[0]:
                    best = (sc, (ax, ay), (bx, by))
    print(f'  pairs (mutual>=0.70): {pairs}  best {best}')
    if name == 'S2':
        dac = scan(statics, 'DAC_SYNC', (68.60, 70.20, 6.70, 7.60),
                   (69.975, 7.250))
        print(f'  DAC west-dive feasible: {len(dac)}  e.g. {dac[:8]}')
