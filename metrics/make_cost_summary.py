#!/usr/bin/env python3
"""Regenerate metrics/cost_summary.csv from the validated token snapshot.

Applies published API list prices (metrics/api_rates.json, hand-maintained
with source URLs and fetch dates) to the recorded token volume, split by
model codename (agents.csv `model` column, values of agent.agents.model)
and by scope, and cross-checks the totals against the final cumulative
row of metrics/token_series.csv.

Codename pricing (confirmed by the project owner, 2026-11-04):
ipnext/watermelon-v0 = Muse Wonder, ipnext/avocado-5.17-v1 = Muse
Spark (see api_rates.json `codename_map`). Every provider's row is
therefore priced per codename share, like-for-like: the watermelon
(Wonder) share at the provider's flagship tier, the avocado (Spark)
share at its step-down tier. For the Muse row those tiers are the
public models themselves (muse-wonder-1.0 / muse-spark-1.3). Each
provider also gets an `upper_bound` row: the whole volume at its
flagship tier - an upper bound, not the headline.

Scopes match make_token_chart.py: "main chat" is this chat's root agent
(the chat-tree agent whose role is 'main agent (root of this chat...)'),
"subagents" is the rest of the chat tree, "checkpoint cron" is the
pdlvds-progress scope.

cost_summary.csv rows: per provider, one row per (scope, tier_model)
priced share, one "all" headline row per tier actually used, one "all"
headline row for the provider (scope=all, tier_model=codename-mix),
and one "all" upper-bound row (tier_model=<flagship> (upper bound)).
Headline costs use standard (uncached) input rates.

The script also prints one sensitivity figure per provider: total cost
if 95% of input tokens had been billed at cache-read rates instead.
Per codename share, each share's own tier cache rate is used (for the
Muse row: Wonder $0.20 / Spark $0.15 per MTok). The 95% share is an
ASSUMED value for sensitivity only (the measured new-vs-repeated
split lives in metrics/input_split.csv when present); it is printed,
never written into cost_summary.csv.

Usage: python3 metrics/make_cost_summary.py [repo_root]
"""
import csv
import json
import sys

ASSUMED_CACHE_SHARE = 0.95
SCOPES = ('main_chat', 'subagents', 'checkpoint_cron')
RATES_FILE_VERSION = 2


def load_agents(repo):
    agents = list(csv.DictReader(open(f'{repo}/metrics/agents.csv')))
    assert 'model' in agents[0], 'agents.csv lacks the model column'
    roots = [r for r in agents
             if r['scope'] == 'chat-tree' and 'root of this chat' in r['role']]
    assert len(roots) == 1, f'expected exactly one chat root, got {len(roots)}'
    return agents, roots[0]['agent_id']


def scope_of(agent, root_id):
    if agent['agent_id'] == root_id:
        return 'main_chat'
    if agent['scope'] == 'chat-tree':
        return 'subagents'
    return 'checkpoint_cron'


def cross_check(repo, scope_totals, codename_totals):
    """Grand totals and codename split must both reconcile with the
    final cumulative row of token_series.csv."""
    series = list(csv.DictReader(open(f'{repo}/metrics/token_series.csv')))
    last = series[-1]
    tin, tout = int(last['cum_input_tokens']), int(last['cum_output_tokens'])
    assert [sum(v[0] for v in scope_totals.values()),
            sum(v[1] for v in scope_totals.values())] == [tin, tout], \
        'scope totals mismatch vs token_series.csv'
    assert [sum(v[0] for v in codename_totals.values()),
            sum(v[1] for v in codename_totals.values())] == [tin, tout], \
        'codename split does not sum to the snapshot totals'
    return tin, tout, last['ts_utc']


def tier_rates(entry, tier_model):
    if tier_model == entry['model']:
        return (entry['input_usd_per_mtok'], entry['output_usd_per_mtok'],
                entry['cached_input_usd_per_mtok'])
    assert tier_model == entry['stepdown_model'], tier_model
    return (entry['stepdown_input_usd_per_mtok'],
            entry['stepdown_output_usd_per_mtok'],
            entry['stepdown_cached_input_usd_per_mtok'])


