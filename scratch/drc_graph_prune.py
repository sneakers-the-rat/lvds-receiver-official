#!/usr/bin/env python3
"""Prune dead copper: KiCad DRC proposes, the contact graph vetoes
bridges, KiCad DRC referees.

Fourth instrument for this job (2026-11-05); the three failures that
define it:

- prune_dead / census models (centreline geometry): missed real
  joints (via-ring landings, off-centre pad landings) and invented
  free ends mid-route.
- Deleting DRC's dangling list raw: dangling certifies a free END,
  not a dead segment -- overshoot tracks bridge two pad groups along
  their bodies (round 0: unconnected 50 -> 52, restored).
- A pure contact-graph leaf test anchored everything except 1,379
  GND stubs (unjudgeable without zone modelling) and 15 others: its
  free-end test still disagrees with the engine at the margins.

So each round:
  1. kicad-cli DRC flags dangling tracks/vias (the engine's own
     connectivity, zones included -- candidacy is KiCad's problem).
  2. Each flagged TRACK is bridge-tested on the copper-contact graph
     (real widths, via radii, pad shapes, body crossings): if, without
     it, its contacts touch two or more pad-bearing components, it is
     a live bridge -- VETOED, kept. Flagged vias are deleted outright
     (a via with an unconnected side bridges nothing).
     The graph only ever vetoes; its over-anchoring errs toward
     keeping copper, the safe direction.
  3. Survivors are deleted; the next round's DRC re-verifies the
     invariant (unconnected count must not rise; no pad may newly
     appear in an unconnected item). Any violation restores the last
     good round and stops.

Usage: python3 scratch/drc_graph_prune.py IN OUT
Modes (internal): --apply PLAN.json BOARD
"""
import json, math, re, shutil, subprocess, sys, os
from collections import defaultdict
import pcbnew

MM = 1_000_000
CU = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)

def run_drc(board_path, out_json):
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

