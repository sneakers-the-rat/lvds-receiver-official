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
# move GND stitch via (77.25,18.38) -> (77.25,18.03), all layers
gv = [it for lay in (0, 1, 2) for it in pool[lay]
      if it[0] == 'via' and it[1] == 'GND'
      and abs(it[2][0] - 77.25) < 0.01 and abs(it[2][1] - 18.38) < 0.01]
print('GND via items moved:', len(gv), flush=True)
rip_items(gv)
add_items({lay: [('via', 'GND', (77.25, 18.03, 0.3), 0.2)]
           for lay in (0, 1, 2)})
# rip SQUELCH F chain
chain = [((75.375, 19.625), (75.625, 19.375)),
         ((75.625, 19.375), (77.875, 19.375)),
         ((77.875, 19.375), (78.125, 19.125)),
         ((78.125, 19.125), (78.375, 18.875)),
         ((78.375, 18.875), (78.625, 18.625)),
         ((78.625, 18.625), (78.875, 18.375)),
         ((78.875, 18.375), (79.125, 18.125)),
         ((79.125, 18.125), (79.375, 17.875)),
         ((79.375, 17.875), (79.625, 17.625)),
         ((79.625, 17.625), (79.875, 17.375)),
         ((79.875, 17.375), (80.125, 17.125)),
         ((80.125, 17.125), (80.375, 16.875)),
         ((80.375, 16.875), (80.625, 16.625)),
         ((80.625, 16.625), (80.875, 16.375))]
def segmatch(it, net, a, b):
    if it[0] != 'seg' or it[1] != net:
        return False
    d = it[2]
    return ((abs(d[0]-a[0]) < 0.01 and abs(d[1]-a[1]) < 0.01 and
             abs(d[2]-b[0]) < 0.01 and abs(d[3]-b[1]) < 0.01) or
            (abs(d[2]-a[0]) < 0.01 and abs(d[3]-a[1]) < 0.01 and
             abs(d[0]-b[0]) < 0.01 and abs(d[1]-b[1]) < 0.01))
victims = []
for a, b in chain:
    v = [it for it in pool[0] if segmatch(it, 'CDR_SQUELCH', a, b)]
    assert len(v) == 1, (a, b, len(v))
    victims += v
rip_items(victims)
print('SQUELCH chain ripped:', len(victims), flush=True)
astar = make_astar((74.0, 82.5, 14.0, 21.5), 0.05)
J = astar('CDR_SQUELCH', ((1,), 75.375, 19.625), (1, 80.875, 16.375),
          hw=0.125, layer_lock=[False, True, False])
print('SQUELCH In2 ride (GND via moved):', 'FOUND' if J else 'NONE',
      flush=True)
if not J:
    J = astar('CDR_SQUELCH', ((0,), 75.375, 19.625), (0, 80.875, 16.375),
              hw=0.125)
    print('SQUELCH free-layer ride:', 'FOUND' if J else 'NONE', flush=True)
if J:
    print('  vias:', J['vias'], 'runs:',
          [(r['layer'], len(r['pts'])) for r in J['runs']], flush=True)
    json.dump(J, open('scratch/work/ay/sq_ride_ay29.json', 'w'))
    add_items(journey_items_dense(J, 'CDR_SQUELCH', hw=0.125))
    print('SQUELCH fragments (ride added, no dive/rise vias yet):',
          len(fragments('CDR_SQUELCH', (-50.0, 200.0, -100.0, 100.0))),
          flush=True)
    # now C22 webs on F from the top east sites
    astar2 = make_astar((76.0, 86.0, 13.0, 23.0), 0.05)
    for pad, site in (((82.5, 17.32), (82.5, 17.8, 90)),
                      ((82.4, 17.22), (82.4, 17.7, 90)),
                      ((82.02, 17.5), (82.5, 17.5, 0))):
        J2 = astar2('PHY_1V8', ((0,), pad[0], pad[1]), (0, 78.1, 17.5),
                    hw=0.10)
        print(f'C22 web F site {site}:', 'FOUND' if J2 else 'NONE',
              flush=True)
        if J2:
            out = {'c22_site': list(site), 'c22_web': J2}
            json.dump(out, open('scratch/work/ax/design251fix.json', 'w'))
            print('FIX WRITTEN', flush=True)
            break
