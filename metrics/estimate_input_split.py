#!/usr/bin/env python3
"""Estimate, per usage record, how much input was NEW vs REPEATED.

ESTIMATE — not a record. The runtime's per-request table
(`agent.token_usage`) has a `cached_input_tokens` column but contains
zero rows in this deployment (verified 2026-11-04), and the populated
per-message table (`agent.agent_message_token_usage`, exported frozen
into `metrics/token_series.csv`) carries only gross input/output. So
the new/repeated split is reconstructed from the agents' own session
transcripts (~/agents/agent-<id>/sessions/*.jsonl).

Model of a transcript:
- An ordered item stream (user/developer messages, assistant messages,
  thinking, commentary, tool calls, tool outputs). A model *request*
  is inferred as one maximal run of consecutive assistant-produced
  items. A request's input is the fixed preamble (system prompt + tool
  schemas; not present in transcripts) plus every context item present
  before the run.
- An item's tokens are NEW at the first request that sends it and
  REPEATED at every later send. The preamble (the runtime-injected
  standing context: system prompt, tool schemas, standing files) is
  published under TWO bounds, because its cache behaviour is the
  estimate's biggest unknown:
  * pessimistic (the headline split, `est_new` / `est_repeated`):
    the preamble is NEW at EVERY request — every context starts
    totally fresh; the injected context is never credited to a
    cache (it is re-injected per request and the standing files are
    edited mid-run).
  * optimistic (`est_new_opt` / `est_repeated_opt`): the preamble
    is new once per session and cache-served at every later request
    — as much caching as the model allows.
  (Simplified to the two bounds 2026-11-05 at the project owner's
  direction — see metrics/README.md.)
- Fork slices: a spawned agent's transcript opens with a byte-identical
  copy (same seq, same content) of a slice of its parent's stream —
  the inherited context. Detected as a >=20-item prefix whose items
  all appear in another project transcript. The slice counts as the
  agent's starting context (new at its first own request); requests
  inside the slice were the parent's and are not counted.
- Compactions (`compaction_checkpoint` records): a compaction starts
  a NEW context window. The summary replaces all items before
  `first_kept_seq`; dropped items are gone. A prefix cache is keyed
  on the exact token prefix of a single window, so the new window's
  prefix matches nothing cached: at the first request after a
  compaction the ENTIRE surviving context — the summary AND every
  kept item — is uncached (NEW); from the second request in the new
  window on, that context accrues REPEATED normally. Identical
  content at new positions behind different preceding text is a
  different prefix and does not hit a prefix cache. (An earlier
  version of this estimator kept kept items' identities alive across
  the boundary and counted only the summary as new; that measured
  content repetition, not cache behaviour, and overstated the
  repeated share. Corrected 2026-11-04 — see metrics/README.md.)
- Single-row agents WITH compactions: the build coordinator #1's row
  reconciles only against its post-last-compaction segment (predicted
  ~1.37M + 21 x preamble vs recorded 2,224,018; the whole-run stream
  predicts ~55M, 25x the record). Such rows are therefore modelled on
  the final segment only; the compaction rule above already counts
  the segment's starting context as new at its first request, because
  the segment opens a new window. Flagged in the validation file.

Item sizes are text character counts. A chars-per-token factor and a
preamble size (tokens) are fitted PER CLASS (root / chat-tree
subagent / checkpoint-cron worker — content mixes differ enough that
a single global factor misfits the cron class by ~35%, see README)
against the recorded per-row inputs:
    recorded ~= S/cpt(class) + preamble(class) * K,
with K = inferred requests in the row and S = sum over requests of
context chars present before the request. Protocol: fit on a train
half of the agents (stratified by scope; the root agent is always in
train — 102 of 151 rows), derive per-class corrections (train median
recorded/estimated), test on the held-out half, then refit on all
agents for the published split. (Multiplicative corrections cancel in
the published proportions; they are a validation device only.) Two
size variants (thinking counted / not counted as re-sent context) are
fitted; the better on held-out data is published, both are reported.
Per row, the estimated new/repeated proportions are applied to the
row's recorded input, so published new+repeated equals the recorded
total exactly and all estimation error lives in the proportion.
Agents whose post-fit ratio falls outside [0.5, 2.0] are flagged NOT
ESTIMABLE: their rows are carried as repeated with a note, and
excluded from the fitted aggregates' numerator (kept visible as
their own summary line). The cron run/delivery agents are excluded
a priori: their session files hold the paired worker's stream, not
their own requests (their recorded rows are ~50-70k against a
~500k-token reconstructed stream, ratio ~0.12).

Outputs (in metrics/): input_split.csv, input_split_summary.csv,
input_split.svg (cumulative stacked area, Pacific-time axis, labelled
as estimate), input_split_validation.json (all fit/validation numbers
cited in README).

Usage: python3 metrics/estimate_input_split.py [repo_root]
       python3 metrics/estimate_input_split.py [repo_root] --trace AGENT_ID_PREFIX
Requires the transcripts under ~/agents (same machine as the runtime
database); base token data is the frozen metrics/token_series.csv.
"""
import csv, hashlib, json, os, sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np

