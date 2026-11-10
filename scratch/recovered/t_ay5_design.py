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

# --- rip the PHY west arm + tail + goal via + GND via 76.487 (v2 config) ---
def segmatch(it, net, lay, a, b):
    if it[0] != 'seg' or it[1] != net:
        return False
    d = it[2]
    return ((abs(d[0]-a[0]) < 0.01 and abs(d[1]-a[1]) < 0.01 and
             abs(d[2]-b[0]) < 0.01 and abs(d[3]-b[1]) < 0.01) or
            (abs(d[2]-a[0]) < 0.01 and abs(d[3]-a[1]) < 0.01 and
             abs(d[0]-b[0]) < 0.01 and abs(d[1]-b[1]) < 0.01))
def viamatch(it, net, x, y):
    return it[0] == 'via' and it[1] == net and abs(it[2][0]-x) < 0.01 \
        and abs(it[2][1]-y) < 0.01
victims = {0: [], 1: [], 2: []}
for lay, a, b in ((2, (77.8, 16.2), (73.4, 16.2)),
                  (2, (73.4, 16.2), (72.9, 16.9)),
                  (2, (72.9, 16.9), (72.125, 17.625)),
                  (2, (72.125, 17.625), (71.375, 17.625)),
                  (0, (71.375, 17.625), (71.725, 17.75)),
                  (0, (71.725, 17.75), (71.725, 18.0))):
    v = [it for it in pool[lay] if segmatch(it, 'PHY_1V8', lay, a, b)]
    print(f'arm rip L{lay} {a}->{b}: {len(v)}', flush=True)
    assert len(v) == 1, (lay, a, b, len(v))
    victims[lay] += v
for lay in range(3):
    v = [it for it in pool[lay] if viamatch(it, 'PHY_1V8', 71.375, 17.625)]
    victims[lay] += v
    v2 = [it for it in pool[lay] if viamatch(it, 'GND', 76.487, 9.139)]
    victims[lay] += v2
for lay in range(3):
    if victims[lay]:
        rip_items(victims[lay])
        print(f'ripped on L{lay}: {len(victims[lay])}', flush=True)

print('PHY_1V8 fragments BEFORE feed:', fragments('PHY_1V8'), flush=True)

# --- A* the C22 feed: pad (72.02,18.0) -> (78.1,17.5) via / U7.15 ---
astar = make_astar((70.0, 79.5, 13.5, 20.5), 0.05)
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
    print('PHY_1V8 fragments AFTER feed:', fragments('PHY_1V8'),
          flush=True)
    out['c22_site'] = [72.5, 18.0, 0]
    out['c22_web'] = J
json.dump(out, open('scratch/work/ax/design251fix.json', 'w'))
print('AY5 DONE, fix written:', bool(out), flush=True)
