---
layout: default
title: Token usage
permalink: /tokens/
---

## Token usage

{% if site.data.tokens.available %}
**{{ site.data.tokens.total_gross | number_delimiter }} gross tokens** ({{ site.data.tokens.total_in | number_delimiter }} input + {{ site.data.tokens.total_out | number_delimiter }} output) across {{ site.data.tokens.n_messages }} recorded messages from {{ site.data.tokens.n_agents_with }} agents ({{ site.data.tokens.n_agents_scope }} in project scope), snapshot {{ site.data.tokens.snapshot_utc | pacific: "%Y-%m-%d %H:%M %Z" }} ({{ site.data.tokens.snapshot_utc }} UTC).

{% if site.data.tokens.has_chart %}<div class="tokenpanel"><img src="{{ '/assets/gen/token_per_message.svg' | relative_url }}" alt="token use per message over time, annotated with project epochs"></div>{% else %}<p><em>per-message chart not generated — run metrics/make_token_chart.py.</em></p>{% endif %}

| Scope | Input | Output | Gross |
|---|---|---|---|
{% for s in site.data.tokens.scopes %}| {{ s.label }} | {{ s.input | number_delimiter }} | {{ s.output | number_delimiter }} | {{ s.gross | number_delimiter }} |
{% endfor %}

Records are the runtime's per-message token-usage rows: each row aggregates every model request made while producing one message — the full context is re-sent on every request, so input dominates and the totals are a work meter, not a content size. Main-chat rows are true per-message values; a subagent appears as a single whole-run record timestamped at its completion. Agents still running have no rows yet, so the snapshot understates the final total. Full method, the exact SQL and all caveats: [metrics/README.md]({{ '/downloads/token-metrics-README.md' | relative_url }}).

{% if site.data.tokens.has_progress %}Board progress against cumulative tokens: [progress_vs_tokens.svg]({{ '/assets/gen/progress_vs_tokens.svg' | relative_url }}) (unconnected nets and clearance violations from the audit file as committed at each revision).{% endif %}
{% else %}
<p><em>Token export not present in this checkout — see metrics/README.md for the export procedure.</em></p>
{% endif %}
{% if site.data.costs and site.data.costs.available %}

## Cost summary

Breakdown of API costs at list-price equivalents, computed from the same per-message token records (method and price basis: [metrics/README.md]({{ '/downloads/token-metrics-README.md' | relative_url }})).

| {% for h in site.data.costs.header %}{{ h }} | {% endfor %}
|{% for h in site.data.costs.header %}---|{% endfor %}
{% for row in site.data.costs.rows %}| {% for cell in row %}{{ cell }} | {% endfor %}
{% endfor %}
{% endif %}
