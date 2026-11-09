import sys, json
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])
for lay, nm in ((2, 'B'), (1, 'In2'), (0, 'F')):
    print(f'===== {nm} items x[73,77.2] y[11,16.5] =====', flush=True)
    rows = []
    for it in pool[lay]:
        kind, d = it[0], it[2]
        if kind == 'seg':
            if max(d[0], d[2]) >= 73 and min(d[0], d[2]) <= 77.2 and \
               max(d[1], d[3]) >= 11 and min(d[1], d[3]) <= 16.5:
                rows.append(f'seg {it[1]} ({d[0]},{d[1]})->({d[2]},{d[3]}) hw{d[4]}')
        elif kind == 'via':
            if 73 <= d[0] <= 77.2 and 11 <= d[1] <= 16.5:
                rows.append(f'via {it[1]} ({d[0]},{d[1]}) r{d[2]}')
        else:
            if 73 <= d[0] <= 77.2 and 11 <= d[1] <= 16.5:
                rows.append(f'pad {it[1]} ({d[0]},{d[1]})')
    for r in sorted(rows):
        print(' ', r, flush=True)
