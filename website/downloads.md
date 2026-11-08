---
layout: default
title: Downloads
permalink: /downloads/
---

## Fabrication downloads

{% if site.data.downloads and site.data.downloads.files.size > 0 %}{% for f in site.data.downloads.files %}<a href="{{ '/downloads/' | append: f.file | relative_url }}">{{ f.name }}</a>{% unless forloop.last %} · {% endunless %}{% endfor %}{% else %}<em>no downloads yet</em>{% endif %}

Gerbers + drill are in `gerbers.zip`; BOM and CPL
(position) CSVs are the same files tabulated above.

{% if site.data.downloads.fab_source %}<p><small>{{ site.data.downloads.fab_source }}. The BOM download is the site build's regenerated BOM (see the BOM page for its source); board-layers.pdf and the schematic PDF are exported from the current board/schematic by the same build wherever KiCad is available.</small></p>{% endif %}
