#!/usr/bin/env python3
"""Align git commits with the token series and the board state committed at
each revision. Reproducible in-repo: reads metrics/token_series.csv and the
git history of HEAD. Board state is parsed from the audit file AS COMMITTED
at each revision (results/pcb-audit.txt) — never from later knowledge.
Usage: python3 metrics/align_commits.py [repo_root]"""
import csv, re, subprocess, sys
from datetime import datetime, timezone

repo = sys.argv[1] if len(sys.argv) > 1 else '.'

def git(*args):
    return subprocess.run(['git', '-C', repo] + list(args),
                          capture_output=True, text=True).stdout

# cumulative tokens by time from the exported series
series = []
with open(f'{repo}/metrics/token_series.csv') as f:
    for r in csv.DictReader(f):
        series.append((int(r['ts_epoch']), int(r['cum_input_tokens']),
                       int(r['cum_output_tokens']), int(r['cum_total_tokens'])))

def cum_at(ts):
    cur = (0, 0, 0)
    for t, ci, co, ct in series:
        if t <= ts:
            cur = (ci, co, ct)
        else:
            break
    return cur

log = git('log', '--format=%H%x09%ct%x09%s', 'HEAD').strip().split('\n')
out = []
for line in log:
    h, ct, subj = line.split('\t', 2)
    ct = int(ct)
    ci, co, ctot = cum_at(ct)
    # Board state: prefer an audit file this commit itself touched (attempt
    # audits live in results/audit-<attempt>.txt); else the standing audit.
    touched = [p for p in git('diff-tree', '--no-commit-id', '--name-only',
                              '-r', h).split('\n')
               if p.startswith('results/') and 'audit' in p and p.endswith('.txt')]
    audit = ''
    for p in touched + ['results/pcb-audit.txt']:
        audit = git('show', f'{h}:{p}')
        if 'unconnected nets:' in audit:
            break
    unc = vio = 'not recorded'
    m = re.search(r'unconnected nets: (\d+)', audit)
    if m: unc = m.group(1)
    m = re.search(r'clearance violations: (\d+)', audit)
    if m: vio = m.group(1)
    erc = git('show', f'{h}:results/erc-report.txt')
    m = re.search(r'Errors (\d+)', erc)
    erc_e = m.group(1) if m else 'not recorded'
    out.append([h[:12], datetime.fromtimestamp(ct, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                subj, ci, co, ctot, unc, vio, erc_e])
out.reverse()  # chronological
with open(f'{repo}/metrics/commit_alignment.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['commit', 'ts_utc', 'subject', 'cum_input_tokens', 'cum_output_tokens',
                'cum_total_tokens', 'unconnected_nets', 'clearance_violations', 'erc_errors'])
    w.writerows(out)
print(f'{len(out)} commits aligned; '
      f'{sum(1 for r in out if r[6] != "not recorded")} with board state')
