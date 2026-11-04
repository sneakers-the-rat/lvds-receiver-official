---
layout: default
title: Simulations
permalink: /sims/
---

## Simulation and verification results

{% for b in site.data.sims.blocks %}
### {{ b.title }}

{% if b.lines %}<pre>{% for ln in b.lines %}{{ ln }}
{% endfor %}</pre>{% else %}<p><em>result file {{ b.path }} not generated yet.</em></p>{% endif %}
{% endfor %}

### Link budget — BER vs incident power

{% if site.data.board.has_link_budget_plot %}<img src="{{ '/assets/gen/link_budget.png' | relative_url }}" alt="link budget plot">{% else %}<p><em>link budget plot render not generated — run scripts/make_fab.sh.</em></p>{% endif %}

### TIA AC response (ngspice)

{% if site.data.board.has_tia_plot %}<img src="{{ '/assets/gen/tia_ac.png' | relative_url }}" alt="TIA AC response">{% else %}<p><em>TIA AC response render not generated — run scripts/make_fab.sh.</em></p>{% endif %}

### Digital simulation

{% if site.data.board.has_digital_plot %}<img src="{{ '/assets/gen/digital_sim.png' | relative_url }}" alt="digital simulation plot">{% else %}<p><em>digital simulation plot render not generated — run scripts/make_fab.sh.</em></p>{% endif %}
