---
layout: default
title: Board
permalink: /board/
---

## PCB — top and bottom

### Routes — all layers and each copper layer

{% comment %}Selectable gallery: the all-layers composite plus each
copper layer. Every thumbnail is a plain link to its SVG (so it
works without JavaScript); assets/js/routes-gallery.js intercepts
the clicks and swaps the main viewer instead. The viewer image is
itself a link to the currently shown SVG, target _blank, so
clicking the big image opens the full-size render in a new tab.
The staged SVGs carry their own #111 background (baked in by
scripts/site_data.py), so the render stands alone in that tab.{% endcomment %}
{% assign bl = site.data.board.layers %}
{% assign default_file = nil %}
{% assign default_label = nil %}
{% if site.data.board.composite %}{% assign default_file = "board-layers.svg" %}{% assign default_label = "All layers" %}{% endif %}
{% unless default_file %}{% for c in site.data.layers %}{% for l in bl %}{% if l.name == c.name %}{% assign default_file = l.file %}{% assign default_label = c.name %}{% break %}{% endif %}{% endfor %}{% if default_file %}{% break %}{% endif %}{% endfor %}{% endunless %}
{% if default_file %}
<div class="routes-gallery">
<figure class="routes-viewer">
<a id="routes-open" class="routes-open" href="{{ '/assets/gen/' | append: default_file | relative_url }}" target="_blank" rel="noopener"><img id="routes-main" class="routes-main" src="{{ '/assets/gen/' | append: default_file | relative_url }}" alt="{{ default_label }}"></a>
<figcaption><span id="routes-caption" class="routes-caption">{{ default_label }}</span> — click the image to open the full-size SVG in a new tab.</figcaption>
</figure>
<div class="routes-thumbs">
{% if site.data.board.composite %}<a class="routes-thumb{% if default_file == 'board-layers.svg' %} active{% endif %}" href="{{ '/assets/gen/board-layers.svg' | relative_url }}" data-label="All layers"><img src="{{ '/assets/gen/board-layers.svg' | relative_url }}" alt="All layers"><span>All layers</span></a>{% endif %}
{% for c in site.data.layers %}{% for l in bl %}{% if l.name == c.name %}<a class="routes-thumb{% if default_file == l.file %} active{% endif %}" href="{{ '/assets/gen/' | append: l.file | relative_url }}" data-label="{{ c.name }}"><img src="{{ '/assets/gen/' | append: l.file | relative_url }}" alt="{{ c.name }} layer"><span>{{ c.name }}</span></a>{% endif %}{% endfor %}{% endfor %}
</div>
</div>
<script src="{{ '/assets/js/routes-gallery.js' | relative_url }}" defer></script>
{% else %}
<p><em>Layer renders not generated — run scripts/make_fab.sh.</em></p>
{% endif %}

### Top

{% if site.data.board.top %}<img src="{{ '/assets/gen/board-top.svg' | relative_url }}" alt="PCB top">{% else %}<p><em>PCB top render not generated — run scripts/make_fab.sh.</em></p>{% endif %}

### Bottom

{% if site.data.board.bottom %}<img src="{{ '/assets/gen/board-bottom.svg' | relative_url }}" alt="PCB bottom">{% else %}<p><em>PCB bottom render not generated — run scripts/make_fab.sh.</em></p>{% endif %}

Per-layer SVG: {% if site.data.board.layers.size > 0 %}{% for l in site.data.board.layers %}<a href="{{ '/assets/gen/' | append: l.file | relative_url }}">{{ l.name }}</a>{% unless forloop.last %} · {% endunless %}{% endfor %}{% else %}<em>per-layer SVGs not generated</em>{% endif %}
