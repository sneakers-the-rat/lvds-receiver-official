---
layout: default
title: Summary
permalink: /
---

## Project summary

Design status and stage-by-stage evidence live in the repository
(`docs/00-status.md`); open risks and the bring-up plan in
`docs/04-risks.md`. Everything on this site is generated from the
repository's own verified artefacts: the skeleton is Jekyll
(`website/`), fed by a data step (`scripts/site_data.py`) that reads
the same result files this panel shows.

{% include status_panel.html %}

{% capture req %}{% include docs/requirements.md %}{% endcapture %}
{{ req | markdownify }}

{% capture arch %}{% include docs/architecture.md %}{% endcapture %}
{{ arch | markdownify }}
