"""t_au3: exact gates for the candidate pair (CLK=au2 B-ride journey,
DATA=journey30) in the PG-corridor-ablated model; PG conflict census;
PG full topology dump.
Checks: each journey's segs (seg_margin) and vias (pt_margin r0.25)
against pool-minus-PG-corridor PLUS the sibling journey's items."""
import sys, math, json
import numpy as np
sys.path.insert(0, 'scratch/work/au')
import t_au1_lib as U
import t_ai_lib as L
from router import dist_to_item

PG_PRED = lambda l, it: l == 2 and it[1] == 'PG_3V3' \
    and 60 < U.item_centre(it)[0] < 70 and 0 < U.item_centre(it)[1] < 16

pool_full = U.load_pool()
removed = {l: [it for it in pool_full[l] if PG_PRED(l, it)]
           for l in range(3)}
pool = {l: [it for it in pool_full[l] if not PG_PRED(l, it)]
        for l in range(3)}
print(f'PG corridor items removed: '
      f'{sum(len(removed[l]) for l in range(3))} '
      f'(kinds: {sorted(set(it[0] for l in range(3) for it in removed[l]))})',
      flush=True)

CLK = U.journey_items('scratch/work/au/journey_au2_CAP_CLK_B_PG.json',
                      'CAP_CLK')
DATA = U.journey_items('scratch/work/as/journey30_CAP_DATA_DC.json',
                       'CAP_DATA')


def check_journey(J, net, extra):
    union = {l: pool[l] + extra[l] for l in range(3)}
    worst_seg = (9.9, None, None)
    worst_via = (9.9, None, None)
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
                if m < worst_seg[0]:
                    worst_seg = (m, it, w)
                if m < 0.05:
                    low.append(('seg', l, m, it, w))
            elif it[0] == 'via':
                d = it[2]
                box = (d[0] - 2.2, d[0] + 2.2, d[1] - 2.2, d[1] + 2.2)
                local = L.in_box_pool(union, box, pad=0.6)
                m, w = L.pt_margin(l, d[0], d[1], net, 0.25, local[l])
                if m < worst_via[0]:
                    worst_via = (m, it, w)
                if m < 0.05:
                    low.append(('via', l, m, it, w))
    print(f'== {net}: worst seg margin {worst_seg[0]:+.3f} '
          f'({L.fmt_it(worst_seg[1])} vs {L.fmt_it(worst_seg[2])})',
          flush=True)
    print(f'   worst via margin {worst_via[0]:+.3f} '
          f'({L.fmt_it(worst_via[1])} vs {L.fmt_it(worst_via[2])})',
          flush=True)
    for (k, l, m, it, w) in sorted(low, key=lambda t: t[2]):
        print(f'   LOW {k} L{l} {m:+.3f}: {L.fmt_it(it)} vs {L.fmt_it(w)}',
              flush=True)
    return worst_seg[0], worst_via[0]


check_journey(CLK, 'CAP_CLK', DATA)
check_journey(DATA, 'CAP_DATA', CLK)

# ---- PG conflict census: removed PG items vs pair B copper + arrivals
pairB = CLK[2] + DATA[2]
print('-- PG removed items vs pair B-layer copper (margin = edge dist '
      '- 0.2 clr):', flush=True)
conflicts = []
for it in removed[2]:
    if it[0] == 'seg':
        d = it[2]
        n = max(2, int(math.hypot(d[2] - d[0], d[3] - d[1]) / 0.05))
        m = 9.9
        for k in range(n + 1):
            x = d[0] + (d[2] - d[0]) * k / n
            y = d[1] + (d[3] - d[1]) * k / n
            for jt in pairB:
                dd = dist_to_item(jt, x, y) - d[4] - 0.2
                if dd < m:
                    m = dd
        conflicts.append((m, it))
    elif it[0] == 'via':
        d = it[2]
        m = 9.9
        for jt in pairB:
            dd = dist_to_item(jt, d[0], d[1]) - d[2] - 0.2
            if dd < m:
                m = dd
        conflicts.append((m, it))
for (m, it) in sorted(conflicts, key=lambda t: t[0]):
    if m < 0.10:
        print(f'   CONFLICT {m:+.3f}: {L.fmt_it(it)}', flush=True)
print(f'   ({sum(1 for m, _ in conflicts if m < 0.0)} items with '
      f'margin < 0; {sum(1 for m, _ in conflicts if m < 0.10)} < +0.10 '
      f'of {len(conflicts)})', flush=True)

# ---- PG full topology (all layers, from the full pool)
print('-- PG_3V3 all items in exp241esc pool:', flush=True)
for l in range(3):
    its = [it for it in pool_full[l] if it[1] == 'PG_3V3']
    print(f'   L{l}: {len(its)} items', flush=True)
    for it in sorted(its, key=lambda t: (U.item_centre(t)[1],
                                         U.item_centre(t)[0])):
        print(f'      {L.fmt_it(it)} clr{it[3]}', flush=True)
print('done', flush=True)
