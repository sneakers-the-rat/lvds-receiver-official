---
layout: default
title: Schematic
permalink: /schematic/
---

## Schematic

{% if site.data.board.has_schematic_pdf %}<p><a href="{{ '/downloads/schematic.pdf' | relative_url }}">Schematic PDF</a></p>{% else %}<p><em>schematic PDF not generated</em></p>{% endif %}
{% if site.data.board.has_schematic_svg %}<img src="{{ '/assets/gen/schematic.svg' | relative_url }}" alt="schematic">{% endif %}
