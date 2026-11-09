import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard(BOARD)
n = 0
for t in b.GetTracks():
    if type(t).__name__ != 'PCB_TRACK':
        continue
    s, e = t.GetStart(), t.GetEnd()
    pts = {(round(s.x / 1e6, 3), round(s.y / 1e6, 3)),
           (round(e.x / 1e6, 3), round(e.y / 1e6, 3))}
    if pts == {(70.825, 12.75), (71.075, 12.75)}:
        n += 1
        print(f'board track: {t.GetNetname()} layer {t.GetLayerName()} '
              f'w {t.GetWidth() / 1e6}', flush=True)
print(f'board tracks between the feed points: {n}', flush=True)
pool = load_board_pool()
from collections import Counter
c = Counter()
for l in range(3):
    for it in pool[l]:
        if it[0] == 'seg':
            d = it[2]
            key = (it[1], l, frozenset(((round(d[0], 3), round(d[1], 3)),
                                        (round(d[2], 3), round(d[3], 3)))))
            c[key] += 1
tw = {k: v for k, v in c.items() if v > 1}
print(f'doubled segs in pool: {len(tw)}', flush=True)
for k, v in list(tw.items())[:15]:
    print('  ', k, v, flush=True)
