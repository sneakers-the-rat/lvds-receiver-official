"""t_au6: pair exact check against the FULL exp241esc pool (NO band /
XO / +3V3D ablations) minus PG corridor items only. This is the true
build fence set. Any negative names a fence the landing pass must
re-lay (band knob / XO web / +3V3D web)."""
import sys, math, json
import numpy as np
sys.path.insert(0, 'scratch/work/au')
import t_au1_lib as U
import t_ai_lib as L

PG_PRED = lambda l, it: l == 2 and it[1] == 'PG_3V3' \
    and 60 < U.item_centre(it)[0] < 70 and 0 < U.item_centre(it)[1] < 16

# full items, no ABL_PREDS: load raw then apply only PG ablation
import pcbnew
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items_full = L.load_items(board)
pool = {l: [it for it in items_full[l] if not PG_PRED(l, it)]
        for l in range(3)}


def journey_items_dense(jfile, net):
    J = json.load(open(jfile))
    out = {0: [], 1: [], 2: []}
    for run in J['runs']:
        l = run['layer']
        pts = [tuple(p) for p in run['pts']]
        keep = [pts[0]]
        for a, b, c in zip(pts, pts[1:], pts[2:]):
            v1 = (round(b[0] - a[0], 6), round(b[1] - a[1], 6))
            v2 = (round(c[0] - b[0], 6), round(c[1] - b[1], 6))
            if v1 != v2:
                keep.append(b)
        keep.append(pts[-1])
        for a, b in zip(keep, keep[1:]):
            out[l].append(('seg', net, (a[0], a[1], b[0], b[1], 0.10), 0.2))
    for (vx, vy) in J['vias']:
        for l in range(3):
            out[l].append(('via', net, (vx, vy, 0.25), 0.2))
    return out


CLK = journey_items_dense('scratch/work/au/journey_au2_CAP_CLK_B_PG.json',
                          'CAP_CLK')
DATA = journey_items_dense('scratch/work/as/journey30_CAP_DATA_DC.json',
                           'CAP_DATA')


def check_journey(J, net, extra):
    union = {l: pool[l] + extra[l] for l in range(3)}
    worst = (9.9, None, None)
    low = []
    for l in range(3):
        for it in J[l]:
            if it[0] == 'seg':
                d = it[2]
                box = (min(d[0], d[2]) - 2.2, max(d[0], d[2]) + 2.2,
                       min(d[1], d[3]) - 2.2, max(d[1], d[3]) + 2.2)
                local = L.in_box_pool(union, box, pad=0.6)
                m, w = L.seg_margin(l, (d[0], d[1]), (d[2], d[3]),
                                    net, 0.10, local[l])
                kind = 'seg'
            else:
                d = it[2]
                box = (d[0] - 2.2, d[0] + 2.2, d[1] - 2.2, d[1] + 2.2)
                local = L.in_box_pool(union, box, pad=0.6)
                m, w = L.pt_margin(l, d[0], d[1], net, 0.25, local[l])
                kind = 'via'
            if m < worst[0]:
                worst = (m, it, w)
            if m < 0.05:
                low.append((kind, l, m, it, w))
    print(f'== {net}: worst {worst[0]:+.3f} '
          f'({L.fmt_it(worst[1])} vs {L.fmt_it(worst[2])})', flush=True)
    for (k, l, m, it, w) in sorted(low, key=lambda t: t[2]):
        print(f'   LOW {k} L{l} {m:+.3f}: {L.fmt_it(it)} vs {L.fmt_it(w)}',
              flush=True)


check_journey(CLK, 'CAP_CLK', DATA)
check_journey(DATA, 'CAP_DATA', CLK)
print('done', flush=True)