repo = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '.'
TRACE = None
if '--trace' in sys.argv:
    TRACE = sys.argv[sys.argv.index('--trace') + 1]
AGENTS_DIR = os.path.expanduser('~/agents')
ROOT_AGENT = '4925d244-018c-4b4f-9fad-7b3ad78af7c1'
PT = ZoneInfo('America/Los_Angeles')
ASSISTANT_KINDS = {'thinking', 'commentary_text', 'function_call'}
SLICE_MIN = 20          # min shared-prefix length treated as a fork slice
FAIL_LO, FAIL_HI = 0.5, 2.0


def item_text_chars(item, include_thinking=True):
    t = item.get('type')
    if t == 'message':
        return len(item.get('text') or '')
    if t == 'message_parts':
        return sum(len(p.get('text') or '') for p in item.get('parts', [])
                   if p.get('type') == 'text')
    if t == 'commentary_text':
        return len(item.get('text') or '')
    if t == 'thinking':
        return len(item.get('thinking') or '') if include_thinking else 0
    if t == 'function_call':
        return len(item.get('name') or '') + len(item.get('arguments') or '')
    if t == 'function_call_output':
        out = item.get('output')
        return len(out) if isinstance(out, str) else len(json.dumps(out))
    return len(json.dumps(item))


def item_hash(item):
    return hashlib.md5(json.dumps(item, sort_keys=True).encode()).hexdigest()


def is_assistant_item(item):
    t = item.get('type')
    if t in ASSISTANT_KINDS:
        return True
    return t == 'message' and item.get('role') == 'assistant'


def to_epoch(v):
    if isinstance(v, (int, float)):
        return float(v)
    return datetime.fromisoformat(v.replace('Z', '+00:00')).timestamp()


def parse_session(path):
    items, compactions = [], []
    header_ts = None
    with open(path) as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get('type') == 'session_header':
                header_ts = to_epoch(r['created_at'])
            elif r.get('type') == 'item':
                items.append({'seq': r['seq'], 'ts': to_epoch(r['created_at']),
                              'item': r['item'], 'hash': item_hash(r['item'])})
            elif r.get('type') == 'compaction_checkpoint':
                compactions.append({
                    'checkpoint_seq': r['checkpoint_seq'],
                    'first_kept_seq': r['first_kept_seq'],
                    'summary_chars': len(r.get('summary') or ''),
                    'tokens_before': r.get('tokens_before'),
                    'tokens_after': r.get('tokens_after'),
                    'ts': to_epoch(r['created_at'])})
    items.sort(key=lambda x: x['seq'])
    return items, compactions, header_ts


