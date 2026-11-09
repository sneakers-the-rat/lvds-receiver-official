import sys, json
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])
for lay, nm in ((1, 'In2'), (2, 'B')):
    print(f'===== {nm} items x[74.5,81.5] y[15.8,20.2] =====', flush=True)
    rows = []
    for it in pool[lay]:
        kind, d = it[0], it[2]
        if kind == 'seg':
            if max(d[0], d[2]) >= 74.5 and min(d[0], d[2]) <= 81.5 and \
               max(d[1], d[3]) >= 15.8 and min(d[1], d[3]) <= 20.2:
                rows.append(f'seg {it[1]} ({d[0]},{d[1]})->({d[2]},{d[3]}) hw{d[4]}')
        elif kind == 'via':
            if 74.5 <= d[0] <= 81.5 and 15.8 <= d[1] <= 20.2:
                rows.append(f'via {it[1]} ({d[0]},{d[1]}) r{d[2]}')
        else:
            if 74.5 <= d[0] <= 81.5 and 15.8 <= d[1] <= 20.2:
                rows.append(f'pad {it[1]} ({d[0]},{d[1]})')
    for r in sorted(rows):
        print(' ', r, flush=True)
