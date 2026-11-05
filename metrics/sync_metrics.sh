#!/bin/sh
# Regenerate every metrics artifact derivable locally from the exported
# usage CSVs (metrics/token_series.csv, metrics/agents.csv) plus git
# history: commit_alignment.csv, token_per_message.svg,
# progress_vs_tokens inputs, cost_summary.csv.
#
# The two CSVs are an export of the Muse runtime database. No shell,
# git hook, or CI job can reach that database (see README.md,
# "Regenerating"); an agent refreshes the export, and this script does
# the rest. The parent agent refreshes the export as part of every
# merge to main, so main's metrics are never more than one merge stale.
#
# Cost when it runs: ~30 s (align_commits.py dominates). To keep worker
# commits free, it only runs in clones that opt in:
#   git config metrics.sync true        (set in the merge clone only)
# or with METRICS_SYNC=1 in the environment. Everywhere else it exits
# immediately. It never fails its caller: failures warn and exit 0.
set -u

if [ "${METRICS_SYNC:-}" != "1" ]; then
    [ "$(git config --bool metrics.sync 2>/dev/null)" = "true" ] || exit 0
fi

repo=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -f "$repo/metrics/token_series.csv" ] || exit 0
cd "$repo" || exit 0

for step in align_commits make_token_chart make_cost_summary; do
    if ! python3 "metrics/$step.py" . >/dev/null 2>&1; then
        echo "metrics sync: $step.py failed (non-fatal; export may be stale)" >&2
    fi
done

# Stage regenerated artifacts so they ride the commit that triggered
# this run (pre-commit) or the follow-up metrics commit (post-merge).
git add metrics/token_series.csv metrics/agents.csv \
        metrics/commit_alignment.csv metrics/token_per_message.svg \
        metrics/cost_summary.csv 2>/dev/null || true
exit 0
