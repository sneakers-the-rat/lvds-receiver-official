# Power tree — PDLVDS-RX rev A

Input: USB-C VBUS 5 V (UFP sink, CC 5.1 kΩ pull-downs), PTC fuse 1.1 A,
SMBJ5.0A TVS. Everything on the board is derived from this one rail;
total worst-case draw ≈ 3.6 W (0.72 A at 5 V) — inside a 900 mA USB2
budget only with the HV supply at light load; a USB3 / BC1.2 port
(1.5 A) is recommended for full-HV operation and this is stated in the
README. Numbers below are datasheet typicals/maximums as noted.

## Rails
| Rail | Source | Set point | Loads (max) | Budget |
|---|---|---|---|---|
| +5V | USB VBUS via F1 | 5.0 V (4.75–5.25) | everything below | — |
| +3V3D | U11 TPS62130 buck | 3.296 V (FB 0.8 V × (1+312/100)) | STM32H723 ≈250 mA, ADN2813 via FB1 155 mA, SN65LVDS32 25 mA, DAC8562 3 mA, misc GPIO/LED 40 mA | ≈0.48 A of 3 A |
| +3V3D_CDR | FB1 ferrite off +3V3D | — | ADN2813 139 mA typ / 155 mA max | — |
| +3V3A | U14 LT3042 LDO from +5V | 3.32 V (RSET 33.2 kΩ × 100 µA) | USB3300 ≈60 mA, TMP117 0.01 mA, MCU VDDA ≈20 mA | ≈80 mA of 125 mA ILIM |
| +VA | U13 LT3042 LDO from +5V | **4.6 V** (RSET 46 kΩ) | OPA657 14.5 mA, THS4304 ≈11 mA, LMH7220 ≈12 mA | ≈38 mA of 125 mA ILIM |
| −VA | U12 TPS62130 inverting + FB2 ferrite | −5.5 V raw, ≈−5.4 V after ferrite at load | OPA657 V− 14.5 mA | ≈15 mA |
| PHY_1V8 | USB3300 internal regulator | 1.8 V | USB3300 core (internal) | not a board rail |
| HV | U10 LT3757 flyback | 116–253 V programmable (C30737 fit; S8664 variant values: 151–420 V) | APD bias: dark current × M + signal ≈ µA; post-filter drop across 10 kΩ is mV-scale | sim/hv_design.py, sim/run_hv_clamp.py |

## Why +VA is 4.6 V, not 5.0 V
The analogue loads want ~5 V, but an LDO fed from USB VBUS cannot make
5.0 V out of a worst-case 4.75 V input. Rather than add a boost stage,
+VA is set to 4.6 V (LT3042 dropout at the +VA load of ≈38 mA is
220 mV typ / 270 mV max per the datasheet EC table, ILOAD 1–50 mA —
this corrects an earlier ≈60 mV figure in this paragraph, which the
datasheet does not support; audit finding F-11). Consequence,
recorded as a settled residual risk (parts-fix, docs/09): regulation
holds at nominal VBUS 5.0 V (400 mV headroom ≥ 270 mV max dropout)
but NOT at the VBUS minimum 4.75 V (150 mV headroom < 220 mV typ
dropout), where +VA sits at ≈4.53 V. That corner stays inside every
load's operating range — OPA657 total supply ≈9.9 V against its
10 V nominal class, THS4304 2.7–5 V ✓, LMH7220 2.7–12 V ✓ — so the
failure mode is a slightly lower analogue rail at the USB voltage
corner, not a dead rail. Consequences at nominal VBUS, all checked
against the requirements: OPA657 runs at +4.6/−5.4 V (total 10.0 V,
inside its ±5 V nominal operating point; gain/noise specs in the link
budget used the datasheet ±5 V figures — the small asymmetry does not
move them materially); THS4304 single-supply range is 2.7–5 V ✓;
LMH7220 range 2.7–12 V ✓ and its LVDS common-mode is supply-independent
to first order. VMID for the post-amp is +VA/2 ≈ 2.3 V.

## HV set-point network (see also hw/CONNECTIONS.md)
V_FBX = 1.6 V (LT3757 datasheet Rev. F: FBX regulation voltage
1.569/1.6/1.631 V). The network is fitted per detector population;
the two value sets are mutually exclusive stuffing variants.

