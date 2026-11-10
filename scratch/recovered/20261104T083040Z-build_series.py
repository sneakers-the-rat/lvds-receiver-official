#!/usr/bin/env python3
"""Merge the two raw DB exports (chat tree + cron) into metrics/token_series.csv
and metrics/agents.csv. Verifies row counts and sums against the independent
bounded aggregate probe queries run against muse.db before the export:
  chat: 117 rows, in 117339932, out 550188
  cron:  34 rows, in  15914052, out 116416
Bound: created_at <= 1793780974 (2026-11-04T08:29:34Z)."""
import csv, sys
from datetime import datetime, timezone

REPO = '/home/hatch/workspace/pdlvds-cifix'
EXPECT = {'chat': (117, 117339932, 550188), 'cron': (34, 15914052, 116416)}

def load(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                ts, aid, i, o = line.split(',')
                rows.append((int(ts), aid, int(i), int(o)))
    return rows

chat = load('/tmp/tok_chat.csv')
cron = load('/tmp/tok_cron.csv')
for name, rows in (('chat', chat), ('cron', cron)):
    n, si, so = len(rows), sum(r[2] for r in rows), sum(r[3] for r in rows)
    assert (n, si, so) == EXPECT[name], f'{name}: got {(n, si, so)} want {EXPECT[name]}'
    print(f'{name}: {n} rows, in={si}, out={so} — matches DB probe')

chat_ids = {r[1] for r in chat}
cron_ids = {r[1] for r in cron}
assert not (chat_ids & cron_ids), 'scope overlap!'

allrows = sorted(chat + cron, key=lambda r: (r[0], r[1]))
ci = co = 0
with open(f'{REPO}/metrics/token_series.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['ts_epoch', 'ts_utc', 'agent_id', 'input_tokens', 'output_tokens',
                'cum_input_tokens', 'cum_output_tokens', 'cum_total_tokens'])
    for ts, aid, i, o in allrows:
        ci += i; co += o
        w.writerow([ts, datetime.fromtimestamp(ts, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    aid, i, o, ci, co, ci + co])
print(f'token_series.csv: {len(allrows)} rows; totals in={ci} out={co} gross={ci+co}')

# ---- agents.csv: preserve old metadata, refresh totals, add new agents ----
old = {}
with open(f'{REPO}/metrics/agents.csv') as f:
    for r in csv.DictReader(f):
        old[r['agent_id']] = r

from collections import defaultdict
tot = defaultdict(lambda: [0, 0, 0, None, None])
for ts, aid, i, o in allrows:
    t = tot[aid]
    t[0] += 1; t[1] += i; t[2] += o
    t[3] = ts if t[3] is None else min(t[3], ts)
    t[4] = ts if t[4] is None else max(t[4], ts)

def iso(ts):
    return '' if ts is None else datetime.fromtimestamp(ts, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

NEW_META = {
    '0088c73b-1d16-42f6-9f1a-5ba99e7c4865': ('chat-tree', 'token-graph worker (per-message chart + site section)',
        'RUNNING at snapshot: no usage row yet (rows land at completion) - excluded from totals'),
    '68408d59-f6ed-4708-90a9-be0e83fac647': ('checkpoint-cron', 'pdlvds-progress checkpoint worker (cron job pdlvds-progress)',
        'run scheduled 2026-11-04T08:09:16Z'),
    'e0d7ee14-2a58-4ea5-b726-45c333173e8b': ('checkpoint-cron', 'pdlvds-progress run/delivery agent (cron job pdlvds-progress)',
        'run scheduled 2026-11-04T08:09:16Z'),
}
order = list(old.keys())
for aid in NEW_META:
    if aid not in order:
        order.append(aid)
for aid in tot:
    if aid not in order:
        order.append(aid)
        print('WARNING: agent in series without metadata:', aid)

CHANGES = {
    '60e10a13-9832-4f5a-b861-c8112a74866b': {'role': 'token-metrics worker (first export: series, census, alignment, methodology)',
        'notes': 'completed after the 2026-11-04T08:04Z snapshot; its usage row landed 2026-11-04T08:09:38Z and is included here'},
}

rows_out = []
for aid in order:
    meta = old.get(aid)
    scope = meta['scope'] if meta else NEW_META[aid][0]
    role = meta['role'] if meta else NEW_META[aid][1]
    notes = meta['notes'] if meta else NEW_META[aid][2]
    if aid in CHANGES:
        role = CHANGES[aid].get('role', role)
        notes = CHANGES[aid].get('notes', notes)
    n, si, so, fts, lts = tot.get(aid, [0, 0, 0, None, None])
    rows_out.append([aid, scope, role, n, si, so, iso(fts), iso(lts), notes])

with open(f'{REPO}/metrics/agents.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['agent_id', 'scope', 'role', 'usage_rows', 'input_tokens', 'output_tokens',
                'first_row_utc', 'last_row_utc', 'notes'])
    w.writerows(rows_out)
n_with = sum(1 for r in rows_out if r[3] > 0)
print(f'agents.csv: {len(rows_out)} agents listed, {n_with} with usage rows')
print('per-scope check:')
for scope in ('chat-tree', 'checkpoint-cron'):
    sel = [r for r in rows_out if r[1] == scope]
    print(f'  {scope}: {len(sel)} agents, rows={sum(r[3] for r in sel)}, '
          f'in={sum(r[4] for r in sel)}, out={sum(r[5] for r in sel)}')
