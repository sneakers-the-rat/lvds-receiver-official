#!/usr/bin/env python3
"""Render metrics/token_per_message.svg: token use per message over time,
with project epochs annotated, plus the cumulative cost stacked by scope.

Reads metrics/token_series.csv (the exported usage records) and
metrics/agents.csv (agent -> scope, for colour-coding). White background,
dark text: the site puts the chart on a light panel by design.

Semantics (see metrics/README.md): a record aggregates ALL model requests
made while producing one message. Main-chat records are true per-message
values; a completed subagent contributes ONE record, timestamped at its
completion, totalling its whole run; checkpoint-cron records are that
job's per-run agents. Running agents have no records yet.

All plotted times are Pacific time (America/Los_Angeles); the CSVs keep
epoch seconds, so this is display-only (user directive, 2026-11-04).

Bottom panel: cumulative tokens as a six-layer stack. Each scope keeps
the top panel's hue (main chat / subagents / checkpoint cron); within a
hue the DARKER shade is input tokens and the LIGHTER shade is output
tokens, and a scope's two layers sit adjacent, so each scope's
cumulative subtotal is the height of its colour band and the top edge
of the stack is the grand cumulative total. The script asserts both
properties against the CSVs before writing the SVG.

Epoch timestamps are commit times from `git log` (each entry names its
commit) or, for the CI-green epoch, the merge commit whose push the
recorded run built. No epoch time is invented.
Usage: python3 metrics/make_token_chart.py [repo_root]"""
import csv, sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb

repo = sys.argv[1] if len(sys.argv) > 1 else '.'
ROOT_AGENT = '4925d244-018c-4b4f-9fad-7b3ad78af7c1'
PT = ZoneInfo('America/Los_Angeles')

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
agent_totals = {}
with open(f'{repo}/metrics/agents.csv') as f:
    for r in csv.DictReader(f):
        scope[r['agent_id']] = r['scope']
        agent_totals[r['agent_id']] = (int(r['input_tokens']),
                                        int(r['output_tokens']))

def klass(aid):
    if aid == ROOT_AGENT:
        return 'main'
    return 'sub' if scope.get(aid) == 'chat-tree' else 'cron'

# records: (ts_epoch, klass, input_tokens, output_tokens)
recs = []
final_cum_total = None
with open(f'{repo}/metrics/token_series.csv') as f:
    for r in csv.DictReader(f):
        recs.append((int(r['ts_epoch']), klass(r['agent_id']),
                     int(r['input_tokens']), int(r['output_tokens'])))
        final_cum_total = int(r['cum_total_tokens'])
recs.sort()

COLORS = {'main': '#1f77b4', 'sub': '#d62728', 'cron': '#2ca02c'}
LABELS = {'main': 'main chat — true per-message records',
          'sub': 'subagent — one whole-run record at completion',
          'cron': 'checkpoint cron — per-run records'}
SHORT = {'main': 'main chat', 'sub': 'subagents', 'cron': 'checkpoint cron'}

def darken(hexcolor, f=0.68):
    r, g, b = to_rgb(hexcolor)
    return (r * f, g * f, b * f)

def lighten(hexcolor, f=0.55):
    r, g, b = to_rgb(hexcolor)
    return (r + (1 - r) * f, g + (1 - g) * f, b + (1 - b) * f)

# --- stacked cumulative layers: (klass, kind) in stacking order, a
# scope's input (dark) directly below its output (light).
LAYERS = [(k, kind) for k in ('main', 'sub', 'cron')
          for kind in ('input', 'output')]
times = sorted({t for t, _, _, _ in recs})
by_time = defaultdict(list)
for t, k, i, o in recs:
    by_time[t].append((k, i, o))
running = {layer: 0 for layer in LAYERS}
layer_series = {layer: [] for layer in LAYERS}
for t in times:
    for k, i, o in by_time[t]:
        running[(k, 'input')] += i
        running[(k, 'output')] += o
    for layer in LAYERS:
        layer_series[layer].append(running[layer])

# --- verify the stack against the CSVs before drawing anything:
# the top of the stack must equal the CSV's final cumulative total, and
# each scope's two layers must equal that scope's agents.csv totals.
layer_final = {layer: layer_series[layer][-1] for layer in LAYERS}
assert sum(layer_final.values()) == final_cum_total, (
    f'stack top {sum(layer_final.values()):,} != CSV final cumulative '
    f'{final_cum_total:,}')
for k in ('main', 'sub', 'cron'):
    ag_in = sum(v[0] for aid, v in agent_totals.items() if klass(aid) == k)
    ag_out = sum(v[1] for aid, v in agent_totals.items() if klass(aid) == k)
    assert layer_final[(k, 'input')] == ag_in, (k, 'input')
    assert layer_final[(k, 'output')] == ag_out, (k, 'output')

def pt(ts):
    return datetime.fromtimestamp(ts, PT)

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(12.5, 9.0),
                               gridspec_kw={'hspace': 0.34})
fig.patch.set_facecolor('white')