**Standard fit — Excelitas C30737 (hardware-bounded ≤ 260 V).**
Divider R31 7.68 MΩ / R32 75.0 kΩ; DAC injection R33 140 kΩ from
DAC8562 VOUTB (0–2.5 V, internal-reference gain ×1). R31/R32/R33
are specified 0.1% (the bound below depends on it; at 1% the
worst-case ceiling rises to 264 V and the bound no longer holds).
As fitted (parts-fix, docs/09), R31 is a three-element series string
(R31 2.94 MΩ + R49/R50 2.37 MΩ, Vishay TNPV1210, 0.1% each) for
voltage rating: the string's all-corner total band equals the
single-part ±0.1% band exactly, so every number below is unchanged
(proof: results/partsfix/r31_string_check.py). No OVP clamp is
fitted for this population: the clamp window (must not conduct at
≤259.40 V worst-case demand; must conduct below the 260 V lowest
rail-fed rating) is 0.6 V wide and no real device fits it — the
set-point bound above is this population's protection (docs/09).
V_HV ≈ 165.4 + 54.86 × (1.6 − V_DAC) volts → 0 V DAC = 253.2 V,
1.25 V ≈ 184.6 V, 2.5 V ≈ 116.1 V. The maximum demand over ALL
DAC states — including the DAC8562's zero-scale power-up state,
which is the top of this transfer — is 253.2 V nominal and
259.4 V with every tolerance corner stacked against the bound
(FBX reference at its 1.631 V datasheet max, resistor ratios at
their 0.1% worst, FBX pin sinking its 100 nA max): inside the
C30737's 260 V breakdown maximum by construction, in hardware,
independent of firmware. Derivation: results/hvfix/derivation.py;
ngspice of the actual network agrees (253.17 V nominal zero-scale,
259.36 V at the corner — sim/run_hv_clamp.py). The range covers
the C30737 envelope: the full 180–260 V VBR span except the top
≈7 V sliver at warm temperatures, and the cold corner (a 180 V
unit at −20 °C needs 125.4 V; the low end reaches 116.1 V nominal,
123.2 V at its own stacked worst corner). Firmware hv_ctrl.c maps
requested voltage → DAC code by inverting this transfer and
applies the C30737 temperature coefficient 1.3 V/°C from TMP117
readings. D1's terminals stand across essentially the full bias
(anode ≈ +1.0 V), so the maximum terminal voltage is ≈252 V
nominal / ≈258 V worst-case — the figure the docs/07 exemption
gate re-runs against.

**Variant fit — Hamamatsu S8664-20K (mutually exclusive).**
R31 7.68 MΩ / R32 49.9 kΩ / R33 71.5 kΩ (the original values):
V_HV ≈ 247.8 + 107.4 × (1.6 − V_DAC) → 151–420 V, the range that
detector's ≈400 V breakdown requires. Firmware constants for this
fit are A = 419.7 V, slope 107.4 V/V (hv_ctrl.h). The 420 V
design-point analysis and sims (sim/hv_design.py, sim/run_hv.py)
describe this variant. This fit DOES get the hardware OVP clamp
R9/docs/02 promised (parts-fix, docs/09): D9–D11 (SMBJ5384B 160 V +
2× SMBJ5383B 150 V, DO-214AA) stack across HV_RAW, 460 V nominal,
±5% band 437–483 V — above this fit's 429.47 V worst-case demand,
below D2's 500 V breakdown maximum, the lowest rating on the rail.
The stack is DNP in the standard (C30737) build.

**HV enable — off at power-up by hardware.** SHDN/UVLO divider
R25 143 kΩ / R26 33 kΩ holds the node at 0.94 V nominal,
1.03 V worst-case (VBUS 4.75–5.25 V, 1% tolerances, 1 µA MCU pin
leakage allowance) — below the LT3757's falling threshold across
its whole datasheet spread (1.17 V min / 1.22 typ / 1.27 max), so
the divider alone can never start the converter (its VIN falling
point is 6.51 V, above any legal VBUS); the pin's own 2 µA
pull-down pulls the idle node lower still. PC7 reaches the node
only through the J5 interlock jumper (docs/06 owner decision):
jumper absent, PC7 is not connected to the node at all and no
DAC or firmware state can start the converter; jumper fitted,
PC7 low clamps the node to ≈0 V and PC7 high drives it to
≈3.3 V to enable. PA6 senses the node voltage (ADC1) so firmware
reports the jumper state and refuses enable while it is absent.
Bring-up check items: idle node voltage (expect ≈0.94 V with PC7
floating), J5-absent blocking under a driven-high PC7, and the
sense thresholds (docs/05).

## Sequencing / safety
- HV bleeder R30 4.7 MΩ (fitted as a 2× 2.35 MΩ KOA HV73V2B series
  string for voltage rating; total and discharge spec unchanged,
  parts-fix docs/09) across C33 discharges the rail → <60 V in
  ≈1 s (sim: 1.34 s for the 10 kΩ/100 nF filter chain worst case
  from the S8664 variant's 420 V; the C30737 fit starts from
  ≤253 V and decays faster) — R9 ✓.
- No rail depends on firmware to be safe: DAC outputs power up at
  zero-scale (DAC8562 power-on-reset to zero), which for the
  fitted network is the maximum demand — 253.2 V nominal,
  259.4 V worst-case for the C30737 fit, inside the detector's
  envelope (above). And the converter cannot start at power-up
  regardless: the SHDN divider holds its node below threshold
  with the MCU pin floating, and PC7 reaches the node only
  through the fitted J5 jumper. Firmware sets the operating
  point (hv_ctrl_init writes minimum demand first) before any
  enable. This interaction is a named bring-up test (docs/05):
  power up with J5 absent and PC7 floating, confirm the rail
  stays at 0 V, fit J5, confirm SHDN control, then enable.
- LT3757 input is +5V direct; input bulk C35 10 µF + the USB TVS.
