---
layout: default
title: Build guide
permalink: /build/
---

## Build guide — from files to a working board

Everything a first builder needs in one place: what to order,
what to fit and what to leave off, how to program the board, and
the safe order to power it up. The detailed fabrication files are
on the [downloads page]({{ '/downloads/' | relative_url }}), the
parts list is tabulated on the [BOM page]({{ '/bom/' | relative_url }}),
and the board itself — 2D renders plus an interactive 3D model —
is on the [board page]({{ '/board/' | relative_url }}).

{% capture bg %}{% include docs/build-guide.md %}{% endcapture %}
{{ bg | markdownify }}
