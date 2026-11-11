---
layout: default
title: Board
permalink: /board/
---

## PCB — the finished board

{% if site.data.board.board_file %}<p><small>Renders of <code>{{ site.data.board.board_file }}</code> — {{ site.data.board.renders_source }}. The site build exports these from the current board on every build; they are never a hand-refreshed copy.</small></p>{% endif %}

### Interactive 3D model

{% if site.data.board.model3d %}
<figure class="viewer3d">
<model-viewer src="{{ '/assets/gen/board-3d.glb' | relative_url }}" poster="{{ '/assets/gen/board-top.svg' | relative_url }}" alt="Interactive 3D model of the PDLVDS-RX board" camera-controls auto-rotate auto-rotate-delay="4000" rotation-per-second="18deg" shadow-intensity="0.6" exposure="1.05"></model-viewer>
<figcaption>Drag to orbit; scroll or pinch to zoom. The model is {{ site.data.board.model3d_source }}. Most components use KiCad library models; the transformer, shield can and clips, photodiodes and BIST LED use simplified project-authored solids at their datasheet dimensions. It is a visualisation, not a mechanical CAD substitute — work from the KiCad board file for enclosure design. A copy is also on the <a href="{{ '/downloads/' | relative_url }}">downloads page</a>.</figcaption>
</figure>
<script type="module" src="{{ '/assets/js/model-viewer.min.js' | relative_url }}"></script>
{% else %}
<p><em>3D model not generated — this site build could neither export it nor stage the fab package's copy.</em></p>
{% endif %}

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
<p><em>Layer renders not generated — the site build could not export them (no KiCad available and no CI fab artefact staged).</em></p>
{% endif %}

### Top

{% if site.data.board.top %}<img src="{{ '/assets/gen/board-top.svg' | relative_url }}" alt="PCB top">{% else %}<p><em>PCB top render not generated — the site build could not export it (no KiCad available and no CI fab artefact staged).</em></p>{% endif %}

### Bottom

{% if site.data.board.bottom %}<img src="{{ '/assets/gen/board-bottom.svg' | relative_url }}" alt="PCB bottom">{% else %}<p><em>PCB bottom render not generated — the site build could not export it (no KiCad available and no CI fab artefact staged).</em></p>{% endif %}

Per-layer SVG: {% if site.data.board.layers.size > 0 %}{% for l in site.data.board.layers %}<a href="{{ '/assets/gen/' | append: l.file | relative_url }}">{{ l.name }}</a>{% unless forloop.last %} · {% endunless %}{% endfor %}{% else %}<em>per-layer SVGs not generated</em>{% endif %}
