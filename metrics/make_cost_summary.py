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
provider also gets an upper-bound row: the whole volume at its
flagship tier - an upper bound, not the headline.

Scopes match make_token_chart.py: "main chat" is this chat's root agent
(the chat-tree agent whose role is 'main agent (root of this chat...)'),
"subagents" is the rest of the chat tree, "checkpoint cron" is the
pdlvds-progress scope.

cost_summary.csv rows: per provider, one row per (scope, tier_model)
priced share, one "all" row per tier actually used, one "tier-matched"
row per scope plus the provider headline (scope=all,
tier_model=tier-matched: each scope priced at the tier its own model
share ran on, totals summing the rounded per-component costs - the
same convention as the per-tier totals), one "all" upper-bound row
(tier_model="upper bound (all flagship)"), and one "all"
cache-adjusted row (tier_model="cache-adjusted (measured share)").
Headline costs use standard (uncached) input rates.

The cache-adjusted figure applies the MEASURED new-vs-repeated split
in metrics/input_split_summary.csv (a validated estimate; per-scope
repeated share: chat tree 97.5%, checkpoint cron 87.8%, overall
96.4% of estimable input): each (scope, codename) cell's input is
billed at that cell's standard rate for the new share and at its own
tier cache-read rate for the repeated share (for the Muse row:
Wonder $0.20 / Spark $0.15 per MTok). If the summary file is absent,
the script falls back to an ASSUMED flat 95% cache share and labels
the row "cache-adjusted (assumed 95% share)". Cache-adjusted figures
are written into cost_summary.csv and also printed.

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

    # Measured repeated (cache-served) share per scope, from the
    # input-split estimate; None -> ASSUMED flat-share fallback.
    measured = None
    try:
        summ = {r['scope']: r for r in csv.DictReader(
            open(f'{repo}/metrics/input_split_summary.csv'))}
        measured = {
            'main_chat': float(
                summ['chat-tree']['est_repeated_pct_of_estimable']) / 100,
            'subagents': float(
                summ['chat-tree']['est_repeated_pct_of_estimable']) / 100,
            'checkpoint_cron': float(
                summ['checkpoint-cron']
                ['est_repeated_pct_of_estimable']) / 100,
        }
    except (OSError, KeyError, ValueError):
        measured = None

    rows = []
    report_lines = []
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
        scope_costs = {s: [0.0, 0.0] for s in SCOPES}

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
                scope_costs[scope][0] += float(r['input_cost_usd'])
                scope_costs[scope][1] += float(r['output_cost_usd'])
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
        for scope in SCOPES:
            cin, cout = scope_costs[scope]
            if cin == 0 and cout == 0:
                continue
            tin, tout = scope_totals[scope]
            rows.append({
                'provider': p['provider'], 'model': 'tier-matched',
                'scope': scope, 'input_tokens': tin,
                'output_tokens': tout,
                'input_rate_usd_per_mtok': 'mixed',
                'output_rate_usd_per_mtok': 'mixed',
                'cache_read_rate_usd_per_mtok': 'mixed',
                'input_cost_usd': f'{cin:.2f}',
                'output_cost_usd': f'{cout:.2f}',
                'total_cost_usd': f'{cin + cout:.2f}',
                'source_url': p['source_url'],
            })
        rows.append({
            'provider': p['provider'], 'model': 'tier-matched',
            'scope': 'all',
            'input_tokens': grand_in, 'output_tokens': grand_out,
            'input_rate_usd_per_mtok': 'mixed',
            'output_rate_usd_per_mtok': 'mixed',
            'cache_read_rate_usd_per_mtok': 'mixed',
            'input_cost_usd': '', 'output_cost_usd': '',
            'total_cost_usd': f'{headline:.2f}',
            'source_url': p['source_url'],
        })
        rin, rout, rcache_f = tier_rates(p, flagship)
        rows.append(cost_row(p['provider'], 'upper bound (all flagship)',
                             'all', grand_in, grand_out,
                             tier_rates(p, flagship), p['source_url']))

        # Cache-adjusted sensitivity for this provider (also printed
        # in the report lines below).
        headline_raw = (sum((tin * tier_rates(p, tier_for[c])[0]
                             + tout * tier_rates(p, tier_for[c])[1]) / 1e6
                            for c, (tin, tout) in codename_totals.items()))
        ub = (grand_in * rin + grand_out * rout) / 1e6
        if measured is not None:
            sens = upper_sens = 0.0
            for (scope, codename), (tin, tout) in cell.items():
                rin_c, rout_c, rcache_c = tier_rates(p, tier_for[codename])
                share = measured[scope]
                sens += (tin * ((1 - share) * rin_c + share * rcache_c)
                         + tout * rout_c) / 1e6
            for scope in SCOPES:
                tin = scope_totals[scope][0]
                share = measured[scope]
                upper_sens += tin * ((1 - share) * rin
                                     + share * rcache_f) / 1e6
            upper_sens += grand_out * rout / 1e6
            cache_label = 'cache-adjusted (measured share)'
            report_lines.append(
                f"{p['provider']}: headline (tier-matched) "
                f"${headline_raw:,.2f} | upper bound (all at {flagship}) "
                f"${ub:,.2f} | at the MEASURED repeated share "
                f"(chat tree {measured['main_chat']:.1%}, cron "
                f"{measured['checkpoint_cron']:.1%}): headline "
                f"${sens:,.2f}, upper bound ${upper_sens:,.2f}")
        else:
            sens = sum((tin * ((1 - ASSUMED_CACHE_SHARE)
                               * tier_rates(p, tier_for[c])[0]
                              + ASSUMED_CACHE_SHARE
                              * tier_rates(p, tier_for[c])[2])
                        + tout * tier_rates(p, tier_for[c])[1]) / 1e6
                       for c, (tin, tout) in codename_totals.items())
            eff = ((1 - ASSUMED_CACHE_SHARE) * rin
                   + ASSUMED_CACHE_SHARE * rcache_f)
            upper_sens = (grand_in * eff + grand_out * rout) / 1e6
            cache_label = 'cache-adjusted (assumed 95% share)'
            report_lines.append(
                f"{p['provider']}: headline (tier-matched) "
                f"${headline_raw:,.2f} | upper bound (all at {flagship}) "
                f"${ub:,.2f} | if {ASSUMED_CACHE_SHARE:.0%} of input "
                f"were cache-reads: headline ${sens:,.2f}, upper "
                f"bound ${upper_sens:,.2f} (assumed share; "
                f"input_split_summary.csv absent)")
        rows.append({
            'provider': p['provider'], 'model': cache_label,
            'scope': 'all',
            'input_tokens': grand_in, 'output_tokens': grand_out,
            'input_rate_usd_per_mtok': 'mixed',
            'output_rate_usd_per_mtok': 'mixed',
            'cache_read_rate_usd_per_mtok': 'mixed',
            'input_cost_usd': '', 'output_cost_usd': '',
            'total_cost_usd': f'{sens:.2f}',
            'source_url': p['source_url'],
        })

    out = f'{repo}/metrics/cost_summary.csv'
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f'wrote {out} (snapshot {snapshot_ts})')
    for line in report_lines:
        print(line)


if __name__ == '__main__':
    main()
