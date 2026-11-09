import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
H = {'__name__': 'ax252head'}
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0], H)
pool = H['pool']
rip_items, add_items = H['rip_items'], H['add_items']
fragments = H['fragments']
journey_items_dense = H['journey_items_dense']
make_astar = H['make_astar']
D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})
# rip +3V3D B staircase (78.375,20.125) -> (81.125,15.625), hw0.3 segs
stair = [it for it in pool[2] if it[0] == 'seg' and it[1] == '+3V3D'
         and abs(it[2][4] - 0.3) < 1e-9
         and min(it[2][0], it[2][2]) >= 78.3 and max(it[2][0], it[2][2]) <= 81.2
         and min(it[2][1], it[2][3]) >= 15.5 and max(it[2][1], it[2][3]) <= 20.2]
print('staircase segs found:', len(stair), flush=True)
for it in stair:
    print('   ', it[2], flush=True)
rip_items(stair)
print('+3V3D fragments after rip:',
      len(fragments('+3V3D', (-50.0, 200.0, -100.0, 100.0))), flush=True)
astar = make_astar((76.0, 83.0, 13.0, 22.0), 0.05)
J = astar('+3V3D', ((1,), 78.375, 20.125), (1, 81.125, 15.625), hw=0.30,
          layer_lock=[False, True, False])
print('+3V3D staircase In2 ride:', 'FOUND' if J else 'NONE', flush=True)
if J:
    print('  vias:', J['vias'], 'runs:',
          [(r['layer'], len(r['pts'])) for r in J['runs']], flush=True)
    json.dump(J, open('scratch/work/ay/stair_in2_ay31.json', 'w'))
    add_items(journey_items_dense(J, '+3V3D', hw=0.30))
    print('+3V3D fragments after In2 ride:',
          len(fragments('+3V3D', (-50.0, 200.0, -100.0, 100.0))),
          flush=True)
    astar2 = make_astar((76.0, 86.0, 13.0, 23.0), 0.05)
    for pad, site in (((82.5, 17.32), (82.5, 17.8, 90)),
                      ((82.4, 17.22), (82.4, 17.7, 90)),
                      ((82.02, 17.5), (82.5, 17.5, 0))):
        J2 = astar2('PHY_1V8', ((0,), pad[0], pad[1]), (2, 78.1, 17.5),
                    hw=0.10)
        print(f'C22 web -> via B site {site}:',
              'FOUND' if J2 else 'NONE', flush=True)
        if J2:
            print('   vias:', J2['vias'], 'runs:',
                  [(r['layer'], len(r['pts'])) for r in J2['runs']],
                  flush=True)
            out = {'c22_site': list(site), 'c22_web': J2}
            json.dump(out, open('scratch/work/ax/design251fix.json', 'w'))
            print('FIX WRITTEN', flush=True)
            break
