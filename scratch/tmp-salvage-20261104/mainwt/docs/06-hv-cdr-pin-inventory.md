# Inventory — HV control and CDR status pins (primary sources)

Written 2026-11-04, before any code change, for firmware reconciliation
job #2 (`fw-hv-pins`). Authority order: `hw/circuit.py` (design source
of truth) → generated netlist `results/netlist.xml` and
`hw/pdlvds_rx.kicad_sch` (verified pin-for-pin against circuit.py by
`hw/check_netlist.py`) → `hw/CONNECTIONS.md` (human-readable form of
the same data) → `datasheets/MANIFEST.md` (pin functions extracted
from official datasheet text for the LT3757 and ADN2813; the PDFs
themselves are not in the repo — the manifest records source and
validity for each) → `docs/03-power.md` and `sim/hv_design.py`
(secondary design narrative).

## (a) HV converter (U10 LT3757) — every MCU connection

Exactly **one**: net `HV_SHDN` = U10 pin 9 (SHDN/UVLO) ↔ U6 pin 97
(**PC7**). Netlist members: `R25.2, R26.1, U10.9, U6.97`. R25 (100 kΩ)
ties the node to +5V, R26 (33 kΩ) ties it to GND — a divider, with the
MCU pin directly on the divided node (no series element).

No other LT3757 pin reaches the MCU: VC/SS/RT/INTVCC are local
passives, GATE/SENSE are the MOSFET loop, FBX is an analogue node
(HV divider R31/R32 + DAC injection via R33), VIN is +5V. Bias
*voltage* control is the DAC8562's VOUTB into that FB node (net
HV_DAC) — reconciled in the DAC job, not this one.

**Polarity and power-up default, derived:**

- LT3757 SHDN/UVLO: 1.22 V **falling** threshold, ~2 µA pin pull-down
  (MANIFEST, from two independent datasheet copies, Rev. F/G/H agree).
- Divider alone (PC7 not driving): 5 V · 33/(100+33) = **1.241 V** —
  above the threshold → converter *enabled*.
- PC7 driven **low**: node ≈ 0 V → below threshold → converter **shut
  down**. PC7 driven high (3.3 V): node 3.3 V → enabled. So the only
  positively-off state is an actively driven low; high or floating
  both leave the converter enabled.
- At reset the MCU pins are inputs, so during the reset window the
  node sits at the divider's ≈1.24 V — the enabled side, and marginal
  (the pin's own pull-down and resistor/threshold spread can pull it
  below threshold; docs/03 records exactly this and calls the
  direction safe). The drawn design's OFF guarantee is therefore
  firmware: PC7 configured push-pull output **low** at the earliest
  init step and never floated afterwards. docs/03 states the intended
  semantics verbatim: "the MCU pulls HV_SHDN low via PC7 to disable,
  and firmware keeps it disabled until configured."

## (b) ADN2813 (U4) status outputs — every MCU connection

- **LOS**: U4 pin 22 → net `CDR_LOS` → U6 pin 75 = **PB14**.
  Datasheet (MANIFEST, official Rev. C text): LVTTL, **active high**
  (1 = loss of signal asserted).
- **LOL**: U4 pin 16 → net `CDR_LOL` → U6 pin 36 = **PA2**.
  Datasheet: LVTTL, **active high** (1 = loss of lock asserted).
- For completeness, the one CDR *input*: **SQUELCH**, U4 pin 27 ← net
  `CDR_SQUELCH` ← U6 pin 76 = **PB15**; LVTTL, active high disables
  the outputs. Nothing else on the board drives it and no pull
  resistor is drawn, so firmware must drive PB15 (low = outputs
  enabled) or the net floats.

## (c) Interlock search — no drawn source exists

Searches, all negative:

- Net names in `results/netlist.xml` (all 213 nets) matching
  INTERLOCK / SWITCH / COVER / DOOR / SAFE / LOOP: **none**.
- `hw/circuit.py` full part list: no switch, jumper, or sense input
  that could serve as an interlock. (RJ1/RJ2 are DNP 0 Ω links for
  the alternative APD footprint; R7/R8 select the comparator source.)
- `hw/pdlvds_rx.kicad_sch`: zero occurrences of "INTERLOCK".
- `hw/CONNECTIONS.md`: the complete U6 assignment list contains no
  spare input usable as one.
