"""t_au1: pair fence-ablation (brief step 1).
Case A: CLK fixed as exact items (centred journey32); DATA widest;
identify binding BOARD fences; ablate each singly (second-min trick)
and in candidate groups (full rebuild); report bottleneck deltas.
Case B: symmetric (DATA journey30 fixed; CLK widest).
Usage: t_au1_ablate.py A|B"""
import sys, math, json
import numpy as np
sys.path.insert(0, 'scratch/work/au')
import t_au1_lib as U
import t_ai_lib as L

mode = sys.argv[1]
if mode == 'A':
    sib_net, net = 'CAP_CLK', 'CAP_DATA'
    sib_file = 'scratch/work/as/journey32_CAP_CLK_CD.json'
else:
    sib_net, net = 'CAP_DATA', 'CAP_CLK'
    sib_file = 'scratch/work/as/journey30_CAP_DATA_DC.json'

pool = U.load_pool()
sib = U.journey_items(sib_file, sib_net)
comb = {l: list(pool[l]) + sib[l] for l in range(3)}
print(f'pool sizes: {[len(pool[l]) for l in range(3)]}, '
      f'sibling items: {[len(sib[l]) for l in range(3)]}', flush=True)

G, AM, F2 = {}, {}, {}
for l in range(3):
    G[l], AM[l], F2[l] = U.build_field(comb[l], net)
print('fields built', flush=True)

bval, came, goal = U.widest(G, net)
print(f'== BASE {net} widest bottleneck (sibling {sib_net} fixed): '
      f'{bval:+.3f}', flush=True)
states = U.widest_path_states(came, goal)
binds = U.bind_items(G, AM, comb, net, (came, goal), bval)
print(f'binding items ({len(binds)}):', flush=True)
board_binds = []
for (l, idx, it, desc) in binds:
    tag = 'SIBLING' if it[1] == sib_net else 'BOARD'
    print(f'   [{tag}] L{l} {L.fmt_it(it)}  @ {desc}', flush=True)
    if tag == 'BOARD':
        board_binds.append((l, idx, it))


def ablate_secondmin(match):
    """match(l, idx, it)->bool over comb; returns G' using F2 where the
    argmin item matches (exact unless two matched items are 1st+2nd)."""
    Gp = {}
    for l in range(3):
        mask = np.zeros(G[l].shape, dtype=bool)
        idxs = np.unique(AM[l][AM[l] >= 0])
        hit = [i for i in idxs if match(l, int(i), comb[l][int(i)])]
        for i in hit:
            mask |= (AM[l] == i)
        Gp[l] = np.where(mask, F2[l], G[l])
    return Gp


def fmt_key(it):
    return (it[0], it[1], tuple(round(v, 3) for v in it[2]))


print('-- single BOARD-item ablations (second-min):', flush=True)
for (l, idx, it) in board_binds:
    key = fmt_key(it)
    Gp = ablate_secondmin(lambda ll, ii, jt: fmt_key(jt) == key)
    bv, _, _ = U.widest(Gp, net)
    print(f'   - {L.fmt_it(it)}: bottleneck {bv:+.3f} '
          f'(delta {bv - bval:+.3f})', flush=True)

GROUPS = {
    'THR_DAC via (64.875,6.625)': lambda l, it:
        it[0] == 'via' and abs(it[2][0] - 64.875) < 0.1
        and abs(it[2][1] - 6.625) < 0.1,
    'SCL In2 chain (corridor)': lambda l, it:
        l == 1 and it[1] == 'I2C_SCL'
        and 62 < U.item_centre(it)[0] < 72 and -1 < U.item_centre(it)[1] < 10,
    'PG_3V3 B braid (corridor)': lambda l, it:
        l == 2 and it[1] == 'PG_3V3'
        and 60 < U.item_centre(it)[0] < 70 and 0 < U.item_centre(it)[1] < 16,
    '+3V3D via (70.875,15.875)': lambda l, it:
        it[0] == 'via' and abs(it[2][0] - 70.875) < 0.1
        and abs(it[2][1] - 15.875) < 0.1,
    'SDA via (69.9,0.82)': lambda l, it:
        it[0] == 'via' and abs(it[2][0] - 69.9) < 0.06
        and abs(it[2][1] - 0.82) < 0.06,
    'XO In2 web (rest)': lambda l, it:
        l == 1 and it[1] == 'XO',
    'HV band In2 (rest, x>=70.2)': lambda l, it:
        l == 1 and it[1] == 'HV_SHDN',
}
print('-- group ablations (full rebuild):', flush=True)
for name, pred in GROUPS.items():
    comb2 = {l: [it for it in comb[l] if not pred(l, it)] for l in range(3)}
    n_removed = sum(len(comb[l]) - len(comb2[l]) for l in range(3))
    if n_removed == 0:
        print(f'   - {name}: no items in model', flush=True)
        continue
    G2 = {}
    for l in range(3):
        G2[l], _, _ = U.build_field(comb2[l], net)
    bv, _, _ = U.widest(G2, net)
    print(f'   - {name} ({n_removed} items): bottleneck {bv:+.3f} '
          f'(delta {bv - bval:+.3f})', flush=True)
print('done', flush=True)
