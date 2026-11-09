import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])
D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})
# rip SQUELCH F chain (75.375,19.625) -> (80.875,16.375)
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
    print(f'SQ rip {a}->{b}: {len(v)}', flush=True)
    assert len(v) == 1, (a, b, len(v))
    victims += v
rip_items(victims)
print('SQUELCH F chain ripped:', len(victims), flush=True)
print('SQUELCH fragments now:', len(fragments('CDR_SQUELCH',
      (-50.0, 200.0, -100.0, 100.0))), flush=True)
astar = make_astar((74.0, 82.0, 15.0, 21.0), 0.05)
J = astar('CDR_SQUELCH', ((1,), 75.375, 19.625), (1, 80.875, 16.375),
          hw=0.125, layer_lock=[False, True, False])
print('SQUELCH In2 ride:', 'FOUND' if J else 'NONE', flush=True)
if J:
    print('  runs:', [(r['layer'], len(r['pts'])) for r in J['runs']],
          'vias:', J['vias'], flush=True)
    json.dump(J, open('scratch/work/ay/sq_in2_journey.json', 'w'))
    add_items(journey_items_dense(J, 'CDR_SQUELCH', hw=0.125))
    print('SQUELCH fragments after In2 ride (excl. dive/rise vias):',
          len(fragments('CDR_SQUELCH', (-50.0, 200.0, -100.0, 100.0))),
          flush=True)
    # now the C22 web on F from the top east site
    astar2 = make_astar((76.0, 86.0, 13.0, 23.0), 0.05)
    J2 = astar2('PHY_1V8', ((0,), 82.5, 17.32), (0, 78.1, 17.5), hw=0.10)
    print('C22 web (82.5,17.8)rot90 -> via F:', 'FOUND' if J2 else 'NONE',
          flush=True)
    if J2:
        print('  vias:', J2['vias'], 'runs:',
              [(r['layer'], len(r['pts'])) for r in J2['runs']], flush=True)
