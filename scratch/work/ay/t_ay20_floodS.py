import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])
D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})
astar = make_astar((75.0, 85.5, 4.0, 17.0), 0.1)
print('flood from model south via (77.98,10.02), all layers', flush=True)
for gy in (7.0, 9.0, 11.0, 13.0):
    row = []
    for gx in (79.0, 80.0, 81.0, 82.0, 83.0, 84.0):
        hit = ''
        for gl, tag in ((0, 'F'), (2, 'B'), (1, 'I')):
            J = astar('PHY_1V8', ((0, 1, 2), 77.98, 10.02), (gl, gx, gy),
                      hw=0.10)
            if J:
                hit = tag
                break
        row.append(f'{gx}:{hit or "-"}')
    print(f'  y={gy}: ' + '  '.join(row), flush=True)