# --- top panel: per-record gross tokens as vertical bars (log scale)
for k in ('main', 'sub', 'cron'):
    xs = [pt(t) for t, kk, i, o in recs if kk == k]
    ys = [i + o for t, kk, i, o in recs if kk == k]
    ax1.vlines(xs, 1, ys, color=COLORS[k], linewidth=1.1, alpha=0.85,
               label=LABELS[k])
    ax1.plot(xs, ys, 'o', color=COLORS[k], markersize=2.6, alpha=0.9)
ax1.set_yscale('log')
ax1.set_ylim(20, 4e7)
ax1.set_ylabel('gross tokens per record (log scale)')
ax1.grid(True, which='major', axis='y', color='#dddddd', linewidth=0.6)
ax1.grid(True, which='minor', axis='y', color='#f0f0f0', linewidth=0.4)
ax1.legend(loc='upper left', fontsize=8, framealpha=0.95)

# --- bottom panel: cumulative tokens stacked by scope x input/output
xs = [pt(t) for t in times]
base = [0.0] * len(times)
for k, kind in LAYERS:
    ys = [v / 1e6 for v in layer_series[(k, kind)]]
    top = [b + y for b, y in zip(base, ys)]
    color = darken(COLORS[k]) if kind == 'input' else lighten(COLORS[k])
    ax2.fill_between(xs, base, top, step='post', color=color,
                     label=f'{SHORT[k]} — {kind}')
    base = top
ax2.step(xs, base, where='post', color='#333333', linewidth=1.2)
ax2.annotate(f'{final_cum_total / 1e6:,.1f}M total',
             xy=(xs[-1], base[-1]), xytext=(-6, 6),
             textcoords='offset points', ha='right', fontsize=8.5,
             color='#333333', fontweight='bold')
ax2.set_ylabel('cumulative tokens (millions)')
ax2.set_xlabel('Pacific time (America/Los_Angeles)')
ax2.grid(True, axis='y', color='#dddddd', linewidth=0.6)
ax2.legend(loc='upper left', fontsize=8, framealpha=0.95, ncol=2,
           title='colour = scope · darker shade = input · '
                 'lighter shade = output')
ax2.get_legend().get_title().set_fontsize(8)

# --- epoch annotations on both panels; labels above the top panel,
# rotated, at two staggered heights so close epochs stay readable
for i, (ts, label, _ev) in enumerate(EPOCHS):
    x = pt(ts)
    for ax in (ax1, ax2):
        ax.axvline(x, color='#888888', linestyle='--', linewidth=0.8,
                   alpha=0.75, zorder=0)
    ax1.annotate(label, xy=(x, 1.0), xycoords=('data', 'axes fraction'),
                 xytext=(0, 4 if i % 2 == 0 else 26), textcoords='offset points',
                 rotation=90, ha='center', va='bottom', fontsize=7,
                 color='#444444', annotation_clip=False)

ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2, tz=PT))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %H:%M', tz=PT))
fig.autofmt_xdate(rotation=30, ha='left')

snap = recs[-1][0]
tot_in = sum(layer_final[(k, 'input')] for k in ('main', 'sub', 'cron'))
tot_out = sum(layer_final[(k, 'output')] for k in ('main', 'sub', 'cron'))
fig.suptitle('Token use per message over time — PDLVDS-RX photodiode LVDS receiver',
             fontsize=12.5, fontweight='bold', y=0.985)
fig.text(0.5, 0.008,
         f'Time axis is Pacific time (America/Los_Angeles); project span '
         f'{pt(recs[0][0]).strftime("%Y-%m-%d %H:%M")} PT to snapshot '
         f'{pt(snap).strftime("%Y-%m-%d %H:%M")} PT '
         f'({datetime.fromtimestamp(snap, timezone.utc).strftime("%H:%M")} UTC) — '
         f'{final_cum_total:,} gross tokens total.\n'
         'Bottom panel stacks cumulative tokens by scope: each scope keeps its top-panel colour, the darker\n'
         'shade is input and the lighter shade is output, and the top edge of the stack is the grand total.\n'
         f'Output is only {tot_out:,} tokens ({100.0 * tot_out / final_cum_total:.1f}% of gross), so the light layers are thin. '
         'Gross = input + output per usage\n'
         'record in agent.agent_message_token_usage; the full context is re-sent on every model request, so this is a work\n'
         'meter, not a content size. Subagent records are whole-run lumps timestamped at completion; agents still running\n'
         '(build coordinator #2, this chart\'s worker) have no records yet and are excluded. Method: metrics/README.md.',
         ha='center', fontsize=7.8, color='#444444')
fig.subplots_adjust(top=0.70, bottom=0.21, left=0.075, right=0.985)
out = f'{repo}/metrics/token_per_message.svg'
fig.savefig(out, format='svg', facecolor='white')
print(f'wrote {out}: {len(recs)} records, {len(EPOCHS)} epochs')
for k in ('main', 'sub', 'cron'):
    print(f'  {SHORT[k]}: input {layer_final[(k, "input")]:,} + '
          f'output {layer_final[(k, "output")]:,} = '
          f'{layer_final[(k, "input")] + layer_final[(k, "output")]:,}')
print(f'  stack top (grand total): {sum(layer_final.values()):,} '
      f'== CSV final cum_total_tokens {final_cum_total:,} ✓')