def reconstruct(items, compactions, include_thinking=True,
                slice_chars=0, trace=False):
    """Walk one session's own items; return (responses, anchors).

    responses: {end_ts, c_before, new_chars, seg} — seg = number of
    compactions before the response. slice_chars = inherited context
    present before the first own item (counts as new at first send).
    """
    events = [(it['seq'], 1, it) for it in items]
    events += [(c['checkpoint_seq'], 0, c) for c in compactions]
    events.sort(key=lambda e: (e[0], e[1]))

    context = {}
    ctx_chars = slice_chars
    responses, anchors = [], []
    cur = None
    pending_new = slice_chars
    seg = 0

    def close_response():
        nonlocal cur
        if cur is not None:
            responses.append(cur)
            cur = None

    for _seq, kind, ev in events:
        if kind == 0:  # compaction
            anchors.append({'chars_before': ctx_chars,
                            'tokens_before': ev['tokens_before'],
                            'tokens_after': ev['tokens_after'],
                            'summary_chars': ev['summary_chars']})
            kept = {s: c for s, c in context.items()
                    if s >= ev['first_kept_seq']}
            context = {-1 - seg: ev['summary_chars']}
            context.update(kept)
            ctx_chars = sum(context.values())
            # New context window: the whole surviving context (summary
            # + kept items) is uncached at the first request after the
            # compaction, so it all counts as NEW there; anything still
            # pending from before the boundary is either inside
            # ctx_chars (kept) or gone (dropped). Assign, don't add.
            pending_new = ctx_chars
            anchors[-1]['chars_after'] = ctx_chars
            seg += 1
            continue
        it = ev['item']
        chars = item_text_chars(it, include_thinking)
        if is_assistant_item(it):
            if cur is None:
                cur = {'end_ts': ev['ts'], 'c_before': ctx_chars,
                       'new_chars': pending_new, 'seg': seg}
                pending_new = 0
                if trace:
                    print(f"    response start seq={ev['seq']} "
                          f"c_before={ctx_chars:,} new={cur['new_chars']:,}")
            cur['end_ts'] = max(cur['end_ts'], ev['ts'])
        else:
            close_response()
        if ev['seq'] not in context:
            context[ev['seq']] = chars
            ctx_chars += chars
            pending_new += chars
    close_response()
    return responses, anchors


def agent_sessions(agent_id):
    d = os.path.join(AGENTS_DIR, f'agent-{agent_id}', 'sessions')
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in sorted(os.listdir(d))
            if f.endswith('.jsonl')]


def klass_of(agent_id, scope):
    if agent_id == ROOT_AGENT:
        return 'root'
    return 'chat-sub' if scope == 'chat-tree' else 'cron'


