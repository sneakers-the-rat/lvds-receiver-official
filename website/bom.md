---
layout: default
title: BOM
permalink: /bom/
---

## Bill of materials

{% if site.data.bom and site.data.bom.available %}
{{ site.data.bom.n_lines }} line items, {{ site.data.bom.n_parts }} placed parts.

| {% for h in site.data.bom.header %}{{ h }} | {% endfor %}
|{% for h in site.data.bom.header %}---|{% endfor %}
{% for row in site.data.bom.rows %}| {% for cell in row %}{{ cell }} | {% endfor %}
{% endfor %}
{% else %}
<p><em>BOM not generated — run scripts/make_fab.sh.</em></p>
{% endif %}