- Near misses that are **not** interlocks: `PG_3V3` (PB9, the 3.3 V
  buck's power-good), `TMP_ALERT` (PB8, TMP117 thermal alert),
  `BIST_DRV` (PC8, an output), NRST/BOOT0 (system pins).

Documentary origin of the idea: `docs/01-requirements.md` R9 lists an
"HV enable interlock" as a requirement, and `docs/02-architecture.md`
says HV requires "the enclosure interlock jumper is fitted". The
drawn rev A design implements neither a jumper nor a sense input.
The requirement is on paper; the hardware is not on the board.

## Consequence — owner design decision

Firmware must not invent an input. Until the owner changes the design
(a fitted interlock in a schematic revision) or records a different
decision, **HV enable is refused unconditionally**: SET_BIAS returns
the protocol's INTERLOCK status and the converter is held off (PC7
driven low). Recorded in `docs/00-status.md` and
`firmware/BRINGUP.md` with this inventory as the evidence.

## What board.h claimed vs. what is drawn (the defect being fixed)

`board.h` defined `BOARD_HV_EN`=PB0, `BOARD_INTERLOCK`=PB1,
`BOARD_LOS`=PB2, with comments describing an AND gate and an
interlock jumper in series. circuit.py assigns **no** HV, interlock,
or LOS function to any of those pins: PB0 = ULPI_D1 and PB1 = ULPI_D2
(the USB data bus — driving them as GPIO would corrupt ULPI), and
PB2 has no assignment at all. As shipped, `hv_ctrl.c` could never
have driven the real converter's shutdown pin, and `adn2813.c` read
a "LOS" pin that is connected to nothing.

## Owner decision and implementation — J5 interlock (2026-11-04)

The decision left open above has been taken. The owner delegated
it ("do whatever you need to do") on 2026-11-04 and it is
implemented in the same schematic change as the HV hardware bound
(docs/03), so the board needs one regeneration, not two.

**Decision: a deliberate-action hardware interlock — a 2-pin
jumper, J5 — in series in the SHDN enable path.** Rationale:
rev A is an open bench board with no enclosure, so an enclosure
switch has nothing to sense; what the design needs is that HV can
never be live unless a person has deliberately armed it. A
fitted-or-absent jumper is exactly that act, it is proportionate,
and it fails safe: every failure direction (jumper absent, jumper
pulled, firmware crashed, MCU unpowered) leaves the converter off.

**As drawn now (hw/circuit.py):**

- J5 = 2-pin header, footprint
  `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical`.
  Pin 1 = net HV_EN (U6 PC7), pin 2 = net HV_SHDN (the LT3757
  node: U10.9, R25.2, R26.1 — plus the sense pin below).
- Jumper ABSENT: PC7 is not connected to the node at all. The
  node is held by the R25/R26 divider alone, which was re-ratioed
  in the same change (R25 100 kΩ → 143 kΩ): idle 0.94 V nominal,
  1.03 V worst-case, below the LT3757 falling threshold across
  its whole datasheet spread (1.17 V min) — so with the jumper
  absent the converter cannot start under ANY DAC or firmware
  state, including a crashed MCU driving PC7 high (the signal
  goes nowhere) or the reset window (pin floating = divider =
  off; this also closes the marginal-divider caveat in section
  (a) above: floating no longer enables).
- Jumper FITTED: PC7 control works as designed — low clamps the
  node to ≈0 V (off), high drives ≈3.3 V (enabled).

**Sense input — fitted.** Section (c) searched for an existing
spare input and found none drawn; the pin inventory of the
LQFP-144 package itself has ample unassigned pins, and PA6 —
previously assigned to nothing in circuit.py — is now wired to
HV_SHDN as an analogue sense input (ADC1; firmware hv_sense.c).
A digital read cannot separate the fitted-clamped signature
(≈0 V) from the absent signature (0.94 V, at the VIL band edge),
hence the ADC. Firmware behaviour with the sense:

- `hv_ctrl_enable()` samples the node: absent (or sense failed)
  → refused, SET_BIAS returns USB_STATUS_INTERLOCK — the same
  refusal rev A always gave, now conditional on a real input.
- Fitted → enable proceeds, subject to the existing gates
  (temperature-valid, slew limiting, fault handling).
- `hv_ctrl_update()` re-samples every cycle: pulling J5 mid-run
  drops HV (the hardware drops the node on its own; firmware
  follows the fact), and GET_STATUS publishes the sensed state.

The hardware gate is authoritative: the sense can only veto or
report. A misreading sense (e.g. a wrong ADC channel constant —
marked VERIFY in board.h) degrades to refusal, never to an
enable the jumper has not physically granted.

**Layout consequence (for the routing lane):** J5 is the one new
footprint in this fix. Place it at the board edge near the HV
cluster, operator-accessible. Nets HV_EN (U6→J5) and HV_SHDN
(J5→U10, plus the PA6 sense member at U6) route as part of that
placement pass; nothing else about the layout changes.