def main():
    agents = {}
    with open(f'{repo}/metrics/agents.csv') as f:
        for r in csv.DictReader(f):
            agents[r['agent_id']] = r
    rows = []
    with open(f'{repo}/metrics/token_series.csv') as f:
        for r in csv.DictReader(f):
            rows.append({'ts': int(r['ts_epoch']), 'agent_id': r['agent_id'],
                         'input': int(r['input_tokens'])})
    rows_by_agent = defaultdict(list)
    for r in rows:
        rows_by_agent[r['agent_id']].append(r)
    for v in rows_by_agent.values():
        v.sort(key=lambda r: r['ts'])

    # ---- parse all transcripts; detect fork slices globally
    parsed = {}   # aid -> [(items, compactions)] per session file
    born = {}     # aid -> earliest session_header timestamp
    for aid in rows_by_agent:
        parsed[aid] = []
        for p in agent_sessions(aid):
            items, compactions, hts = parse_session(p)
            parsed[aid].append((items, compactions))
            if hts is not None:
                born[aid] = min(born.get(aid, hts), hts)
    # Fork slices exist only inside the chat tree (a spawned agent
    # inherits a slice of its parent's stream). Cron agents are
    # scheduler-spawned with no inherited context, and their runs are
    # near-identical to each other (same prompt, same commands, often
    # identical outputs), so cross-matching is restricted to chat-tree
    # agents on both sides — otherwise whole cron transcripts would be
    # misread as slices. An item counts as inherited for agent A only
    # if it also appears in a chat-tree agent BORN EARLIER than A
    # (the parent direction); the root agent is never sliced (its
    # items appear in its children's files, not the reverse).
    hash_files = defaultdict(set)   # (seq, hash) -> chat-tree agent ids
    for aid, sessions in parsed.items():
        if agents[aid]['scope'] != 'chat-tree':
            continue
        for items, _c in sessions:
            for it in items:
                hash_files[(it['seq'], it['hash'])].add(aid)
    slices = {}   # (aid, session_idx) -> (n_items, chars_by_variant)
    for aid, sessions in parsed.items():
        if agents[aid]['scope'] != 'chat-tree' or aid == ROOT_AGENT:
            continue
        for si, (items, _c) in enumerate(sessions):
            n = 0
            for it in items:
                earlier = [b for b in hash_files[(it['seq'], it['hash'])]
                           if b != aid and born.get(b, 0) < born.get(aid, 0)]
                if earlier:
                    n += 1
                else:
                    break
            if n >= SLICE_MIN:
                sl = items[:n]
                slices[(aid, si)] = (n, {
                    v: sum(item_text_chars(it['item'], v == 'with_thinking')
                           for it in sl)
                    for v in ('with_thinking', 'without_thinking')})
    if TRACE:
        for (aid, si), (n, ch) in sorted(slices.items()):
            if aid.startswith(TRACE):
                print(f'slice: agent {aid[:8]} session {si}: {n} items, '
                      f'{ch["with_thinking"]:,} chars')

    # ---- reconstruct per agent/variant; apply final-segment rule for
    # single-row agents with compactions
    rec = {}
    for aid in rows_by_agent:
        single_row = len(rows_by_agent[aid]) == 1
        rec[aid] = {}
        for variant, incl in (('with_thinking', True),
                              ('without_thinking', False)):
            responses, anchors = [], []
            for si, (items, compactions) in enumerate(parsed[aid]):
                n_sl, sl_chars = slices.get((aid, si), (0, None))
                own_items = items[n_sl:] if n_sl else items
                start_chars = sl_chars[variant] if n_sl else 0
                rs, an = reconstruct(own_items, compactions, incl,
                                     slice_chars=start_chars,
                                     trace=bool(TRACE and aid.startswith(TRACE)))
                if rs:
                    rs[0]['session_first'] = True
                if single_row and compactions and rs:
                    max_seg = max(r['seg'] for r in rs)
                    if max_seg > 0:
                        # Final segment only. No manual new-count
                        # adjustment for its starting context:
                        # reconstruct()'s compaction rule already
                        # counts the whole surviving context as new at
                        # the segment's first request (new window).
                        rs = [r for r in rs if r['seg'] == max_seg]
                responses += rs
                anchors += an
            responses.sort(key=lambda r: r['end_ts'])
            rec[aid][variant] = {'responses': responses, 'anchors': anchors}

    def row_aggregates(variant):
        agg, unassigned = {}, 0
        for aid, arows in rows_by_agent.items():
            responses = rec[aid][variant]['responses']
            ri = 0
            for resp in responses:
                while ri < len(arows) and arows[ri]['ts'] < resp['end_ts'] - 2:
                    ri += 1
                if ri >= len(arows):
                    unassigned += 1
                    continue
                d = agg.setdefault((aid, ri), {'K': 0, 'S': 0, 'new_chars': 0,
                                               'n_first': 0})
                d['K'] += 1
                d['S'] += resp['c_before']
                d['new_chars'] += resp['new_chars']
                if resp.get('session_first'):
                    d['n_first'] += 1
            for i in range(len(arows)):
                agg.setdefault((aid, i), {'K': 0, 'S': 0, 'new_chars': 0,
                                          'n_first': 0})
        return agg, unassigned

    others = sorted(a for a in rows_by_agent if a != ROOT_AGENT)
    train_agents, test_agents = {ROOT_AGENT}, set()
    by_scope = defaultdict(list)
    for a in others:
        by_scope[agents[a]['scope']].append(a)
    for _scope, lst in by_scope.items():
        for i, a in enumerate(sorted(lst)):
            (train_agents if i % 2 == 0 else test_agents).add(a)

    delivery_agents = {a for a in rows_by_agent
                       if 'run/delivery' in agents[a]['role']}
    CLASSES = ('root', 'chat-sub', 'cron')

    def unpack(coef):
        b = {c: coef[2 * i] for i, c in enumerate(CLASSES)}
        pre = {c: coef[2 * i + 1] for i, c in enumerate(CLASSES)}
        return b, pre

    def fit(agg, agent_filter):
        X, y = [], []
        for (aid, ri), d in sorted(agg.items()):
            if aid not in agent_filter or d['K'] == 0 or aid in delivery_agents:
                continue
            kls = klass_of(aid, agents[aid]['scope'])
            row = [0.0] * 6
            row[2 * CLASSES.index(kls)] = d['S']
            row[2 * CLASSES.index(kls) + 1] = d['K']
            X.append(row)
            y.append(rows_by_agent[aid][ri]['input'])
        X, y = np.array(X, float), np.array(y, float)
        try:
            from scipy.optimize import nnls
            coef, _ = nnls(X, y)
        except Exception:
            coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        return unpack(coef)

    def ratio_stats(ratios):
        r = np.array(ratios, float)
        if len(r) == 0:
            return {'n': 0, 'median': None, 'p10': None, 'p90': None,
                    'median_abs_err_pct': None}
        return {'n': int(len(r)), 'median': float(np.median(r)),
                'p10': float(np.percentile(r, 10)),
                'p90': float(np.percentile(r, 90)),
                'median_abs_err_pct': float(np.median(np.abs(r - 1)) * 100)}

    validation = {'compaction_anchors': [], 'slices': {}, 'agents': {}}
    for (aid, si), (n, ch) in slices.items():
        validation['slices'][f'{aid[:8]}#{si}'] = {
            'items': n, 'chars': ch['with_thinking']}
    seen_anchor = set()
    for aid in rows_by_agent:
        for an in rec[aid]['with_thinking']['anchors']:
            key = (aid, an['tokens_before'], an['chars_before'])
            if key in seen_anchor:
                continue
            seen_anchor.add(key)
            validation['compaction_anchors'].append({
                'agent': aid[:8], 'chars_before': an['chars_before'],
                'tokens_before': an['tokens_before'],
                'chars_per_token_before': (an['chars_before'] / an['tokens_before']
                                           if an['tokens_before'] else None),
                'chars_after': an['chars_after'],
                'tokens_after': an['tokens_after']})

    def predict(b, pre, aid, d):
        kls = klass_of(aid, agents[aid]['scope'])
        return b[kls] * d['S'] + pre[kls] * d['K']

    fits = {}
    for variant in ('with_thinking', 'without_thinking'):
        agg, unassigned = row_aggregates(variant)
        b_tr, pre_tr = fit(agg, train_agents)

        def ratios(agent_filter, b, pre, agg=agg):
            out = []
            for (aid, ri), d in agg.items():
                if aid not in agent_filter or d['K'] == 0 or aid in delivery_agents:
                    continue
                est = predict(b, pre, aid, d)
                if est > 0:
                    out.append((aid, rows_by_agent[aid][ri]['input'] / est))
            return out

        train_r = ratios(train_agents, b_tr, pre_tr)
        correction = {}
        for kls in CLASSES:
            vals = [r for a, r in train_r if klass_of(a, agents[a]['scope']) == kls]
            correction[kls] = float(np.median(vals)) if vals else 1.0
        test_r = ratios(test_agents, b_tr, pre_tr)
        test_r_corr = [r / correction[klass_of(a, agents[a]['scope'])]
                       for a, r in test_r]
        b_all, pre_all = fit(agg, set(rows_by_agent))
        agent_ratios = {}
        for (aid, ri), d in agg.items():
            if d['K'] == 0 or aid in delivery_agents:
                continue
            est = predict(b_all, pre_all, aid, d)
            if est > 0:
                agent_ratios.setdefault(aid, []).append(
                    rows_by_agent[aid][ri]['input'] / est)
        root_row_ratios = [rows_by_agent[ROOT_AGENT][ri]['input'] /
                           predict(b_all, pre_all, ROOT_AGENT, agg[(ROOT_AGENT, ri)])
                           for ri in range(len(rows_by_agent[ROOT_AGENT]))
                           if agg[(ROOT_AGENT, ri)]['K'] > 0
                           and predict(b_all, pre_all, ROOT_AGENT, agg[(ROOT_AGENT, ri)]) > 0]
        fits[variant] = {
            'agg': agg, 'unassigned': unassigned,
            'b_train': b_tr, 'pre_train': pre_tr,
            'correction_by_class': correction,
            'train_ratios': ratio_stats([r for _a, r in train_r]),
            'test_ratios_raw': ratio_stats([r for _a, r in test_r]),
            'test_ratios_corrected': ratio_stats(test_r_corr),
            'b_all': b_all, 'pre_all': pre_all,
            'agent_ratios_fullfit': {a[:8]: ratio_stats(v)
                                     for a, v in agent_ratios.items()},
            'root_row_ratios_fullfit': ratio_stats(root_row_ratios),
            'zero_k_rows': sum(1 for d in agg.values() if d['K'] == 0)}
        print(f"[{variant}] cpt(train)="
              f"{ {k: round(1 / v, 2) if v > 0 else None for k, v in b_tr.items()} } "
              f"preambles(train)={ {k: round(v) for k, v in pre_tr.items()} } "
              f"corrections={ {k: round(v, 3) for k, v in correction.items()} } "
              f"test_raw={fits[variant]['test_ratios_raw']} "
              f"test_corr={fits[variant]['test_ratios_corrected']}")

    chosen = min(fits, key=lambda v: (fits[v]['test_ratios_corrected']['median_abs_err_pct']
                                      if fits[v]['test_ratios_corrected']['median_abs_err_pct'] is not None
                                      else 1e9))
    validation['chosen_variant'] = chosen
    validation['delivery_agents_excluded_a_priori'] = sorted(
        a[:8] for a in delivery_agents)
    for v, f in fits.items():
        validation[v] = {k: f[k] for k in ('b_train', 'pre_train',
                                          'correction_by_class',
                                          'train_ratios', 'test_ratios_raw',
                                          'test_ratios_corrected', 'b_all',
                                          'pre_all', 'agent_ratios_fullfit',
                                          'root_row_ratios_fullfit',
                                          'zero_k_rows', 'unassigned')}
    print('chosen variant:', chosen)

    f = fits[chosen]
    agg, b, pre = f['agg'], f['b_all'], f['pre_all']

    # per-agent estimability from the full fit (median ratio for
    # multi-row agents, the single ratio for one-row agents)
    failed_agents = {}
    for aid in rows_by_agent:
        if aid in delivery_agents:
            failed_agents[aid] = 'delivery-agent (a priori)'
            validation['agents'][aid[:8]] = {'median_ratio_fullfit': None,
                                             'rows': 0}
            continue
        rs = [rows_by_agent[aid][ri]['input'] / predict(b, pre, aid, agg[(aid, ri)])
              for ri in range(len(rows_by_agent[aid]))
              if agg[(aid, ri)]['K'] > 0
              and predict(b, pre, aid, agg[(aid, ri)]) > 0]
        med = float(np.median(rs)) if rs else None
        validation['agents'][aid[:8]] = {'median_ratio_fullfit': med, 'rows': len(rs)}
        if med is None or med < FAIL_LO or med > FAIL_HI:
            failed_agents[aid] = med
    validation['not_estimable_agents'] = {a[:8]: m for a, m in failed_agents.items()}
    print('not-estimable agents:', validation['not_estimable_agents'])

    # ---- published split
    out_rows = []
    for (aid, ri), d in agg.items():
        row = rows_by_agent[aid][ri]
        scope = agents[aid]['scope']
        kls = klass_of(aid, scope)
        if aid in failed_agents:
            est_new, est_rep = 0, row['input']
            est_new_opt, est_rep_opt = 0, row['input']
            note = ('NOT ESTIMABLE for this agent (transcript/record '
                    f"reconciliation ratio {failed_agents[aid]}); "
                    'recorded input carried as repeated')
        elif d['K'] == 0:
            est_new, est_rep = 0, row['input']
            est_new_opt, est_rep_opt = 0, row['input']
            note = 'no requests reconstructed for this record; carried as repeated'
        else:
            est_total = predict(b, pre, aid, d)
            # Pessimistic bound: the preamble (injected standing
            # context) counts as NEW at every request (d['K'] of
            # them), never as repeated — every context starts fresh.
            new_tokens = b[kls] * d['new_chars'] + pre[kls] * d['K']
            share = min(max(new_tokens / est_total, 0.0), 1.0) if est_total > 0 else 0.0
            est_new = round(row['input'] * share)
            est_rep = row['input'] - est_new
            # Optimistic bound: the preamble counts as NEW once per
            # session (d['n_first']) and cache-served thereafter.
            new_tokens_opt = (b[kls] * d['new_chars']
                              + pre[kls] * d['n_first'])
            share_opt = min(max(new_tokens_opt / est_total, 0.0), 1.0) if est_total > 0 else 0.0
            est_new_opt = round(row['input'] * share_opt)
            est_rep_opt = row['input'] - est_new_opt
            note = ''
        out_rows.append({'ts_epoch': row['ts'],
                         'ts_utc': datetime.fromtimestamp(row['ts'], timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                         'agent_id': aid, 'scope': scope,
                         'recorded_input': row['input'],
                         'est_new': est_new, 'est_repeated': est_rep,
                         'est_new_opt': est_new_opt,
                         'est_repeated_opt': est_rep_opt,
                         'note': note})
    out_rows.sort(key=lambda r: r['ts_epoch'])
    with open(f'{repo}/metrics/input_split.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['ts_epoch', 'ts_utc', 'agent_id',
                                           'scope', 'recorded_input',
                                           'est_new', 'est_repeated',
                                           'est_new_opt', 'est_repeated_opt',
                                           'note'])
        w.writeheader()
        w.writerows(out_rows)

    summary = []
    for scope in ('chat-tree', 'checkpoint-cron', 'ALL'):
        sel = [r for r in out_rows if scope == 'ALL' or r['scope'] == scope]
        est_sel = [r for r in sel
                   if not r['note'].startswith('NOT ESTIMABLE')]
        rec_in = sum(r['recorded_input'] for r in sel)
        en = sum(r['est_new'] for r in est_sel)
        er = sum(r['est_repeated'] for r in est_sel)
        eno = sum(r['est_new_opt'] for r in est_sel)
        ero = sum(r['est_repeated_opt'] for r in est_sel)
        est_in = en + er
        summary.append({'scope': scope, 'usage_rows': len(sel),
                        'recorded_input': rec_in,
                        'estimable_recorded_input': est_in,
                        'not_estimable_input': rec_in - est_in,
                        'est_new': en, 'est_repeated': er,
                        'est_new_pct_of_estimable': round(100 * en / est_in, 2) if est_in else 0,
                        'est_repeated_pct_of_estimable': round(100 * er / est_in, 2) if est_in else 0,
                        'est_new_opt': eno, 'est_repeated_opt': ero,
                        'est_repeated_opt_pct_of_estimable': round(100 * ero / est_in, 2) if est_in else 0})
    with open(f'{repo}/metrics/input_split_summary.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)
    with open(f'{repo}/metrics/input_split_validation.json', 'w') as fh:
        json.dump(validation, fh, indent=1)

    # ---- worked-example trace (smallest one-row cron worker agent)
    cands = [(len(rec[a][chosen]['responses']), a)
             for a in rows_by_agent
             if agents[a]['scope'] == 'checkpoint-cron'
             and len(rows_by_agent[a]) == 1 and a not in delivery_agents]
    cands.sort()
    ex = cands[0][1]
    d = agg[(ex, 0)]
    est = predict(b, pre, ex, d)
    print(f"TRACE example agent {ex}: K={d['K']} S={d['S']:,} "
          f"new_chars={d['new_chars']:,} est={est:,.0f} "
          f"recorded={rows_by_agent[ex][0]['input']:,} "
          f"ratio={rows_by_agent[ex][0]['input'] / est:.3f}")
    if TRACE:
        for aid in rows_by_agent:
            if aid.startswith(TRACE):
                for ri in range(len(rows_by_agent[aid])):
                    dd = agg[(aid, ri)]
                    ee = predict(b, pre, aid, dd)
                    print(f"TRACE agent {aid} row {ri}: K={dd['K']} "
                          f"S={dd['S']:,} new_chars={dd['new_chars']:,} "
                          f"est={ee:,.0f} recorded={rows_by_agent[aid][ri]['input']:,} "
                          f"ratio={(rows_by_agent[aid][ri]['input'] / ee) if ee else None}")

    # ---- chart
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    xs = [datetime.fromtimestamp(r['ts_epoch'], PT) for r in out_rows]
    cum_new = np.cumsum([r['est_new'] for r in out_rows]) / 1e6
    cum_rep = np.cumsum([r['est_repeated'] for r in out_rows]) / 1e6
    fig, ax = plt.subplots(figsize=(12.5, 5.6))
    fig.patch.set_facecolor('white')
    ax.stackplot(xs, cum_new, cum_rep,
                 labels=['NEW input (first send of each item) — estimate',
                         'REPEATED input (context re-sent) — estimate'],
                 colors=['#2ca02c', '#1f77b4'], alpha=0.85)
    ax.plot(xs, cum_new + cum_rep, color='#333333', linewidth=1.2,
            label='total recorded input (cumulative)')
    ax.set_ylabel('cumulative input tokens (millions)')
    ax.grid(True, axis='y', color='#dddddd', linewidth=0.6)
    ax.legend(loc='upper left', fontsize=8.5, framealpha=0.95)
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2, tz=PT))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %H:%M', tz=PT))
    fig.autofmt_xdate(rotation=30, ha='left')
    fig.suptitle('ESTIMATE — input tokens split NEW vs REPEATED, cumulative\n'
                 'PDLVDS-RX photodiode LVDS receiver token metrics',
                 fontsize=12, fontweight='bold', y=0.98)
    te = f['test_ratios_corrected']
    fig.text(0.5, 0.008,
             'Time axis is Pacific (America/Los_Angeles). ESTIMATE, not a record: the per-request table '
             'with cached_input_tokens is empty in this\ndeployment, so the split is reconstructed from '
             'agent transcripts (method + validation: metrics/README.md). Held-out validation of the '
             f"underlying totals:\nmedian recorded/estimated ratio {te['median']:.2f} "
             f"(p10 {te['p10']:.2f}, p90 {te['p90']:.2f}) on {te['n']} held-out records. "
             'Published per-record new+repeated equals recorded input exactly;\nall estimation error '
             'lives in the split proportion.',
             ha='center', fontsize=7.8, color='#444444')
    fig.subplots_adjust(top=0.86, bottom=0.22, left=0.07, right=0.985)
    out_svg = f'{repo}/metrics/input_split.svg'
    fig.savefig(out_svg, format='svg', facecolor='white')
    print(f'wrote {out_svg}')
    for s in summary:
        print(s)


if __name__ == '__main__':
    main()
