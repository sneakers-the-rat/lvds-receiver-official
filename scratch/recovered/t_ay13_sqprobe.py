import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])
D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})
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
    victims += [it for it in pool[0] if segmatch(it, 'CDR_SQUELCH', a, b)]
rip_items(victims)
print('ripped', len(victims), flush=True)
print('netclass CDR_SQUELCH:', netclass('CDR_SQUELCH'), flush=True)
astar = make_astar((74.0, 82.5, 15.0, 21.0), 0.05)
probes = [(77.0, 19.3), (79.0, 19.3), (80.5, 19.0), (81.2, 18.375),
          (81.2, 16.5), (80.875, 16.375), (79.0, 17.0), (77.0, 17.5)]
for gx, gy in probes:
    J = astar('CDR_SQUELCH', ((1,), 75.375, 19.625), (1, gx, gy),
              hw=0.125, layer_lock=[False, True, False])
    print(f'In2 probe -> ({gx},{gy}):', 'FOUND' if J else 'NONE',
          flush=True)
