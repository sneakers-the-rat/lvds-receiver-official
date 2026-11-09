"""t_au16: pocket rebuild v2.
Extra rips vs t_au15: TMP_ALERT chain segs down to (66.125,-3.125);
+3V3A stub (69.225,2.75)->(69.475,2.75).
TMP re-lay west/south at x65.7. SDA via candidates gated vs CLK B
ride + SCL via + own stub/hop; best candidate wins.
Then SCL chord A* (In2, slot wall sum>=70.0 fenced) and DATA entry
fine A* in the rebuilt model."""
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
RIPS.append(lambda l, it: it[0] == 'via' and it[1] == 'I2C_SCL'
            and near(it, 69.375, 1.375))
RIPS.append(lambda l, it: l == 0 and it[1] == 'I2C_SCL' and it[0] == 'seg'
            and 66.8 < C(it)[0] < 69.6 and 1.0 < C(it)[1] < 2.2)
RIPS.append(lambda l, it: l == 1 and it[1] == 'I2C_SCL' and it[0] == 'seg'
            and ((abs(it[2][0] - 67.875) < 0.01 and abs(it[2][1] - 5.125) < 0.01)
                 or (abs(it[2][0] - 69.375) < 0.01
                     and abs(it[2][1] - 1.375) < 0.01)))
RIPS.append(lambda l, it: it[0] == 'via' and it[1] == 'I2C_SDA'
            and near(it, 69.320, 2.140))
RIPS.append(lambda l, it: l == 0 and it[1] == 'GND' and it[0] == 'seg'
            and ((abs(it[2][0] - 68.25) < 0.01 and abs(it[2][1] - 3.5) < 0.01)
                 or (abs(it[2][2] - 68.25) < 0.01
                     and abs(it[2][3] - 3.5) < 0.01)))
RIPS.append(lambda l, it: l == 0 and it[1] == 'TMP_ALERT' and it[0] == 'seg'
            and C(it)[0] < 67.3 and C(it)[1] > -3.2)
RIPS.append(lambda l, it: l == 0 and it[1] == '+3V3A' and it[0] == 'seg'
            and abs(it[2][0] - 69.225) < 0.01 and abs(it[2][1] - 2.75) < 0.01
            and abs(it[2][2] - 69.475) < 0.01 and abs(it[2][3] - 2.75) < 0.01)
U9PADS = []
for it in items_full[0]:
    if it[0] == 'pad' and 66.5 < it[2][0] < 70.0 and 1.5 < it[2][1] < 4.0 \
            and it[1] in ('I2C_SCL', 'GND', 'TMP_ALERT', '+3V3A', 'I2C_SDA'):
        U9PADS.append(it)
RIPS.append(lambda l, it: it in U9PADS)

pool = {l: [it for it in items_full[l]
            if not any(p(l, it) for p in RIPS)] for l in range(3)}
print(f'rips: {sum(len(items_full[l]) - len(pool[l]) for l in range(3))}',
      flush=True)
for it in U9PADS:
    d = it[2]
    pool[0].append(('pad', it[1], (d[0] - 1.0, d[1], d[2], d[3], d[4]),
                    it[3]))

clk_items = U.journey_items('scratch/work/au/journey_au9_CLK.json',
                            'CAP_CLK')

NEW = {0: [], 1: [], 2: []}


def seg(l, net, a, b, hw=0.10, clr=0.2, store=None):
    (NEW if store is None else store)[l].append(
        ('seg', net, (a[0], a[1], b[0], b[1], hw), clr))


def via(store, net, x, y, r=0.25, clr=0.2):
    for l in range(3):
        store[l].append(('via', net, (x, y, r), clr))


via(NEW, 'I2C_SCL', 69.35, 1.40)
# GND EP chain
seg(0, 'GND', (67.625, 3.875), (67.45, 3.55))
# TMP re-lay west/south
TMP = [(66.275, 3.4), (65.95, 3.35), (65.7, 3.15), (65.7, 2.2),
       (65.7, -2.6), (66.125, -3.125)]
for a, b in zip(TMP, TMP[1:]):
    seg(0, 'TMP_ALERT', a, b, hw=0.125 if b[1] < 0 else 0.10)
