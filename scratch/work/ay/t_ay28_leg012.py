import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
H = {'__name__': 'ax252head'}
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0], H)
pool = H['pool']
load_board_pool = H['load_board_pool']
rip_items, add_items = H['rip_items'], H['add_items']
fragments = H['fragments']
journey_items_dense = H['journey_items_dense']
make_astar = H['make_astar']
faithful = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')

def near(it, x, y, tol=0.01):
    d = it[2]
    return abs(d[0] - x) < tol and abs(d[1] - y) < tol

# remove the staged C22 pads (only edit being reversed besides arm/C20/via)
staged = [it for it in pool[0] if it[0] == 'pad'
          and (near(it, 79.12, 18.6) or near(it, 80.08, 18.6))]
print('staged C22 pads removed:', len(staged), flush=True)
rip_items(staged)

def restore_excl(it):
    # keep ripped on purpose: GND via (76.487,9.139); C20 real 0603 pads;
    # old south via + its stub/B segs (moved by the design)
    if it[0] == 'via' and near(it, 76.487, 9.139):
        return True
    if it[0] == 'pad' and (near(it, 75.725, 18.5) or near(it, 77.275, 18.5)):
        return True
    d = it[2]
    if it[0] == 'seg' and (abs(d[2] - 77.869) < 0.01 and abs(d[3] - 10.056) < 0.01
                           or abs(d[0] - 77.869) < 0.01 and abs(d[1] - 10.056) < 0.01):
        return True
    if it[0] == 'via' and near(it, 77.869, 10.056):
        return True
    return False

restored = {0: [], 1: [], 2: []}
for lay in (0, 1, 2):
    cur = set(pool[lay])
    for it in faithful[lay]:
        if it not in cur and not restore_excl(it):
            restored[lay].append(it)
    add_items({lay: restored[lay]})
print('restored per layer:', {k: len(v) for k, v in restored.items()},
      flush=True)
for it in restored[0] + restored[2]:
    print('   ', it[1], it[0], it[2], flush=True)
print('PHY fragments (arm restored):',
      len(fragments('PHY_1V8', (-50.0, 200.0, -100.0, 100.0))), flush=True)

D = json.load(open('scratch/work/ax/design214_ax252.json'))
legs = D['stp_legs']
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.96, 0.25), 0.2)]})
for i, J in enumerate(legs):
    if i in (0, 1, 2):
        continue
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
print('STP fragments (no legs0-2):',
      len(fragments('ULPI_STP', (-50.0, 200.0, -100.0, 100.0))), flush=True)
s3 = legs[3]['runs'][0]['pts'][0]
l3 = legs[3]['runs'][0]['layer']
print('leg3 start:', l3, s3, flush=True)
astar = make_astar((68.0, 82.0, 6.0, 21.0), 0.05)
J = astar('ULPI_STP', ((0, 1, 2), 76.065, 17.96), (l3, s3[0], s3[1]),
          hw=0.10)
print('legs0-2 replacement (arm intact, east descent):',
      'FOUND' if J else 'NONE', flush=True)
if J:
    print('  vias:', J['vias'], 'runs:',
          [(r['layer'], len(r['pts'])) for r in J['runs']], flush=True)
    D2 = dict(D)
    newlegs = [J] + list(legs[3:])
    D2['n_legs_note'] = 'ay27: legs0-2 replaced by one journey'
    D2['stp_legs'] = newlegs
    json.dump(D2, open('scratch/work/ay/design214_ay26.json', 'w'))
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
    print('STP fragments (with new legs0-2):',
          len(fragments('ULPI_STP', (-50.0, 200.0, -100.0, 100.0))),
          flush=True)
