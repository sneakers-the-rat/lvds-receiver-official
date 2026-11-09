import sys, json, math
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
astar = make_astar((68.0, 80.0, 4.0, 21.0), 0.05)
probes = [
    (2, 72.02, 18.0, 'dive at pad -> B'), (1, 72.02, 18.0, 'dive at pad -> In2'),
    (0, 73.0, 18.0, 'F east 1mm'), (0, 74.0, 18.0, 'F east 2mm'),
    (0, 75.0, 18.0, 'F east 3mm'), (0, 71.0, 18.0, 'F west 1mm'),
    (0, 72.02, 19.0, 'F north 1mm'), (0, 72.02, 17.0, 'F south 1mm'),
    (0, 72.02, 15.0, 'F south 3mm'), (0, 72.02, 12.0, 'F south 6mm'),
    (2, 74.0, 12.0, 'B (74,12)'), (2, 77.0, 12.0, 'B (77,12)'),
    (1, 74.0, 12.0, 'In2 (74,12)'), (1, 77.0, 12.0, 'In2 (77,12)'),
    (2, 76.0, 17.0, 'B (76,17)'), (1, 76.0, 17.0, 'In2 (76,17)'),
    (0, 76.0, 18.6, 'F (76,18.6) X1 area'), (0, 74.0, 19.5, 'F (74,19.5)'),
    (2, 72.02, 12.0, 'B south slot'), (1, 72.02, 12.0, 'In2 south slot'),
]
for gl, gx, gy, name in probes:
    J = astar('PHY_1V8', ((0,), 72.02, 18.0), (gl, gx, gy), hw=0.10)
    print(f'probe {name}:', 'FOUND' if J else 'NONE', flush=True)
