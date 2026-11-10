"""t_au15: rebuilt-pocket model + SCL chord + DATA entry.
Pocket changes vs exp241esc:
- U9 pads shifted -1.0 in x (centre (67.25,2.75)).
- SCL via (69.375,1.375) r0.3 ripped -> new via (69.35,1.40) r0.25;
  SCL F pocket segs ripped; SCL In2 diagonal+tail ripped.
- SDA via (69.32,2.14) ripped -> new via (69.4,2.2) r0.25.
- GND EP feed segs ripped (re-laid in build step).
- TMP_ALERT F segs from old pad ripped.
Added hand items: SCL via, SDA via + F stub + In2 hop + staircase
restore, GND EP chain, TMP re-fan.
Then: SCL In2 chord A* (slot centreline sum>=70.0 fenced), DATA
entry fine A* (0.025, box x[64.5,71.5] y[0,8]) to rejoin (65.35,4.65).
All gates printed."""
import sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
import t_au1_lib as U
import t_ai_lib as L
import pcbnew
from router import netclass

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items_full = L.load_items(board)

C = U.item_centre


def near(it, x, y, tol=0.01):
    c = C(it)
    return abs(c[0] - x) < tol and abs(c[1] - y) < tol


RIPS = []
# SCL via old (all layers handled by centre match)
RIPS.append(lambda l, it: it[0] == 'via' and it[1] == 'I2C_SCL'
            and near(it, 69.375, 1.375, 0.01))
# SCL F pocket segs (the y1.625 staircase + diagonal + fanout)
RIPS.append(lambda l, it: l == 0 and it[1] == 'I2C_SCL' and it[0] == 'seg'
            and 66.8 < C(it)[0] < 69.6 and 1.0 < C(it)[1] < 2.2)
# SCL In2 diagonal + tail
RIPS.append(lambda l, it: l == 1 and it[1] == 'I2C_SCL' and it[0] == 'seg'
            and ((abs(it[2][0] - 67.875) < 0.01 and abs(it[2][1] - 5.125) < 0.01)
                 or (abs(it[2][0] - 69.375) < 0.01
                     and abs(it[2][1] - 1.375) < 0.01)))
# SDA via old
RIPS.append(lambda l, it: it[0] == 'via' and it[1] == 'I2C_SDA'
            and near(it, 69.320, 2.140, 0.01))
# GND EP feed segs
RIPS.append(lambda l, it: l == 0 and it[1] == 'GND' and it[0] == 'seg'
            and ((abs(it[2][0] - 68.25) < 0.01 and abs(it[2][1] - 3.5) < 0.01)
                 or (abs(it[2][2] - 68.25) < 0.01
                     and abs(it[2][3] - 3.5) < 0.01)))
# TMP_ALERT F segs from old pad
RIPS.append(lambda l, it: l == 0 and it[1] == 'TMP_ALERT' and it[0] == 'seg'
            and C(it)[0] > 66.6 and C(it)[1] > 2.8)
# U9 pads (all, F only in model)
U9PADS = []
for it in items_full[0]:
    if it[0] == 'pad' and 66.5 < it[2][0] < 70.0 and 1.5 < it[2][1] < 4.0 \
            and it[1] in ('I2C_SCL', 'GND', 'TMP_ALERT', '+3V3A', 'I2C_SDA'):
        U9PADS.append(it)
RIPS.append(lambda l, it: it in U9PADS)

pool = {l: [it for it in items_full[l]
            if not any(p(l, it) for p in RIPS)] for l in range(3)}
n_rip = sum(len(items_full[l]) - len(pool[l]) for l in range(3))
print(f'pocket rips: {n_rip} items (incl U9 pads '
      f'{len(U9PADS)})', flush=True)

# U9 pads shifted
for it in U9PADS:
    d = it[2]
    pool[0].append(('pad', it[1], (d[0] - 1.0, d[1], d[2], d[3], d[4]),
                    it[3]))

