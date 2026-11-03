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
| HV | U10 LT3757 flyback | 150–420 V programmable | APD bias: dark current × M + signal ≈ µA; post-filter drop across 10 kΩ is mV-scale | sim/hv_design.py |

## Why +VA is 4.6 V, not 5.0 V
The analogue loads want ~5 V, but an LDO fed from USB VBUS cannot make
5.0 V out of a worst-case 4.75 V input. Rather than add a boost stage,
+VA is set to 4.6 V (LT3042 dropout at 40 mA is ≈60 mV typical, so
regulation holds down to VBUS ≈ 4.7 V). Consequences, all checked
against the requirements: OPA657 runs at +4.6/−5.4 V (total 10.0 V,
inside its ±5 V nominal operating point; gain/noise specs in the link
budget used the datasheet ±5 V figures — the small asymmetry does not
move them materially); THS4304 single-supply range is 2.7–5 V ✓;
LMH7220 range 2.7–12 V ✓ and its LVDS common-mode is supply-independent
to first order. VMID for the post-amp is +VA/2 ≈ 2.3 V.

## HV set-point network (see also hw/CONNECTIONS.md)
V_FBX = 1.6 V (VERIFY against LT3757 datasheet text — docs/04).
Divider R31 7.68 MΩ / R32 49.9 kΩ; DAC injection R33 71.5 kΩ from
DAC8562 VOUTB (0–2.5 V, internal-reference gain ×1):
V_HV ≈ 247.8 + 107.4 × (1.6 − V_DAC) volts → 0 V DAC ≈ 420 V,
1.25 V ≈ 285 V, 2.5 V ≈ 151 V. Firmware hv_ctrl.c maps requested
voltage → DAC code with these constants and applies the C30737
temperature coefficient 1.3 V/°C from TMP117 readings. HV is OFF at
power-up: SHDN/UVLO sits at ≈1.24 V from the R25/R26 divider (just
above the 1.22 V threshold — marginal by design intent? No: it means
the flyback starts when +5V is present; the MCU pulls HV_SHDN low via
PC7 to disable, and firmware keeps it disabled until configured. The
divider ratio is a bring-up check item: if unit-to-unit threshold
spread leaves it below threshold, HV stays off — safe direction.)

## Sequencing / safety
- HV bleeder R30 4.7 MΩ across C33 discharges 420 V → <60 V in ≈0.9 s
  (sim: 1.34 s for the 10 kΩ/100 nF filter chain worst case) — R9 ✓.
- No rail depends on firmware to be safe: DAC outputs power up at
  zero-scale (DAC8562 power-on-reset to zero), which corresponds to
  HV ≈ 420 V demand — BUT the LT3757 loop is bounded by its current
  limit and the divider sets the absolute ceiling: with V_DAC = 0 the
  loop regulates to ≈420 V, the design maximum. Firmware sets the
  operating point before enabling HV via PC7. This interaction is a
  named bring-up test (docs/05): power up with HV disabled at the MCU
  pin, confirm SHDN control, then enable.
- LT3757 input is +5V direct; input bulk C35 10 µF + the USB TVS.
