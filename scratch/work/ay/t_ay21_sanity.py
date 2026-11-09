import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])
for lay in (0, 1, 2):
    hits = [it for it in pool[lay] if it[1] == 'PHY_1V8' and it[0] == 'via']
    print(f'layer {lay} PHY vias:', [(it[2]) for it in hits], flush=True)
print('fragments PHY:', len(fragments('PHY_1V8',
      (-50.0, 200.0, -100.0, 100.0))), flush=True)
astar = make_astar((74.0, 86.0, 8.0, 20.0), 0.05)
tests = [(((0, 1, 2), 78.1, 17.5), (2, 76.95, 14.5), 'via78 -> Bvert'),
         (((0, 1, 2), 78.1, 17.5), (0, 77.25, 16.4375), 'via78 -> U7.15'),
         (((0, 1, 2), 77.98, 10.02), (2, 76.95, 14.5), 'Svia -> Bvert'),
         (((0, 1, 2), 77.98, 10.02), (0, 78.1, 17.5), 'Svia -> via78 F'),
         (((0,), 72.02, 18.0), (2, 76.95, 14.5), 'C22old -> Bvert')]
for st, gl, nm in tests:
    J = astar('PHY_1V8', st, gl, hw=0.10)
    print(nm, ':', 'FOUND' if J else 'NONE', flush=True)