def cost_row(provider, tier_model, scope_label, tin, tout, rates, source):
    rin, rout, rcache = rates
    cin, cout = tin * rin / 1e6, tout * rout / 1e6
    return {
        'provider': provider,
        'model': tier_model,
        'scope': scope_label,
        'input_tokens': tin,
        'output_tokens': tout,
        'input_rate_usd_per_mtok': f'{rin:.2f}',
        'output_rate_usd_per_mtok': f'{rout:.2f}',
        'cache_read_rate_usd_per_mtok': f'{rcache:.2f}',
        'input_cost_usd': f'{cin:.2f}',
        'output_cost_usd': f'{cout:.2f}',
        'total_cost_usd': f'{cin + cout:.2f}',
        'source_url': source,
    }


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else '.'
    agents, root_id = load_agents(repo)

    scope_totals = {s: [0, 0] for s in SCOPES}
    codename_totals = {}
    cell = {}
    for a in agents:
        scope, codename = scope_of(a, root_id), a['model']
        tin, tout = int(a['input_tokens']), int(a['output_tokens'])
        scope_totals[scope][0] += tin
        scope_totals[scope][1] += tout
        codename_totals.setdefault(codename, [0, 0])
        codename_totals[codename][0] += tin
        codename_totals[codename][1] += tout
        key = (scope, codename)
        cell.setdefault(key, [0, 0])
        cell[key][0] += tin
        cell[key][1] += tout
    grand_in, grand_out, snapshot_ts = cross_check(
        repo, scope_totals, codename_totals)

    rates_doc = json.load(open(f'{repo}/metrics/api_rates.json'))
    assert rates_doc.get('version') == RATES_FILE_VERSION, \
        'api_rates.json is not the tier-pair (v2) layout'
    codename_map = rates_doc['codename_map']['map']

    rows = []
    for p in rates_doc['providers']:
        flagship, stepdown = p['model'], p['stepdown_model']
        # Map this provider's two tiers to codenames by role: the
        # codename the map resolves to a Wonder public model takes the
        # flagship tier, the one resolved to a Spark public model the
        # step-down tier (like-for-like across providers).
        muse_flagship_public = rates_doc['providers'][0]['model']
        tier_for = {}
        codename_for_tier = {}
        for codename, public in codename_map.items():
            tier = flagship if public == muse_flagship_public else stepdown
            tier_for[codename] = tier
            codename_for_tier[tier] = codename
        tier_totals = {flagship: [0.0, 0.0], stepdown: [0.0, 0.0]}

        for scope in SCOPES:
            for tier in (flagship, stepdown):
                tin, tout = cell.get(
                    (scope, codename_for_tier[tier]), [0, 0])
                if tin == 0 and tout == 0:
                    continue
                r = cost_row(p['provider'], tier, scope, tin, tout,
                             tier_rates(p, tier), p['source_url'])
                rows.append(r)
                tier_totals[tier][0] += float(r['input_cost_usd'])
                tier_totals[tier][1] += float(r['output_cost_usd'])
        headline = 0.0
        for tier in (flagship, stepdown):
            cin, cout = tier_totals[tier]
            if cin == 0 and cout == 0:
                continue
            tin, tout = codename_totals[codename_for_tier[tier]]
            rin, rout, rcache = tier_rates(p, tier)
            rows.append({
                'provider': p['provider'], 'model': tier,
                'scope': 'all', 'input_tokens': tin,
                'output_tokens': tout,
                'input_rate_usd_per_mtok': f'{rin:.2f}',
                'output_rate_usd_per_mtok': f'{rout:.2f}',
                'cache_read_rate_usd_per_mtok': f'{rcache:.2f}',
                'input_cost_usd': f'{cin:.2f}',
                'output_cost_usd': f'{cout:.2f}',
                'total_cost_usd': f'{cin + cout:.2f}',
                'source_url': p['source_url'],
            })
            headline += cin + cout
        rows.append({
            'provider': p['provider'], 'model': 'codename-mix',
            'scope': 'all',
            'input_tokens': grand_in, 'output_tokens': grand_out,
            'input_rate_usd_per_mtok': 'mixed',
            'output_rate_usd_per_mtok': 'mixed',
            'cache_read_rate_usd_per_mtok': 'mixed',
            'input_cost_usd': '', 'output_cost_usd': '',
            'total_cost_usd': f'{headline:.2f}',
            'source_url': p['source_url'],
        })
        rin, rout, _ = tier_rates(p, flagship)
        rows.append(cost_row(p['provider'], f'{flagship} (upper bound)',
                             'all', grand_in, grand_out,
                             tier_rates(p, flagship), p['source_url']))

    out = f'{repo}/metrics/cost_summary.csv'
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f'wrote {out} (snapshot {snapshot_ts})')

    # sensitivity (printed only): 95% of each codename share's input at
    # that share's tier cache-read rate
    muse_flagship_public = rates_doc['providers'][0]['model']
    for p in rates_doc['providers']:
        flagship, stepdown = p['model'], p['stepdown_model']
        headline = sens = 0.0
        for codename, (tin, tout) in codename_totals.items():
            tier = flagship if codename_map[codename] == \
                muse_flagship_public else stepdown
            rin, rout, rcache = tier_rates(p, tier)
            headline += (tin * rin + tout * rout) / 1e6
            eff = ((1 - ASSUMED_CACHE_SHARE) * rin
                   + ASSUMED_CACHE_SHARE * rcache)
            sens += (tin * eff + tout * rout) / 1e6
        rin, rout, rcache = tier_rates(p, flagship)
        eff = ((1 - ASSUMED_CACHE_SHARE) * rin
               + ASSUMED_CACHE_SHARE * rcache)
        upper_sens = (grand_in * eff + grand_out * rout) / 1e6
        ub = (grand_in * rin + grand_out * rout) / 1e6
        print(f"{p['provider']}: headline (codename-priced) "
              f"${headline:,.2f} | upper bound (all at {flagship}) "
              f"${ub:,.2f} | if {ASSUMED_CACHE_SHARE:.0%} of input were "
              f"cache-reads: headline ${sens:,.2f}, upper bound "
              f"${upper_sens:,.2f} (assumed share)")


if __name__ == '__main__':
    main()
