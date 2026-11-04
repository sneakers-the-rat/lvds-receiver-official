#!/usr/bin/env python3
"""Render metrics/token_per_message.svg: token use per message over time,
with project epochs annotated, plus the cumulative cost curve.

Reads metrics/token_series.csv (the exported usage records) and
metrics/agents.csv (agent -> scope, for colour-coding). White background,
dark text: the site puts the chart on a light panel by design.

Semantics (see metrics/README.md): a record aggregates ALL model requests
made while producing one message. Main-chat records are true per-message
values; a completed subagent contributes ONE record, timestamped at its
completion, totalling its whole run; checkpoint-cron records are that
job's per-run agents. Running agents have no records yet.

Epoch timestamps are commit times from `git log` (each entry names its
commit) or, for the CI-green epoch, the merge commit whose push the
recorded run built. No epoch time is invented.
Usage: python3 metrics/make_token_chart.py [repo_root]"""
import csv, sys
from datetime import datetime, timezone

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

repo = sys.argv[1] if len(sys.argv) > 1 else '.'
ROOT_AGENT = '4925d244-018c-4b4f-9fad-7b3ad78af7c1'

# (ts_epoch, label, evidence) — ts from `git log --format=%ct` for the
# named commit, verified when this chart was built (2026-11-04).
EPOCHS = [
    (1793730814, 'project start', 'commit 073664b (first commit)'),
    (1793734004, 'schematic + netlist verified', 'commit 0d6622d (stage7a)'),
    (1793734769, 'router v1', 'commit dc6a010 (v1-era router; v1/v2 committed no board)'),
    (1793739145, 'router v3', 'commit 3ac1a43 (v3 result: 57/112 nets)'),
    (1793741140, 'router v4', 'commit 41d7196 (v4 result: 67/112 nets)'),
    (1793744945, 'router v5', 'commit fb2acf7 (v5 result: 58/112 nets)'),
    (1793745981, 'ERC 0 errors', 'commit 6d66aaf (CI-fix round 4 merge; ERC 0/8 confirmed on its CI run)'),
    (1793751501, 'repair passes 1-4', 'commit 162cc87 (repair attempt 4, arc end)'),
    (1793752396, 'router v6', 'commit 9fcb471 (exact segment-clearance model)'),
    (1793754945, 'CI fully green', 'commit 0e7e532 (merge built by run 41752825210, first fully green run)'),
    (1793766803, 'fanout macro', 'commit aa04b66'),
    (1793772645, 'repair6', 'commit 67722e0 (83 -> 62 unconnected, violations unchanged)'),
    (1793779707, 'token metrics', 'commit 7a55543 (first token export)'),
]

scope = {}
with open(f'{repo}/metrics/agents.csv') as f:
    for r in csv.DictReader(f):
        scope[r['agent_id']] = r['scope']

rows = []
with open(f'{repo}/metrics/token_series.csv') as f:
    for r in csv.DictReader(f):
        rows.append((int(r['ts_epoch']), r['agent_id'],
                     int(r['input_tokens']) + int(r['output_tokens']),
                     int(r['cum_total_tokens'])))
rows.sort()

def klass(aid):
    if aid == ROOT_AGENT:
        return 'main'
    return 'sub' if scope.get(aid) == 'chat-tree' else 'cron'

COLORS = {'main': '#1f77b4', 'sub': '#d62728', 'cron': '#2ca02c'}
LABELS = {'main': 'main chat — true per-message records',
          'sub': 'subagent — one whole-run record at completion',
          'cron': 'checkpoint cron — per-run records'}

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(12.5, 8.4),
                               gridspec_kw={'hspace': 0.32})
fig.patch.set_facecolor('white')

# --- top panel: per-record gross tokens as vertical bars (log scale)
for k in ('main', 'sub', 'cron'):
    xs = [datetime.fromtimestamp(t, timezone.utc) for t, a, v, c in rows
          if klass(a) == k]
    ys = [v for t, a, v, c in rows if klass(a) == k]
    ax1.vlines(xs, 1, ys, color=COLORS[k], linewidth=1.1, alpha=0.85,
               label=LABELS[k])
    ax1.plot(xs, ys, 'o', color=COLORS[k], markersize=2.6, alpha=0.9)
ax1.set_yscale('log')
ax1.set_ylim(20, 4e7)
ax1.set_ylabel('gross tokens per record (log scale)')
ax1.grid(True, which='major', axis='y', color='#dddddd', linewidth=0.6)
ax1.grid(True, which='minor', axis='y', color='#f0f0f0', linewidth=0.4)
ax1.legend(loc='upper left', fontsize=8, framealpha=0.95)

# --- bottom panel: cumulative gross tokens
xs = [datetime.fromtimestamp(t, timezone.utc) for t, a, v, c in rows]
ax2.plot(xs, [c / 1e6 for t, a, v, c in rows], color='#333333',
         linewidth=1.6)
ax2.fill_between(xs, [c / 1e6 for t, a, v, c in rows], color='#1f77b4',
                 alpha=0.10)
ax2.set_ylabel('cumulative gross tokens (millions)')
ax2.grid(True, axis='y', color='#dddddd', linewidth=0.6)

# --- epoch annotations on both panels; labels above the top panel,
# rotated, at two staggered heights so close epochs stay readable
for i, (ts, label, _ev) in enumerate(EPOCHS):
    x = datetime.fromtimestamp(ts, timezone.utc)
    for ax in (ax1, ax2):
        ax.axvline(x, color='#888888', linestyle='--', linewidth=0.8,
                   alpha=0.75, zorder=0)
    ax1.annotate(label, xy=(x, 1.0), xycoords=('data', 'axes fraction'),
                 xytext=(0, 4 if i % 2 == 0 else 26), textcoords='offset points',
                 rotation=90, ha='center', va='bottom', fontsize=7,
                 color='#444444', annotation_clip=False)

ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %H:%M', tz=timezone.utc))
fig.autofmt_xdate(rotation=30, ha='left')

snap = rows[-1][0]
fig.suptitle('Token use per message over time — PDLVDS-RX photodiode LVDS receiver',
             fontsize=12.5, fontweight='bold', y=0.985)
fig.text(0.5, 0.008,
         f'Time axis is UTC; project span 2026-11-03 18:33Z to snapshot '
         f'{datetime.fromtimestamp(snap, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")} '
         f'({rows[-1][3]:,} gross tokens total). Gross = input + output tokens per usage record in '
         'agent.agent_message_token_usage;\nthe full context is re-sent on every model request, so this '
         'is a work meter, not a content size. Subagent records are whole-run lumps timestamped at '
         'completion;\nagents still running (build coordinator #2, this chart\'s worker) have no records '
         'yet and are excluded. Method: metrics/README.md.',
         ha='center', fontsize=7.8, color='#444444')
fig.subplots_adjust(top=0.70, bottom=0.15, left=0.075, right=0.985)
out = f'{repo}/metrics/token_per_message.svg'
fig.savefig(out, format='svg', facecolor='white')
print(f'wrote {out}: {len(rows)} records, {len(EPOCHS)} epochs, '
      f'final cumulative {rows[-1][3]:,}')
