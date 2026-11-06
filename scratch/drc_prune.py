#!/usr/bin/env python3
"""Prune dead copper using KiCad's OWN connectivity engine as both the
instrument and the referee.

Why this exists (2026-11-05): two home-grown geometric models failed
at this job -- prune_dead's redrawn-graph model absorbed real barbs
into junctions, and a strengthened centreline/copper-overlap census
deleter still severed live joints (DRC unconnected 50 -> 115 on v1,
50 -> 51 on v2). KiCad's DRC already computes true connectivity and
flags dead copper itself (track_dangling / via_dangling, with item
UUIDs and positions in its JSON report). So:

  loop:
    1. kicad-cli pcb drc on the board -> JSON
    2. invariant check vs the previous round: unconnected_items count
       must not rise, and no pad UUID may newly appear in an
       unconnected item (a new pad there = a split group). On any
       rise: restore the last good round's file and stop.
    3. delete exactly the items DRC flagged dangling this round
       (resolved to board objects by net+layer+position in a fresh
       pcbnew process -- reads all happen before any Remove, because
       KiCad 8's python proxies rot after removals)
    4. repeat until a round flags nothing new.

Every deletion is certified by the same engine that judges the
result. Multi-segment dead chains peel one segment per round (DRC
flags only the current free end); rounds run in parallel across
chains, ~8 s per round.

Usage: python3 scratch/drc_prune.py IN.kicad_pcb OUT.kicad_pcb
Modes (internal): --apply PLAN.json BOARD  (one delete batch)
"""
import json, math, re, shutil, subprocess, sys, os
import pcbnew

MM = 1_000_000

def drc(board_path, out_json):
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--output', out_json,
                    '--format', 'json', '--all-track-errors',
                    board_path], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(out_json) as f:
        return json.load(f)

def invariant(report):
    pads = set()
    for it in report['unconnected_items']:
        for item in it['items']:
            if item['description'].startswith('Pad'):
                pads.add(item['uuid'])
    return len(report['unconnected_items']), pads

def plan(report):
    out = []
    for v in report['violations']:
        if v['type'] in ('track_dangling', 'via_dangling'):
            for item in v['items']:
                out.append({'kind': v['type'], 'uuid': item['uuid'],
                            'desc': item['description'],
                            'x': item['pos']['x'], 'y': item['pos']['y']})
    return out

def apply_plan(plan_path, board_path):
    with open(plan_path) as f:
        items = json.load(f)
    board = pcbnew.LoadBoard(board_path)
    tracks, vias = [], []
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_TRACE_T:
            a, b = t.GetStart(), t.GetEnd()
            tracks.append((t, t.GetNetname(), t.GetLayer(),
                           a.x, a.y, b.x, b.y))
        elif t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            vias.append((t, t.GetNetname(), p.x, p.y))
    layer_ids = {pcbnew.LayerName(l): l for l in
                 (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)}
    removed, skipped = 0, []
    for it in items:
        m = re.search(r'\[(.*?)\] on ([A-Za-z0-9_.]+)', it['desc'])
        net, lname = m.group(1), m.group(2)
        x, y = round(it['x'] * MM), round(it['y'] * MM)
        hit = None
        if it['kind'] == 'track_dangling':
            lid = layer_ids[lname]
            cand = [c for c in tracks
                    if c[1] == net and c[2] == lid and
                    (math.hypot(c[3] - x, c[4] - y) <= 3000 or
                     math.hypot(c[5] - x, c[6] - y) <= 3000)]
            if len(cand) == 1:
                hit = cand[0][0]
        else:
            cand = [c for c in vias if c[1] == net and
                    math.hypot(c[2] - x, c[3] - y) <= 3000]
            if len(cand) == 1:
                hit = cand[0][0]
        if hit is None:
            skipped.append(it['desc'])
            continue
        board.Remove(hit)
        removed += 1
    board.Save(board_path)
    print(f'apply: removed {removed}, skipped {len(skipped)}')
    for s in skipped:
        print(f'  SKIP (no unique match): {s}')

def main():
    if sys.argv[1] == '--apply':
        apply_plan(sys.argv[2], sys.argv[3])
        return
    src, dst = sys.argv[1], sys.argv[2]
    shutil.copyfile(src, dst)
    work_json = 'scratch/drc-prune-round.json'
    plan_path = 'scratch/drc-prune-plan.json'
    prev = None
    total_removed = 0
    for rnd in range(80):
        rep = drc(dst, work_json)
        cnt, pads = invariant(rep)
        dang = sum(1 for v in rep['violations']
                   if v['type'] in ('track_dangling', 'via_dangling'))
        print(f'round {rnd}: unconnected {cnt}, dangling flagged '
              f'{dang}', flush=True)
        if prev is not None:
            pcnt, ppads = prev
            if cnt > pcnt or not pads <= ppads:
                print(f'INVARIANT BROKEN (unconnected {pcnt} -> {cnt}, '
                      f'new pads in unconnected: '
                      f'{sorted(pads - ppads)[:3]}); restoring last '
                      f'good board and stopping.')
                shutil.copyfile(dst + '.good', dst)
                break
        prev = (cnt, pads)
        shutil.copyfile(dst, dst + '.good')
        items = plan(rep)
        if not items:
            print('converged: DRC flags no dangling copper.')
            break
        with open(plan_path, 'w') as f:
            json.dump(items, f)
        r = subprocess.run([sys.executable, os.path.abspath(__file__),
                            '--apply', plan_path, dst],
                           capture_output=True, text=True)
        print(r.stdout.strip())
        m = re.search(r'removed (\d+)', r.stdout)
        if m:
            total_removed += int(m.group(1))
        if r.returncode != 0:
            print('apply failed:', r.stderr[-500:])
            break
    print(f'TOTAL removed across rounds: {total_removed}')

if __name__ == '__main__':
    main()
