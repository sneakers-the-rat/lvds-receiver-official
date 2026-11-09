import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])
D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})
astar = make_astar((71.0, 78.5, 10.0, 19.5), 0.05)
tests = [(((2,), 73.5, 16.0), (2, 76.8, 14.5), 'slot->vert B-lock'),
         (((0, 1, 2), 73.5, 16.0), (2, 76.8, 14.5), 'slot->vert any'),
         (((2,), 73.5, 16.0), (2, 74.5, 15.5), 'slot->(74.5,15.5)'),
         (((2,), 73.5, 16.0), (2, 75.5, 15.8), 'slot->(75.5,15.8)'),
         (((2,), 73.5, 16.0), (2, 76.0, 15.2), 'slot->(76,15.2)'),
         (((0,), 72.02, 18.0), (2, 73.5, 16.0), 'pad->slot 0.05')]
for st, gl, nm in tests:
    lock = [False, False, True] if 'B-lock' in nm else None
    J = astar('PHY_1V8', st, gl, hw=0.10, layer_lock=lock)
    print(nm, ':', 'FOUND' if J else 'NONE', flush=True)
    if J and 'slot->vert' in nm:
        json.dump(J, open('scratch/work/ay/bchan_journey.json', 'w'))
        print('   vias', J['vias'], 'runs',
              [(r['layer'], len(r['pts'])) for r in J['runs']], flush=True)
