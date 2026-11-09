import sys, json
sys.path.insert(0, 'scratch/work/ax')

src = open('scratch/work/ax/t_ax246_design214ad.py').read()
head = src.split("\nbox = (64.0")[0]
exec(head)

box = (64.0, 79.5, -6.0, 20.5)
goal = (0, 71.3375, -2.25)
found = {}
for label, s in (('from B (73.0,-1.5)', ((2,), 73.0, -1.5)),
                 ('from I (72.7,-1.3)', ((1,), 72.7, -1.3)),
                 ('from dive via B (76.065,17.99)', ((2,), 76.065, 17.99))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', s, goal, hw=0.10)
    print(f'FULL ML {label} -> F pad:', 'FOUND' if J else 'NONE',
          ('vias=' + str(J['vias'])) if J else '', flush=True)
    if J:
        found[label] = J
        print('  runs:', [(r[0][0], len(r)) for r in J['runs']], flush=True)
        break
if found:
    json.dump(found, open('scratch/work/ax/design214_ax250.json', 'w'))
    print('FULL ML JOURNEY SAVED', flush=True)
print('FULL ML DONE', flush=True)
