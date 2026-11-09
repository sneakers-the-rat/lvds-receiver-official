import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])
D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})
# NOTE: model south via is at (77.98,10.02) per ax252 head re-lay;
# builder emits (77.90,10.08). Goals cover both neighbourhoods.
astar = make_astar((74.0, 86.0, 8.0, 23.0), 0.05)
SITES = [((82.5, 17.32), (82.5, 17.8, 90)), ((82.4, 17.22), (82.4, 17.7, 90)),
         ((82.02, 17.5), (82.5, 17.5, 0)), ((82.5, 16.82), (82.5, 17.3, 90))]
GOALS = [(2, 76.95, 14.5, 'B vert 14.5'), (2, 76.95, 13.0, 'B vert 13'),
         (2, 76.95, 12.0, 'B vert 12'), (2, 77.8, 16.2, 'B corner'),
         (2, 77.45, 10.1, 'B via seg'), (0, 77.9, 10.08, 'S via F'),
         (2, 77.9, 10.08, 'S via B')]
found = {}
for pad, site in SITES:
    for gl, gx, gy, gn in GOALS:
        J = astar('PHY_1V8', ((0,), pad[0], pad[1]), (gl, gx, gy), hw=0.10)
        print(f'site {site} goal {gn}:', 'FOUND' if J else 'NONE',
              flush=True)
        if J and site not in found:
            found[site] = (gn, J)
for site, (gn, J) in found.items():
    print('FIRST HIT for site', site, 'goal', gn, 'vias', J['vias'],
          'runs', [(r['layer'], len(r['pts'])) for r in J['runs']],
          flush=True)
if found:
    site = next(iter(found))
    gn, J = found[site]
    out = {'c22_site': list(site), 'c22_web': J}
    json.dump(out, open('scratch/work/ax/design251fix.json', 'w'))
    print('FIX WRITTEN from site', site, 'goal', gn, flush=True)