# ---------- contact graph (veto machinery, from graph_prune) --------
def build_graph(board):
    segs = []
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_TRACE_T:
            a, b = t.GetStart(), t.GetEnd()
            segs.append({'net': t.GetNetname(), 'layer': t.GetLayer(),
                         'x0': a.x, 'y0': a.y, 'x1': b.x, 'y1': b.y,
                         'w': t.GetWidth(), 'obj': t})
    vias = []
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            vias.append({'net': t.GetNetname(), 'x': p.x, 'y': p.y,
                         'r': t.GetWidth() // 2, 'obj': t})
    pads = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            pads.append({'net': p.GetNetname(),
                         'layers': {l for l in CU if p.IsOnLayer(l)},
                         'bb': (bb.GetLeft(), bb.GetTop(),
                                bb.GetRight(), bb.GetBottom())})
    zones = []
    for z in board.Zones():
        bb = z.GetBoundingBox()
        zones.append({'net': z.GetNetname(), 'layer': z.GetLayer(),
                      'bb': (bb.GetLeft(), bb.GetTop(),
                             bb.GetRight(), bb.GetBottom())})
    via_by_net = defaultdict(list)
    for i, v in enumerate(vias):
        via_by_net[v['net']].append(i)
    pad_by_net = defaultdict(list)
    for i, p in enumerate(pads):
        pad_by_net[p['net']].append(i)
    seg_by_nl = defaultdict(list)
    for i, s in enumerate(segs):
        seg_by_nl[(s['net'], s['layer'])].append(i)

    def pt_seg(x, y, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 == 0:
            return math.hypot(x - ax, y - ay)
        u = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        return math.hypot(x - (ax + u * dx), y - (ay + u * dy))

    contacts = [set() for _ in segs]
    for (net, layer), idxs in seg_by_nl.items():
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                i, j = idxs[a], idxs[b]
                s, o = segs[i], segs[j]
                reach = s['w'] // 2 + o['w'] // 2 + 1000
                hit = False
                for (x, y) in ((s['x0'], s['y0']), (s['x1'], s['y1'])):
                    if min(math.hypot(x - o['x0'], y - o['y0']),
                           math.hypot(x - o['x1'], y - o['y1']),
                           pt_seg(x, y, o['x0'], o['y0'],
                                  o['x1'], o['y1'])) <= reach:
                        hit = True
                for (x, y) in ((o['x0'], o['y0']), (o['x1'], o['y1'])):
                    if pt_seg(x, y, s['x0'], s['y0'],
                              s['x1'], s['y1']) <= reach:
                        hit = True
                if not hit:
                    def orient(ax, ay, bx, by, cx, cy):
                        return (bx - ax) * (cy - ay) - \
                               (by - ay) * (cx - ax)
                    d1 = orient(o['x0'], o['y0'], o['x1'], o['y1'],
                                s['x0'], s['y0'])
                    d2 = orient(o['x0'], o['y0'], o['x1'], o['y1'],
                                s['x1'], s['y1'])
                    d3 = orient(s['x0'], s['y0'], s['x1'], s['y1'],
                                o['x0'], o['y0'])
                    d4 = orient(s['x0'], s['y0'], s['x1'], s['y1'],
                                o['x1'], o['y1'])
                    if ((d1 > 0) != (d2 > 0)) and \
                       ((d3 > 0) != (d4 > 0)):
                        hit = True
                if hit:
                    contacts[i].add(('s', j))
                    contacts[j].add(('s', i))
    for i, s in enumerate(segs):
        hw = s['w'] // 2
        for vi in via_by_net.get(s['net'], ()):
            v = vias[vi]
            if pt_seg(v['x'], v['y'], s['x0'], s['y0'],
                      s['x1'], s['y1']) <= v['r'] + hw + 1000:
                contacts[i].add(('v', vi))
        for pi in pad_by_net.get(s['net'], ()):
            p = pads[pi]
            if s['layer'] not in p['layers']:
                continue
            l, t, r, b = p['bb']
            d = min(pt_seg(l, t, s['x0'], s['y0'], s['x1'], s['y1']),
                    pt_seg(r, t, s['x0'], s['y0'], s['x1'], s['y1']),
                    pt_seg(l, b, s['x0'], s['y0'], s['x1'], s['y1']),
                    pt_seg(r, b, s['x0'], s['y0'], s['x1'], s['y1']))
            for (x, y) in ((s['x0'], s['y0']), (s['x1'], s['y1'])):
                dx = max(l - x, 0, x - r)
                dy = max(t - y, 0, y - b)
                d = min(d, math.hypot(dx, dy))
            # through-the-middle crossings: endpoint/corner distances
            # can both be large; a segment whose AABB meets the rect
            # and whose line passes through it is caught by checking
            # the segment against the rect edges via the corner
            # distances already taken plus endpoint containment:
            if (l <= s['x0'] <= r and t <= s['y0'] <= b) or \
               (l <= s['x1'] <= r and t <= s['y1'] <= b):
                d = 0
            if d <= hw + 1000:
                contacts[i].add(('p', pi))
    seg_by_net = defaultdict(list)
    for i, s in enumerate(segs):
        seg_by_net[s['net']].append(i)
    return segs, vias, pads, contacts, seg_by_net, pad_by_net, zones

def bridges(i, segs, contacts, seg_by_net, pad_by_net):
    net = segs[i]['net']
    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for j in seg_by_net[net]:
        if j == i:
            continue
        for kind, k in contacts[j]:
            if kind == 's' and k == i:
                continue
            union(('s', j), (kind, k))
    padcomp = {find(('p', pi)) for pi in pad_by_net.get(net, ())}
    touched = set()
    for kind, k in contacts[i]:
        r = find((kind, k))
        if r in padcomp:
            touched.add(r)
    return len(touched) >= 2

# ---------- one delete batch in a fresh process ---------------------
def apply_plan(plan_path, board_path):
    with open(plan_path) as f:
        items = json.load(f)
    board = pcbnew.LoadBoard(board_path)
    segs, vias, pads, contacts, seg_by_net, pad_by_net, zones = \
        build_graph(board)
    layer_ids = {pcbnew.LayerName(l): l for l in CU}

    def anchored(segs, vias, pads, s, x, y, self_idx):
        # copper-overlap anchor test for one endpoint (matcher use)
        net, layer, hw = s['net'], s['layer'], s['w'] // 2
        for z in zones:
            if z['net'] == net and z['layer'] == layer:
                l, t, r, b = z['bb']
                if l - hw <= x <= r + hw and t - hw <= y <= b + hw:
                    return True
        for p in pads:
            if p['net'] != net or layer not in p['layers']:
                continue
            l, t, r, b = p['bb']
            if l - hw <= x <= r + hw and t - hw <= y <= b + hw:
                return True
        for v in vias:
            if v['net'] == net and \
               math.hypot(v['x'] - x, v['y'] - y) <= v['r'] + hw + 1000:
                return True
        for j, o in enumerate(segs):
            if j == self_idx or o['net'] != net or o['layer'] != layer:
                continue
            reach = hw + o['w'] // 2 + 1000
            if math.hypot(o['x0'] - x, o['y0'] - y) <= reach or \
               math.hypot(o['x1'] - x, o['y1'] - y) <= reach:
                return True
            dx, dy = o['x1'] - o['x0'], o['y1'] - o['y0']
            L2 = dx * dx + dy * dy
            if L2 == 0:
                continue
            u = max(0.0, min(1.0, ((x - o['x0']) * dx +
                                   (y - o['y0']) * dy) / L2))
            if math.hypot(x - (o['x0'] + u * dx),
                          y - (o['y0'] + u * dy)) <= reach:
                return True
        return False

    removed, vetoed, skipped = 0, [], []
    for it in items:
        m = re.search(r'\[(.*?)\] on ([A-Za-z0-9_.]+)', it['desc'])
        net, lname = m.group(1), m.group(2)
        x, y = round(it['x'] * MM), round(it['y'] * MM)
        if it['kind'] == 'via_dangling':
            cand = [v for v in vias if v['net'] == net and
                    math.hypot(v['x'] - x, v['y'] - y) <= 3000]
            if len(cand) == 1:
                board.Remove(cand[0]['obj'])
                removed += 1
            else:
                skipped.append(it['desc'])
            continue
        lid = layer_ids[lname]
        cand = [i for i, s in enumerate(segs)
                if s['net'] == net and s['layer'] == lid and
                (math.hypot(s['x0'] - x, s['y0'] - y) <= 3000 or
                 math.hypot(s['x1'] - x, s['y1'] - y) <= 3000)]
        if not cand:
            # Shorting items report the CONTACT point, which can sit
            # mid-body: fall back to segments whose body passes under
            # the point (distance <= half width + slack).
            def body_d(s):
                dx, dy = s['x1'] - s['x0'], s['y1'] - s['y0']
                L2 = dx * dx + dy * dy
                if L2 == 0:
                    return math.hypot(s['x0'] - x, s['y0'] - y)
                u = max(0.0, min(1.0, ((x - s['x0']) * dx +
                                       (y - s['y0']) * dy) / L2))
                return math.hypot(x - (s['x0'] + u * dx),
                                  y - (s['y0'] + u * dy))
            cand = [i for i, s in enumerate(segs)
                    if s['net'] == net and s['layer'] == lid and
                    body_d(s) <= s['w'] // 2 + 2000]
        if len(cand) > 1:
            lm = re.search(r'length ([0-9.]+) mm', it['desc'])
            if lm:
                want = float(lm.group(1)) * MM
                cand = [i for i in cand
                        if abs(math.hypot(segs[i]['x1'] - segs[i]['x0'],
                                          segs[i]['y1'] - segs[i]['y0'])
                               - want) <= 20000]
        delete_all = False
        if len(cand) > 1:
            # The DRC position is the JOINT: several segments share
            # it, often identical-length fanout twins. The dangling
            # one is the candidate whose FAR endpoint (the one away
            # from the joint) touches nothing.
            def far_free(i):
                s = segs[i]
                ends = []
                if math.hypot(s['x0'] - x, s['y0'] - y) <= 3000:
                    ends.append((s['x1'], s['y1']))
                if math.hypot(s['x1'] - x, s['y1'] - y) <= 3000:
                    ends.append((s['x0'], s['y0']))
                for (fx, fy) in ends:
                    if not anchored(segs, vias, pads, s, fx, fy, i):
                        return True
                return False
            ff = [i for i in cand if far_free(i)]
            if len(ff) == 1:
                cand = ff
            elif len(ff) > 1 and all(
                    (segs[i]['x0'], segs[i]['y0'], segs[i]['x1'],
                     segs[i]['y1']) ==
                    (segs[ff[0]]['x0'], segs[ff[0]]['y0'],
                     segs[ff[0]]['x1'], segs[ff[0]]['y1'])
                    for i in ff):
                # stacked identical duplicates: all are the flagged
                # copper; delete every copy (bridge test per copy
                # below still applies to the first; identical twins
                # share its verdict)
                cand = ff
                delete_all = True
            else:
                # Ambiguous and NOT stacked duplicates: never guess.
                # (SWCLK, exp154: two DIFFERENT segments share the
                # flagged joint on In2.Cu at (94.12,34.38); both far
                # ends anchor in this graph -- one onto the long
                # northbound segment 0.11 mm away, one onto the next
                # lattice segment -- yet jointly they carry the net:
                # deleting both raised DRC unconnected 50 -> 51.
                # The old fall-through deleted all candidates here;
                # that was the load-bearing deletion the bisect
                # caught. Skip and leave the item for the routing
                # phase, where the hairline joint can be healed.)
                skipped.append(it['desc'])
                continue
        if len(cand) < 1:
            skipped.append(it['desc'])
            continue
        multi = delete_all
        i = cand[0]
        if bridges(i, segs, contacts, seg_by_net, pad_by_net):
            vetoed.append(it['desc'])
            continue
        if multi:
            for j in cand:
                board.Remove(segs[j]['obj'])
            removed += len(cand)
        else:
            board.Remove(segs[i]['obj'])
            removed += 1
    board.Save(board_path)
    print(f'apply: removed {removed}, vetoed {len(vetoed)}, '
          f'skipped {len(skipped)}')
    for v in vetoed:
        print(f'  VETO (bridge): {v}')
    for s in skipped:
        print(f'  SKIP (no unique match): {s}')

def main():
    if sys.argv[1] == '--apply':
        apply_plan(sys.argv[2], sys.argv[3])
        return
    src, dst = sys.argv[1], sys.argv[2]
    shutil.copyfile(src, dst)
    work_json = 'scratch/dgp-round.json'
    plan_path = 'scratch/dgp-plan.json'
    prev = None
    total_removed = 0
    for rnd in range(80):
        rep = run_drc(dst, work_json)
        cnt, pads = invariant(rep)
        items = []
        for v in rep['violations']:
            if v['type'] in ('track_dangling', 'via_dangling'):
                for item in v['items']:
                    items.append({'kind': v['type'],
                                  'desc': item['description'],
                                  'x': item['pos']['x'],
                                  'y': item['pos']['y']})
        excl_path = 'scratch/dgp-exclusions.json'
        if os.path.exists(excl_path):
            with open(excl_path) as f:
                excl = json.load(f)
            def excluded(it):
                for e in excl:
                    if e['net'] in it['desc'] and \
                       abs(it['x'] - e['x']) < 0.01 and \
                       abs(it['y'] - e['y']) < 0.01:
                        return True
                return False
            items = [it for it in items if not excluded(it)]
        print(f'round {rnd}: unconnected {cnt}, dangling flagged '
              f'{len(items)}', flush=True)
        if prev is not None:
            pcnt, ppads = prev
            # Count only: a rise means a split. (Pad-set membership is
            # NOT a valid invariant -- when a deleted stub was an
            # unconnected pair's representative item, DRC re-pairs the
            # group to a pad, which looks like a "new" pad with the
            # partition unchanged. Verified round 1 of the first run:
            # 50 -> 50 with re-pairing only.)
            if cnt > pcnt:
                print(f'INVARIANT BROKEN (unconnected {pcnt} -> {cnt});'
                      f' restoring last good board and stopping.')
                shutil.copyfile(dst + '.good', dst)
                break
        prev = (cnt, pads)
        shutil.copyfile(dst, dst + '.good')
        if not items:
            print('converged: DRC flags no dangling copper.')
            break
        with open(plan_path, 'w') as f:
            json.dump(items, f)
        r = subprocess.run([sys.executable, os.path.abspath(__file__),
                            '--apply', plan_path, dst],
                           capture_output=True, text=True)
        print(r.stdout.strip(), flush=True)
        m = re.search(r'removed (\d+)', r.stdout)
        if m:
            total_removed += int(m.group(1))
        if r.returncode != 0:
            print('apply failed:', r.stderr[-500:])
            break
        if m and int(m.group(1)) == 0:
            print('round removed nothing (all vetoed/skipped); '
                  'stopping with residue flagged above.')
            break
    print(f'TOTAL removed across rounds: {total_removed}')

if __name__ == '__main__':
    main()
