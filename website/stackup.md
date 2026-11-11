---
layout: default
title: Stackup
permalink: /stackup/
---

## Stackup and impedance

| Layer | Use | Notes |
|---|---|---|
| F.Cu | signals + GND pour | 50 Ω SE width 0.405 mm |
| In1.Cu | solid GND plane | reference for all routing |
| In2.Cu | signals | 100 Ω diff pairs: W 0.300 mm / gap 0.349 mm |
| B.Cu | signals + GND pour | |

Stackup: JLCPCB JLC04161H-7628, 4-layer, 1.6 mm, Er 4.4,
prepreg height 0.2104 mm. Geometry from `sim/impedance.py`
(Hammerstad–Jansen / Wadell); propagation delay 6.02 ps/mm.

An earlier version of this page said the LVDS pairs were length
matched within 0.5 mm. That was a design target, not a property of
the shipped board. Copper measured on the final board gives
CDR_DATP 55.10 mm vs CDR_DATN 57.44 mm (2.34 mm apart) and
CDR_CLKP 48.19 mm vs CDR_CLKN 41.85 mm (6.34 mm apart). The larger
difference is about 38 ps at 6.02 ps/mm — roughly 0.19% of the
20 ns unit interval at the 50 Mbps design target, and a much
smaller fraction of the paper mode's timing — but it is not
0.5 mm matching, and the page no longer claims that it is.
