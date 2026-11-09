import sys, json
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])
D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})
staged = [it for it in pool[0] if it[0] == 'pad'
          and abs(it[2][1] - 18.6) < 0.01 and it[2][0] in (79.12, 80.08)]
rip_items(staged)
add_items({0: [('pad', 'PHY_1V8', (72.02, 18.0, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (72.98, 18.0, 0.280, 0.310, 0.0), 0.2)]})
add_items({l: [('via', 'GND', (73.434, 17.685, 0.25), 0.2)]
           for l in range(3)})
LN = {0: 'F', 1: 'In2', 2: 'B'}
for lay in range(3):
    print(f'===== LAYER {LN[lay]} items in x[69.5,79] y[13.5,20.5] =====',
          flush=True)
    rows = []
    for it in pool[lay]:
        kind, d = it[0], it[2]
        if kind == 'pad':
            if 69.5 <= d[0] <= 79 and 13.5 <= d[1] <= 20.5:
                rows.append(f'pad {it[1]} ({d[0]},{d[1]}) hw{d[2]} hh{d[3]}')
        elif kind == 'seg':
            if max(d[0], d[2]) >= 69.5 and min(d[0], d[2]) <= 79 and \
               max(d[1], d[3]) >= 13.5 and min(d[1], d[3]) <= 20.5:
                rows.append(f'seg {it[1]} ({d[0]},{d[1]})->({d[2]},{d[3]}) hw{d[4]}')
        else:
            if 69.5 <= d[0] <= 79 and 13.5 <= d[1] <= 20.5:
                rows.append(f'via {it[1]} ({d[0]},{d[1]}) r{d[2]}')
    for r in sorted(rows):
        print(' ', r, flush=True)
