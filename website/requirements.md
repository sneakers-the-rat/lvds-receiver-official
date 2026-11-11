---
layout: default
title: Requirements
permalink: /requirements/
---

## Requirements — derived from the source paper

What the design had to do, extracted from the Miniscope Zero paper
itself (`docs/01-requirements.md` in the repository, staged into
this page at build time).

{% capture req %}{% include docs/requirements.md %}{% endcapture %}
{{ req | markdownify }}
