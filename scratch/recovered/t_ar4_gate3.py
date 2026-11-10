#!/usr/bin/env python3
"""Gate with statics mods incl. via rips/adds. Usage:
  t_ar4_gate3.py board.kicad_pcb mods.json plan.json
mods: {"rips": [[kind,net,x,y],...], "adds": [plan entries...],
       "rip_vias": [[net,x,y],...], "add_vias": [[net,x,y],...]}
Rips/adds of vias are applied to the statics so gates see the new field."""
import sys, json
sys.path.insert(0, 'scratch/work/ai'); sys.path.insert(0, 'scratch/work/ar')
import t_ai_lib as L
import pcbnew

board_path, mods_path, plan_path = sys.argv[1], sys.argv[2], sys.argv[3]
mods = json.load(open(mods_path))
plan = json.load(open(plan_path))
b = pcbnew.LoadBoard(board_path)
items = L.load_items(b)
rips = [tuple(r) for r in mods.get('rips', [])]
rip_vias = [tuple(r) for r in mods.get('rip_vias', [])]
n0 = len(items)
items = [it for it in items if not (
    (it[0] in ('seg', 'arc') and (it[1], it[3], it[4]) in rips) or
    (it[0] in ('seg', 'arc') and (it[1], it[5], it[6]) in rips) or
    (it[0] == 'via' and (it[1], it[3], it[4]) in rip_vias))]
print(f"statics rips applied: {n0-len(items)} (expected {len(rips)+len(rip_vias)})")
adds = [tuple(a) for a in mods.get('adds', [])]
add_vias = [tuple(v) for v in mods.get('add_vias', [])]
alladds = [('seg',)+a[1:] for a in adds] + \
          [('via', v[0], None, v[1], v[2], 0.25, None) for v in add_vias]
fails = 0
for src, group in (('MOD', alladds), ('PLAN', [tuple(p) for p in plan])):
    for i, a in enumerate(group):
        worst = 9e9; wdesc = ''
        for li in ((0, 1, 2) if a[0] == 'via' else (a[2],)):
            for it in items:
                if it[1] == a[1]:
                    continue
                m, d = L.entry_margin(a, li, it)
                if m is not None and m < worst:
                    worst, wdesc = m, d
        ok = worst >= -0.001
        if not ok: fails += 1
        print(('OK ' if ok else 'FAIL'), f'[{src}{i}]', a[0], a[1],
              f'L{a[2]}' if a[0] == 'seg' else '',
              (f'({a[3]},{a[4]})->({a[5]},{a[6]})' if a[0] == 'seg'
               else f'({a[3]},{a[4]})'),
              f'w{a[7]}' if a[0] == 'seg' else '',
              f'worst {worst:+.3f}' if a[0] == 'via' else f'{worst:+.3f}',
              'vs', wdesc)
        items.append(a)
print(f'TOTAL {len(alladds)+len(plan)} items, {fails} FAILS')
