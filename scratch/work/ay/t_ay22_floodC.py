import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])
D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})
astar = make_astar((69.0, 79.5, 5.0, 21.0), 0.1)
print('flood from C22 PHY pad (72.02,18.0), start F only', flush=True)
for gy in (16.0, 14.0, 12.0, 10.0, 8.0):
    row = []
    for gx in (72.0, 73.5, 75.0, 76.5, 78.0):
        hit = ''
        for gl, tag in ((0, 'F'), (2, 'B'), (1, 'I')):
            J = astar('PHY_1V8', ((0,), 72.02, 18.0), (gl, gx, gy),
                      hw=0.10)
            if J:
                hit = tag
                break
        row.append(f'{gx}:{hit or "-"}')
    print(f'  y={gy}: ' + '  '.join(row), flush=True)
for gl, gx, gy, nm in ((2, 76.95, 14.5, 'Bvert14.5'), (2, 76.95, 12.0, 'Bvert12'),
                      (2, 77.98, 10.02, 'SviaB'), (0, 78.1, 17.5, 'via78F')):
    J = astar('PHY_1V8', ((0,), 72.02, 18.0), (gl, gx, gy), hw=0.10)
    print(f'  goal {nm}:', 'FOUND' if J else 'NONE', flush=True)
