"""t_ba20: identify the NW loopy-rail sighting: census of
long items in x[58,73] y[5,21] by net/layer -- total seg
length per net, longest single segs, and dense micro-seg
clusters (the 'shortcut wires' look)."""
import sys, math
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp252.kicad_pcb')
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
agg = {}
longs = []
for l in range(3):
    for it in pool[l]:
        if it[0] != 'seg':
            continue
        cc = C(it)
        if not (58 <= cc[0] <= 73 and 5 <= cc[1] <= 21):
            continue
        d = it[2]
        ln = math.hypot(d[2] - d[0], d[3] - d[1])
        k = (it[1], LAYN[l])
        a = agg.setdefault(k, [0, 0.0, 0])
        a[0] += 1
        a[1] += ln
        if ln < 0.35:
            a[2] += 1
        if ln > 2.2:
            longs.append((round(ln, 2), it[1], LAYN[l],
                          (round(d[0], 2), round(d[1], 2)),
                          (round(d[2], 2), round(d[3], 2))))
print('--- per net/layer: nsegs, total mm, microsegs(<0.35) ---')
for k in sorted(agg, key=lambda k: -agg[k][1]):
    v = agg[k]
    print(f'  {k[0]:12s} {k[1]:3s} n={v[0]:4d} len={v[1]:7.1f} micro={v[2]}')
print('--- longest segs (>2.2mm) ---')
for row in sorted(longs, reverse=True)[:20]:
    print('  ', row)
print('=== done ===')