NEW = {0: [], 1: [], 2: []}


def seg(l, net, a, b, hw=0.10, clr=0.2):
    NEW[l].append(('seg', net, (a[0], a[1], b[0], b[1], hw), clr))


def via(net, x, y, r=0.25, clr=0.2):
    for l in range(3):
        NEW[l].append(('via', net, (x, y, r), clr))


# SCL via + SDA via
via('I2C_SCL', 69.35, 1.40)
via('I2C_SDA', 69.4, 2.2)
# SDA F stub: pad (68.225,2.1) -> via (69.4,2.2)
seg(0, 'I2C_SDA', (68.45, 2.1), (69.4, 2.2))
# SDA In2 hop: via (69.4,2.2) -> (70.2,2.5) -> anchor (71.125,1.875)
seg(1, 'I2C_SDA', (69.4, 2.2), (70.2, 2.5), hw=0.125)
seg(1, 'I2C_SDA', (70.2, 2.5), (71.125, 1.875), hw=0.125)
# SDA staircase restore (original exp240 geometry)
STAIR = [(69.9, 0.82), (70.125, 0.875), (70.375, 1.125), (70.625, 1.375),
         (70.875, 1.625), (71.125, 1.875)]
for a, b in zip(STAIR, STAIR[1:]):
    seg(1, 'I2C_SDA', a, b, hw=0.125)
# GND EP chain: (67.625,3.875) -> (67.45,3.55) EP top edge
seg(0, 'GND', (67.625, 3.875), (67.45, 3.55))
# TMP re-fan: pad (66.275,3.4) -> (66.5,3.05) -> anchor (66.625,2.875)
seg(0, 'TMP_ALERT', (66.5, 3.4), (66.55, 3.05))
seg(0, 'TMP_ALERT', (66.55, 3.05), (66.625, 2.875))

for l in range(3):
    pool[l] += NEW[l]

# gate hand items
union = {l: list(pool[l]) for l in range(3)}
clk_items = U.journey_items('scratch/work/au/journey_au9_CLK.json',
                            'CAP_CLK')
for l in range(3):
    union[l] += clk_items[l]
print('-- hand item gates:', flush=True)
for l in range(3):
    for it in NEW[l]:
        if it[0] == 'via':
            continue
        rest = [x for x in union[l] if x is not it]
        d = it[2]
        box = (min(d[0], d[2]) - 2.2, max(d[0], d[2]) + 2.2,
               min(d[1], d[3]) - 2.2, max(d[1], d[3]) + 2.2)
        local = L.in_box_pool({l: rest}, box, pad=0.6)
        m, w = L.seg_margin(l, (d[0], d[1]), (d[2], d[3]), it[1],
                            it[2][4], local[l])
        flag = '' if m >= 0 else '  << FAIL'
        print(f'   L{l} {L.fmt_it(it)}: {m:+.3f} vs {L.fmt_it(w)}{flag}',
              flush=True)
for net, x, y in [('I2C_SCL', 69.35, 1.40), ('I2C_SDA', 69.4, 2.2)]:
    for l in range(3):
        rest = [it for it in union[l]
                if not (it[0] == 'via' and it[1] == net
                        and abs(it[2][0] - x) < 0.01
                        and abs(it[2][1] - y) < 0.01)]
        box = (x - 2.2, x + 2.2, y - 2.2, y + 2.2)
        local = L.in_box_pool({l: rest}, box, pad=0.6)
        m, w = L.pt_margin(l, x, y, net, 0.25, local[l])
        flag = '' if m >= 0 else '  << FAIL'
        print(f'   via {net} ({x},{y}) L{l}: {m:+.3f} vs '
              f'{L.fmt_it(w)}{flag}', flush=True)

json.dump({'pool_note': 'model only'}, open('/dev/null', 'w'))
print('done part 1', flush=True)
