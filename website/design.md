---
layout: default
title: Design
permalink: /design/
---

## Design — architecture and part selection

The project's architecture record (`docs/02-architecture.md` in the
repository, staged into this page at build time): the signal chain,
why each part was chosen, and the alternatives that were rejected.

{% capture arch %}{% include docs/architecture.md %}{% endcapture %}
{{ arch | markdownify }}
