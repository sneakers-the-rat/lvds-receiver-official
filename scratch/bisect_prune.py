#!/usr/bin/env python3
"""Bisect the drc_graph_prune round-0 removals by net: apply only one
net's flagged items to a fresh copy, DRC it, report the unconnected
count. Finds which net's batch contains the load-bearing deletion.
Usage: python3 scratch/bisect_prune.py BOARD"""
import json, re, shutil, subprocess, sys, os
from collections import defaultdict

board = sys.argv[1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drc_graph_prune as dgp

rep = dgp.run_drc(board, 'scratch/bisect-drc.json')
base, _ = dgp.invariant(rep)
print(f'baseline unconnected: {base}')
items = []
for v in rep['violations']:
    if v['type'] in ('track_dangling', 'via_dangling'):
        for item in v['items']:
            items.append({'kind': v['type'],
                          'desc': item['description'],
                          'x': item['pos']['x'], 'y': item['pos']['y']})
by_net = defaultdict(list)
for it in items:
    net = re.search(r'\[(.*?)\]', it['desc']).group(1)
    by_net[net].append(it)
for net, group in sorted(by_net.items()):
    tmp = 'scratch/bisect-board.kicad_pcb'
    shutil.copyfile(board, tmp)
    with open('scratch/bisect-plan.json', 'w') as f:
        json.dump(group, f)
    r = subprocess.run([sys.executable,
                        os.path.join(os.path.dirname(
                            os.path.abspath(__file__)),
                            'drc_graph_prune.py'),
                        '--apply', 'scratch/bisect-plan.json', tmp],
                       capture_output=True, text=True)
    m = re.search(r'removed (\d+), vetoed (\d+), skipped (\d+)',
                  r.stdout)
    rep2 = dgp.run_drc(tmp, 'scratch/bisect-drc.json')
    cnt, _ = dgp.invariant(rep2)
    flag = '  <<<< SPLIT' if cnt > base else ''
    print(f'{net:12s} flagged {len(group)}  apply[{m.groups() if m else "?"}]'
          f'  unconnected {base} -> {cnt}{flag}', flush=True)
