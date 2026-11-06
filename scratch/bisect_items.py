#!/usr/bin/env python3
"""Item-level bisect: apply ONE flagged dangling item at a time to a
fresh copy of BOARD, DRC, report the unconnected delta.
Usage: python3 scratch/bisect_items.py BOARD NET"""
import json, re, shutil, subprocess, sys, os

board, net_want = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drc_graph_prune as dgp

rep = dgp.run_drc(board, 'scratch/bi-drc.json')
base, _ = dgp.invariant(rep)
print(f'baseline unconnected: {base}')
items = []
for v in rep['violations']:
    if v['type'] in ('track_dangling', 'via_dangling'):
        for item in v['items']:
            net = re.search(r'\[(.*?)\]', item['description']).group(1)
            if net == net_want:
                items.append({'kind': v['type'],
                              'desc': item['description'],
                              'x': item['pos']['x'],
                              'y': item['pos']['y']})
print(f'{net_want}: {len(items)} flagged items')
script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      'drc_graph_prune.py')
for it in items:
    tmp = 'scratch/bi-board.kicad_pcb'
    shutil.copyfile(board, tmp)
    with open('scratch/bi-plan.json', 'w') as f:
        json.dump([it], f)
    r = subprocess.run([sys.executable, script, '--apply',
                        'scratch/bi-plan.json', tmp],
                       capture_output=True, text=True)
    m = re.search(r'removed (\d+), vetoed (\d+), skipped (\d+)',
                  r.stdout)
    rep2 = dgp.run_drc(tmp, 'scratch/bi-drc.json')
    cnt, _ = dgp.invariant(rep2)
    flag = '  <<<< SPLIT' if cnt > base else ''
    print(f"[{m.groups() if m else '?'}] unconnected {base} -> {cnt}  "
          f"{it['desc']} @ ({it['x']}, {it['y']}){flag}", flush=True)
