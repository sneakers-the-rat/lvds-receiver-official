#!/usr/bin/env python3
"""Regenerate metrics/cost_summary.csv from the validated token snapshot.

Applies published API list prices (metrics/api_rates.json, hand-maintained
with source URLs and fetch dates) to the per-scope token totals derived
from metrics/agents.csv, and cross-checks the grand totals against the
final cumulative row of metrics/token_series.csv.

Scopes match make_token_chart.py: "main chat" is this chat's root agent
(the chat-tree agent whose role is 'main agent (root of this chat...)'),
"subagents" is the rest of the chat tree, "checkpoint cron" is the
pdlvds-progress scope.

Headline costs use standard (uncached) input rates. The script also
prints one sensitivity figure per provider: total cost if 95% of input
tokens had been billed at the provider's cache-read rate instead. The
95% share is an ASSUMED value for sensitivity only (the measured
new-vs-repeated split lives in metrics/input_split.csv when present);
it is printed, never written into cost_summary.csv.

Usage: python3 metrics/make_cost_summary.py [repo_root]
"""
import csv
import json
import sys

ASSUMED_CACHE_SHARE = 0.95


def scope_totals(repo):
    agents = list(csv.DictReader(open(f'{repo}/metrics/agents.csv')))
    roots = [r for r in agents
             if r['scope'] == 'chat-tree' and 'root of this chat' in r['role']]
    assert len(roots) == 1, f'expected exactly one chat root, got {len(roots)}'
    root_id = roots[0]['agent_id']

    scopes = {'main_chat': [0, 0], 'subagents': [0, 0], 'checkpoint_cron': [0, 0]}
    for r in agents:
        if r['agent_id'] == root_id:
            key = 'main_chat'
        elif r['scope'] == 'chat-tree':
            key = 'subagents'
        else:
            key = 'checkpoint_cron'
        scopes[key][0] += int(r['input_tokens'])
        scopes[key][1] += int(r['output_tokens'])
    scopes['all'] = [sum(v[0] for v in scopes.values()),
                     sum(v[1] for v in scopes.values())]

    # cross-check against token_series.csv final cumulative row
    series = list(csv.DictReader(open(f'{repo}/metrics/token_series.csv')))
    last = series[-1]
    assert scopes['all'][0] == int(last['cum_input_tokens']), 'input mismatch'
    assert scopes['all'][1] == int(last['cum_output_tokens']), 'output mismatch'
    return scopes, last['ts_utc']


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else '.'
    scopes, snapshot_ts = scope_totals(repo)
    rates = json.load(open(f'{repo}/metrics/api_rates.json'))['providers']

    rows = []
    for p in rates:
        for scope in ('main_chat', 'subagents', 'checkpoint_cron', 'all'):
            tin, tout = scopes[scope]
            cin = tin * p['input_usd_per_mtok'] / 1e6
            cout = tout * p['output_usd_per_mtok'] / 1e6
            rows.append({
                'provider': p['provider'],
                'model': p['model'],
                'scope': scope,
                'input_tokens': tin,
                'output_tokens': tout,
                'input_rate_usd_per_mtok': f"{p['input_usd_per_mtok']:.2f}",
                'output_rate_usd_per_mtok': f"{p['output_usd_per_mtok']:.2f}",
                'cache_read_rate_usd_per_mtok':
                    f"{p['cached_input_usd_per_mtok']:.2f}",
                'input_cost_usd': f'{cin:.2f}',
                'output_cost_usd': f'{cout:.2f}',
                'total_cost_usd': f'{cin + cout:.2f}',
                'source_url': p['source_url'],
            })

    out = f'{repo}/metrics/cost_summary.csv'
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f'wrote {out} (snapshot {snapshot_ts})')

    tin, tout = scopes['all']
    for p in rates:
        total = (tin * p['input_usd_per_mtok']
                 + tout * p['output_usd_per_mtok']) / 1e6
        eff_in_rate = ((1 - ASSUMED_CACHE_SHARE) * p['input_usd_per_mtok']
                       + ASSUMED_CACHE_SHARE * p['cached_input_usd_per_mtok'])
        sens_in = tin * eff_in_rate / 1e6
        sens_total = sens_in + tout * p['output_usd_per_mtok'] / 1e6
        print(f"{p['provider']} / {p['model']}: total ${total:,.2f} | "
              f"if {ASSUMED_CACHE_SHARE:.0%} of input were cache-reads: "
              f"input ${sens_in:,.2f}, total ${sens_total:,.2f} (assumed share)")


if __name__ == '__main__':
    main()
