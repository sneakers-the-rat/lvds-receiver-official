# ---- ay tail: corridor fence dump + extended web search ----
print('--- corridor F items x[77.8,82.8] y[16.4,19.6] ---', flush=True)
for it in pool[0]:
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy = d[0], d[1]
        if 77.8 <= cx <= 82.8 and 16.4 <= cy <= 19.6:
            print('  F pad', it[1], (cx, cy), flush=True)
    elif kind == 'seg':
        if max(d[0], d[2]) >= 77.8 and min(d[0], d[2]) <= 82.8 and \
           max(d[1], d[3]) >= 16.4 and min(d[1], d[3]) <= 19.6:
            print('  F seg', it[1], (d[0], d[1], d[2], d[3], d[4]),
                  flush=True)
    else:
        if 77.8 <= d[0] <= 82.8 and 16.4 <= d[1] <= 19.6:
            print('  F via', it[1], (d[0], d[1], d[2]), flush=True)

GOALS = [(0, 'F'), (2, 'B'), (1, 'In2')]
results = []
astar = make_astar((76.0, 86.0, 13.0, 23.0), 0.05)
for (m, cx, cy, rot, m1, m2) in exact:
    p1 = (cx - 0.48, cy) if rot == 0 else (cx, cy - 0.48)
    for gl, glname in GOALS:
        J = astar('PHY_1V8', ((0,), p1[0], p1[1]), (gl, 78.1, 17.5),
                  hw=0.10)
        if J:
            nv = len(J['vias'])
            length = 0.0
            for r in J['runs']:
                pp = r['pts']
                for a, b2 in zip(pp, pp[1:]):
                    length += math.hypot(a[0]-b2[0], a[1]-b2[1])
            print(f'  WEB OK centre ({cx},{cy}) rot {rot} goal {glname}: '
                  f'vias {nv} len {length:.2f} margin {m:+.3f}', flush=True)
            results.append((GOALS.index((gl, glname)), nv, length,
                            -m, cx, cy, rot, J))
            break
results.sort()
winner = None
if results:
    g0, nv, length, negm, cx, cy, rot, J = results[0]
    winner = (cx, cy, rot, J)
    print('WINNER:', winner[:3], 'goal', GOALS[g0][1], 'vias', nv,
          flush=True)
else:
    print('NO WEB FROM ANY EXACT SITE; trying staged site (79.6,18.6)',
          flush=True)
    m1, w1 = pad_margin_exact(79.12, 18.6, 'PHY_1V8')
    m2, w2 = pad_margin_exact(80.08, 18.6, 'GND')
    print(f'  staged pads exact: PHY {m1:+.3f} vs {w1}, GND {m2:+.3f} '
          f'vs {w2}', flush=True)
    for gl, glname in GOALS:
        J = astar('PHY_1V8', ((0,), 79.12, 18.6), (gl, 78.1, 17.5),
                  hw=0.10)
        print(f'  staged web goal {glname}:', 'FOUND' if J else 'NONE',
              flush=True)
        if J:
            winner = (79.6, 18.6, 0, J)
            print('WINNER (staged):', winner[:3], flush=True)
            break
out = {}
if winner:
    out['c22_site'] = winner[:3]
    out['c22_web'] = winner[3]
json.dump(out, open('scratch/work/ax/design251fix.json', 'w'))
print('AY SCAN2 DONE, fix written:', bool(out), flush=True)
