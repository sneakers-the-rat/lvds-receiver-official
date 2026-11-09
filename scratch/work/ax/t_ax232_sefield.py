import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
# coarse density grid for +3V3A on B, x 73..79 step 0.5, y -1..7 step 0.5
pts = []
for it in pool[2]:
    if it[1] != '+3V3A':
        continue
    d = it[2]
    if it[0] == 'seg':
        n = max(2, int(max(abs(d[2] - d[0]), abs(d[3] - d[1])) / 0.25) + 1)
        for i in range(n + 1):
            pts.append((d[0] + (d[2] - d[0]) * i / n,
                        d[1] + (d[3] - d[1]) * i / n))
    else:
        pts.append((d[0], d[1]))
print('   ' + ''.join(f'{73 + i * 0.5:.0f}'[-1] for i in range(13)), flush=True)
for j in range(16, -1, -1):
    y = -1 + j * 0.5
    row = ''
    for i in range(13):
        x = 73 + i * 0.5
        row += '#' if any(abs(px - x) < 0.3 and abs(py - y) < 0.3
                          for px, py in pts) else '.'
    print(f'{y:5.1f} {row}', flush=True)
from collections import Counter
for l, nm in ((0, 'F'), (1, 'In2')):
    cnt = Counter(it[1] for it in pool[l]
                  if (it[0] == 'seg' and max(it[2][0], it[2][2]) > 73
                      and min(it[2][0], it[2][2]) < 78.5
                      and max(it[2][1], it[2][3]) > -1
                      and min(it[2][1], it[2][3]) < 7)
                  or (it[0] == 'via' and 73 < it[2][0] < 78.5
                      and -1 < it[2][1] < 7))
    print(nm, dict(cnt), flush=True)
