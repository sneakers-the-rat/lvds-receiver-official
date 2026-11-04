---
layout: default
title: Board
permalink: /board/
---

## PCB — top and bottom

### Top

{% if site.data.board.top %}<img src="{{ '/assets/gen/board-top.svg' | relative_url }}" alt="PCB top">{% else %}<p><em>PCB top render not generated — run scripts/make_fab.sh.</em></p>{% endif %}

### Bottom

{% if site.data.board.bottom %}<img src="{{ '/assets/gen/board-bottom.svg' | relative_url }}" alt="PCB bottom">{% else %}<p><em>PCB bottom render not generated — run scripts/make_fab.sh.</em></p>{% endif %}

Per-layer SVG: {% if site.data.board.layers.size > 0 %}{% for l in site.data.board.layers %}<a href="{{ '/assets/gen/' | append: l.file | relative_url }}">{{ l.name }}</a>{% unless forloop.last %} · {% endunless %}{% endfor %}{% else %}<em>per-layer SVGs not generated</em>{% endif %}
