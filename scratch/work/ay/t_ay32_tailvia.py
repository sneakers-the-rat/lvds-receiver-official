import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
H = {'__name__': 'ax252head'}
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0], H)
pool = H['pool']
make_astar = H['make_astar']
fragments = H['fragments']
D = json.load(open('scratch/work/ax/design214_ax252.json'))
add_items = H['add_items']
journey_items_dense = H['journey_items_dense']
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})
print('PHY fragments in v2 model:',
      len(fragments('PHY_1V8', (-50.0, 200.0, -100.0, 100.0))), flush=True)
astar = make_astar((68.0, 80.0, 6.0, 21.0), 0.05)
GOALS = [(0, 78.1, 17.5, 'via78F'), (2, 78.1, 17.5, 'via78B'),
         (1, 78.1, 17.5, 'via78In2'), (2, 76.95, 14.5, 'Bvert'),
         (2, 77.98, 10.02, 'SviaB'), (0, 77.25, 16.4375, 'U715')]
for gl, gx, gy, gn in GOALS:
    J = astar('PHY_1V8', ((0, 1, 2), 71.375, 17.625), (gl, gx, gy),
              hw=0.10)
    print(f'tail-via -> {gn}:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        print('   vias:', J['vias'], 'runs:',
              [(r['layer'], len(r['pts'])) for r in J['runs']], flush=True)
        json.dump(J, open('scratch/work/ay/tail_feed_ay32.json', 'w'))
        break
