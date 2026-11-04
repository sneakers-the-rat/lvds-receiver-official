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
(Hammerstad–Jansen / Wadell); propagation delay 6.02 ps/mm, length
matching within 0.5 mm on LVDS pairs.
