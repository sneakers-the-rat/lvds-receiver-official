---
layout: default
title: Pass history overview
permalink: /progress/
---

## Pass history overview

The whole routing campaign on one chart: for every layout pass, the
number of **unconnected nets** and the number of **clearance
violations** its board audit recorded. Success is both lines
reaching the bottom — 0 unconnected, 0 violations.

<div class="progresspanel">
<img src="{{ '/assets/gen/progress.svg' | relative_url }}" alt="Line chart per pass: unconnected nets and clearance violations, both trending toward zero">
</div>

The chart is generated at build time by
`website/_plugins/progress_chart.rb` from the passes metadata — the
same `unconnected_nets` / `clearance_violations` stats
`scripts/commit_pass.py` records from each pass's audit — so it
stays current on its own as new passes land; nothing here is
maintained by hand.

Why counts and not “% connected”: the only total-nets figure in the
early pass metadata is 112, the net count of the *original* board.
The design has since been re-schematicked — the current netlist has
223 nets (`results/partsfix/netlist-final.txt`) — so no single
denominator spans all 100+ passes, and a percentage would mix two
different boards. The honest series is the disconnected count
itself, falling to 0.

{% assign sorted_passes = site.passes | sort: "pass" %}
{% assign latest = sorted_passes | last %}
**Latest:** pass {{ latest.pass }} ({{ latest.timestamp | pacific: "%Y-%m-%d %H:%M %Z" }}) —
{{ latest.unconnected_nets }} unconnected nets,
{{ latest.clearance_violations }} clearance violations.
Per-pass detail: the [routing history]({{ '/routing/' | relative_url }})
and the pass pages in the sidebar (use the ← → buttons on a pass
page to flip between versions without losing your scroll position).
