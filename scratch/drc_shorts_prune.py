#!/usr/bin/env python3
"""Remove shorting stub copper, DRC-refereed, per-net batches.

Written 2026-11-05 for the shorting_items class (59 on exp158). The
cluster evidence: heal-era fanout stubs around fine-pitch parts
(above all U5, the ADN2813) terminate on FOREIGN pads -- +3V3D stubs
on U5 GND/CLKP/CLKN pads, CDR_DATP tracks on U5's +3V3D pad, I2C vias
on CDR pads. Each DRC violation names the offending track/via and
the pad it touches.

Method (same discipline as drc_graph_prune): KiCad proposes (the
track items of shorting_items violations; vias are NOT auto-deleted
-- a via on a foreign pad can still be its net's layer bridge, those
go to the hand list), the contact graph vetoes segments that bridge
two pad groups of their own net, and KiCad referees: deletions are
applied one NET at a time to the working board, DRC runs after each
net, and any net whose batch raises unconnected_items is restored
wholesale and hand-listed. A deletion is never banked on a model.

Usage: python3 scratch/drc_shorts_prune.py IN OUT
"""
import json, re, shutil, subprocess, sys, os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drc_graph_prune as dgp

src, dst = sys.argv[1], sys.argv[2]
shutil.copyfile(src, dst)
total_removed = 0
hand = []
for rnd in range(12):
    rep = dgp.run_drc(dst, 'scratch/sp-round.json')
    cnt, _ = dgp.invariant(rep)
    by_net = defaultdict(list)
    via_items = []
    for v in rep['violations']:
        if v['type'] != 'shorting_items':
            continue
        for item in v['items']:
            desc = item['description']
            if desc.startswith('Pad'):
                continue
            entry = {'kind': 'track_dangling', 'desc': desc,
                     'x': item['pos']['x'], 'y': item['pos']['y']}
            if desc.startswith('Via'):
                via_items.append(desc)
            else:
                net = re.search(r'\[(.*?)\]', desc).group(1)
                by_net[net].append(entry)
    print(f'round {rnd}: unconnected {cnt}, shorting track items '
          f'{sum(len(g) for g in by_net.values())} across '
          f'{len(by_net)} nets, via shorts {len(via_items)}',
          flush=True)
    if not by_net:
        print('no shorting tracks remain.')
        break
    round_removed = 0
    for net, group in sorted(by_net.items()):
        shutil.copyfile(dst, dst + '.bak')
        with open('scratch/sp-plan.json', 'w') as f:
            json.dump(group, f)
        r = subprocess.run([sys.executable,
                            os.path.join(os.path.dirname(
                                os.path.abspath(__file__)),
                                'drc_graph_prune.py'),
                            '--apply', 'scratch/sp-plan.json', dst],
                           capture_output=True, text=True)
        m = re.search(r'removed (\d+), vetoed (\d+), skipped (\d+)',
                      r.stdout)
        if r.returncode != 0 or not m:
            print(f'  {net}: apply failed, batch restored. '
                  f'{r.stderr[-200:]}')
            shutil.copyfile(dst + '.bak', dst)
            hand.extend(g['desc'] for g in group)
            continue
        removed, vetoed, skipped = (int(m.group(1)), int(m.group(2)),
                                    int(m.group(3)))
        rep2 = dgp.run_drc(dst, 'scratch/sp-round.json')
        cnt2, _ = dgp.invariant(rep2)
        if cnt2 > cnt:
            print(f'  {net}: SPLIT ({cnt} -> {cnt2}); batch restored, '
                  f'hand-listed.')
            shutil.copyfile(dst + '.bak', dst)
            hand.extend(g['desc'] for g in group)
            continue
        cnt = cnt2
        round_removed += removed
        if vetoed or skipped:
            print(f'  {net}: removed {removed}, vetoed {vetoed}, '
                  f'skipped {skipped} (hand list)')
            hand.extend(g['desc'] for g in group
                        if True and (vetoed or skipped))
    total_removed += round_removed
    print(f'round {rnd}: removed {round_removed}', flush=True)
    if round_removed == 0:
        break
print(f'TOTAL removed: {total_removed}')
if via_items:
    print('via shorts (hand list, not auto-deleted):')
    for d in sorted(set(via_items)):
        print(f'  {d}')
