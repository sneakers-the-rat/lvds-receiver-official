"""t_au70: phase-2 model assembly + conflict census + fragments.
Model: v6 base + CLK9 (truncated at (69.55,2.7)) + bheal + hop +
heal1 + exit (F run + via (69.075,2.8) + B join) + DATA entry/tail.
Conflicts: new items vs PG_3V3/+3V3D/XO items (margin<0).
Fragments per net in its box after conflict rips."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au60_v6.py').read()
exec(src.split("\nout = {")[0], g)
pool = g['pool']
journey_items_dense = g['journey_items_dense']
import t_ai_lib as L
import t_au1_lib as U
C = U.item_centre
# NOTE: t_au60 head placed bheal+hop+au40exit; remove au40 exit:


def is_au40_exit(it):
    if it[1] != 'CAP_CLK':
        return False
    if it[0] == 'via':
        return abs(it[2][0] - 68.975) < 0.01 and abs(it[2][1] - 2.8) < 0.01
    return it[2][0] < 70.3 and it[2][2] < 70.3


for l in range(3):
    pool[l] = [it for it in pool[l] if not is_au40_exit(it)]

NEW = {0: [], 1: [], 2: []}


def add_new(J, net, hw=0.10):
    for l, its in journey_items_dense(J, net, hw=hw).items():
        NEW[l] += its
        pool[l] += its


J67 = json.load(open('scratch/work/au/heals_au67.json'))
add_new(J67['v3a_heal1'], '+3V3A', 0.10)
add_new(J67['clk_exit_frun'], 'CAP_CLK', 0.10)
for l in range(3):
    it = ('via', 'CAP_CLK', (69.075, 2.8, 0.25), 0.2)
    NEW[l].append(it)
    pool[l].append(it)
bj = ('seg', 'CAP_CLK', (69.075, 2.8, 69.55, 2.7, 0.10), 0.2)
NEW[2].append(bj)
pool[2].append(bj)
add_new(J67['data_entry'], 'CAP_DATA', 0.10)
add_new(J67['data_tail'], 'CAP_DATA', 0.10)
# CLK9 truncated at rejoin (69.55,2.7)
J9 = json.load(open('scratch/work/au/journey_au9_CLK.json'))
runs = []
for run in J9['runs']:
    pts = [tuple(p) for p in run['pts']]
    if run['layer'] == 2 and pts[0] == (70.15, 2.1):
        i = pts.index((69.55, 2.7))
        runs.append(dict(layer=2, pts=[list(p) for p in pts[i:]]))
    else:
        runs.append(run)
CLK9T = dict(vias=J9['vias'], runs=runs)
add_new(CLK9T, 'CAP_CLK', 0.10)
print('model assembled; new items per layer:',
      {l: len(NEW[l]) for l in range(3)}, flush=True)

# conflict census
TARGETS = {'PG_3V3': (54.0, 74.0, -18.0, 18.0),
           '+3V3D': (66.0, 78.0, 16.0, 28.0),
           'XO': (64.0, 78.0, 14.0, 24.0)}
conf = {}
for net, (bx0, bx1, by0, by1) in TARGETS.items():
    lst = []
    for l in range(3):
        cand = [it for it in pool[l] if it[1] == net
                and bx0 < C(it)[0] < bx1 and by0 < C(it)[1] < by1]
        for nit in NEW[l]:
            ncx, ncy = C(nit)
            if not (bx0 - 2 < ncx < bx1 + 2 and by0 - 2 < ncy < by1 + 2):
                continue
            for it in cand:
                m = L.item_margin(l, nit, it)
                if m < 0:
                    lst.append((l, it, nit, round(m, 3)))
    conf[net] = lst
    print(f'{net}: {len(lst)} conflicts', flush=True)
    for (l, it, nit, m) in lst:
        print(f'  L{l} {m:+.3f} {L.fmt_it(it)}  vs NEW {L.fmt_it(nit)}',
              flush=True)
json.dump({net: [(l, it[0], it[1], list(it[2]), it[3])
                 for (l, it, nit, m) in conf[net]]
           for net in conf},
          open('scratch/work/au/conflicts_au70.json', 'w'))
print('done', flush=True)
