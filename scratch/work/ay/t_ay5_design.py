import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ay')

src = open('scratch/work/ax/t_ax252_design214ae.py').read()
head = src.split("\nbox = (64.0")[0]
exec(head)

D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})
print('STP legs + stub in model', flush=True)

# --- correct C22: staged pads OUT, real pads IN ---
staged = [it for it in pool[0] if it[0] == 'pad'
          and abs(it[2][1] - 18.6) < 0.01 and it[2][0] in (79.12, 80.08)]
rip_items(staged)
print('ripped staged C22 pads:', len(staged), flush=True)
add_items({0: [('pad', 'PHY_1V8', (72.02, 18.0, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (72.98, 18.0, 0.280, 0.310, 0.0), 0.2)]})
print('C22 real pads restored at (72.5,18.0)', flush=True)

# head already ripped arm + vias (71.375 PHY, 73.434 GND, 76.487 GND).
# C22 STAYS, so restore its GND stitch via (73.434,17.685) on all layers.
add_items({l: [('via', 'GND', (73.434, 17.685, 0.25), 0.2)]
           for l in range(3)})
print('GND stitch via (73.434,17.685) restored', flush=True)

print('PHY_1V8 fragments BEFORE feed:', len(fragments('PHY_1V8', (-50.0, 200.0, -100.0, 100.0))), flush=True)

# --- A* the C22 feed: pad (72.02,18.0) -> (78.1,17.5) via / U7.15 ---
astar = make_astar((70.0, 79.5, 6.0, 20.5), 0.05)
GOALS = [(0, 78.1, 17.5, 'via F'), (2, 78.1, 17.5, 'via B'),
         (1, 78.1, 17.5, 'via In2'), (0, 77.25, 16.438, 'U7.15 pad'),
         (0, 77.25, 17.188, 'F seg joint')]
J = None
for gl, gx, gy, gn in GOALS:
    J = astar('PHY_1V8', ((0,), 72.02, 18.0), (gl, gx, gy), hw=0.10)
    print(f'feed goal {gn}:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        print('  vias:', J['vias'], 'runs:',
              [(r['layer'], len(r['pts'])) for r in J['runs']], flush=True)
        break
out = {}
if J:
    add_items(journey_items_dense(J, 'PHY_1V8', hw=0.10))
    print('PHY_1V8 fragments AFTER feed:', len(fragments('PHY_1V8', (-50.0, 200.0, -100.0, 100.0))),
          flush=True)
    out['c22_site'] = [72.5, 18.0, 0]
    out['c22_web'] = J
json.dump(out, open('scratch/work/ax/design251fix.json', 'w'))
print('AY5 DONE, fix written:', bool(out), flush=True)
