---
layout: default
title: Routing history
permalink: /routing/
---

## Routing history

**Chart:** the [pass history overview]({{ '/progress/' | relative_url }})
plots unconnected nets and clearance violations across all passes —
both series falling to 0 is the finish line. On a pass page, the
← → buttons stick to the bottom of the content area (or use the
left/right arrow keys) to flip between versions; the page you land
on re-aligns itself on the board image you were looking at, so two
versions' renders line up for comparison even though each pass's
text above them is a different length.

Every layout pass, in order — one counter for the whole project, including the passes that failed. Strategy changes are the changelog lines under each pass number. Passes live in `history/` in the repository, one directory per pass, committed by `scripts/commit_pass.py` at the moment the board state existed; each pass also has its own page (below, and in the sidebar) carrying the renders committed with it — those committed image files, never re-rendered. The renders are route-only: tracks, vias and pads, with zone fills (the opaque GND pours) removed — each snapshot is exported from a temp copy of the board with its zones deleted, so every layer's routes stay visible. All renders are presented light-on-dark — bright layer colours on dark panels, the presentation the project owner asked for; drill holes are drawn in the panel tone so they read as holes in the pads around them. Runs whose boards were never committed hold no pass number — they are listed as gaps in `history/PASSES.md`.

{% assign sorted_passes = site.passes | sort: "pass" %}
{% for p in sorted_passes %}
<div class="attempt" markdown="0">
<h3><a href="{{ p.url | relative_url }}">Pass {{ p.pass }}</a></h3>
<p>{{ p.timestamp | pacific: "%Y-%m-%d %H:%M %Z" }} ({{ p.timestamp }} UTC) · commit <code>{{ p.short_hash }}</code> · {% if p.adopted %}<span class="badge pass">ADOPTED</span>{% else %}<span class="badge fail">NOT ADOPTED</span>{% endif %}</p>
<p>{{ p.description }}</p>
<table><tbody>
<tr><td>Nets fully routed</td><td>{% if p.nets_routed %}{{ p.nets_routed }}{% if p.nets_total %} of {{ p.nets_total }}{% endif %}{% else %}not recorded{% endif %}</td></tr>
<tr><td>Unconnected nets</td><td>{{ p.unconnected_nets | default: "not recorded" }}</td></tr>
<tr><td>Clearance violations</td><td>{{ p.clearance_violations | default: "not recorded" }}</td></tr>
<tr><td>Audit verdict</td><td>{{ p.audit_verdict | default: "not recorded" }}</td></tr>
</tbody></table>
<p><a href="{{ p.url | relative_url }}">Pass {{ p.pass }} renders and full record →</a></p>
</div>
{% endfor %}