# SDA staircase restore
STAIR = [(69.9, 0.82), (70.125, 0.875), (70.375, 1.125), (70.625, 1.375),
         (70.875, 1.625), (71.125, 1.875)]
for a, b in zip(STAIR, STAIR[1:]):
    seg(1, 'I2C_SDA', a, b, hw=0.125)

for l in range(3):
    pool[l] += NEW[l]
union = {l: pool[l] + clk_items[l] for l in range(3)}


def gate_seg(l, it, extra_pool=None):
    upl = union if extra_pool is None else extra_pool
    rest = [x for x in upl[l] if x is not it]
    d = it[2]
    box = (min(d[0], d[2]) - 2.2, max(d[0], d[2]) + 2.2,
           min(d[1], d[3]) - 2.2, max(d[1], d[3]) + 2.2)
    px = {0: [], 1: [], 2: []}
    px[l] = rest
    local = L.in_box_pool(px, box, pad=0.6)
    return L.seg_margin(l, (d[0], d[1]), (d[2], d[3]), it[1], d[4],
                        local[l])


def gate_via(net, x, y, r, extra_items):
    worst = (9.9, None, None)
    for l in range(3):
        rest = [it for it in union[l] + extra_items[l]
                if not (it[0] == 'via' and it[1] == net
                        and abs(it[2][0] - x) < 0.01
                        and abs(it[2][1] - y) < 0.01)]
        px = {0: [], 1: [], 2: []}
        px[l] = rest
        box = (x - 2.2, x + 2.2, y - 2.2, y + 2.2)
        local = L.in_box_pool(px, box, pad=0.6)
        m, w = L.pt_margin(l, x, y, net, r, local[l])
        if m < worst[0]:
            worst = (m, l, w)
    return worst


print('-- fixed hand items:', flush=True)
for l in range(3):
    for it in NEW[l]:
        if it[0] == 'seg':
            m, w = gate_seg(l, it)
            print(f'   L{l} {L.fmt_it(it)}: {m:+.3f} vs {L.fmt_it(w)}'
                  f'{"  << FAIL" if m < 0 else ""}', flush=True)
m = gate_via('I2C_SCL', 69.35, 1.40, 0.25, NEW)
print(f'   via SCL (69.35,1.40): {m[0]:+.3f} L{m[1]} vs {L.fmt_it(m[2])}',
      flush=True)

print('-- SDA via candidates:', flush=True)
best = None
for (vx, vy) in [(69.4, 2.2), (69.2, 2.2), (69.3, 2.35), (69.15, 2.3),
                 (69.3, 2.1), (69.25, 2.45)]:
    cand = {0: [], 1: [], 2: []}
    via(cand, 'I2C_SDA', vx, vy)
    seg(0, 'I2C_SDA', (68.45, 2.1), (vx, vy), store=cand)
    seg(1, 'I2C_SDA', (vx, vy), (70.35, 2.6), hw=0.125, store=cand)
    seg(1, 'I2C_SDA', (70.35, 2.6), (71.125, 1.875), hw=0.125, store=cand)
    upl = {l: union[l] + cand[l] for l in range(3)}
    wv = gate_via('I2C_SDA', vx, vy, 0.25, cand)
    ws = (9.9, None)
    for l in range(3):
        for it in cand[l]:
            if it[0] == 'seg':
                mm, ww = gate_seg(l, it, extra_pool=upl)
                if mm < ws[0]:
                    ws = (mm, ww)
    score = min(wv[0], ws[0])
    print(f'   ({vx},{vy}): via {wv[0]:+.3f} (vs {L.fmt_it(wv[2])}), '
          f'segs {ws[0]:+.3f} (vs {L.fmt_it(ws[1])}) -> {score:+.3f}',
          flush=True)
    if best is None or score > best[0]:
        best = (score, vx, vy, cand)
print(f'BEST SDA via: ({best[1]},{best[2]}) score {best[0]:+.3f}',
      flush=True)
SDA_CAND = best[3]
for l in range(3):
    pool[l] += SDA_CAND[l]
    union[l] += SDA_CAND[l]
json.dump({'sda_via': [best[1], best[2]]},
          open('scratch/work/au/pocket_au16.json', 'w'))
print('done', flush=True)
