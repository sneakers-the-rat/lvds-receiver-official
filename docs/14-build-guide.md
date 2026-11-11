# 14 — Build guide

How to take this design from files to a working board: what to
order, what to fit (and what to deliberately leave off), how to
program it, and how to power it up for the first time without
hurting it or yourself.

One honest starting point: as of this writing, the design is
complete and fully checked in simulation and by the CAD rule
checkers, but **nobody has built one yet**. The first boards are
first articles. Follow the bring-up order below, stop at the first
step that misbehaves, and expect to spend bench time — that is
what the bench test plan (docs/05) is for.

## 1. The standard build

There is one standard build. Everything else in this guide refers
to it unless it says otherwise.

- Detector: **D1, the Excelitas C30737LH-500-90 APD, fitted.**
  The Hamamatsu S8664-20K position (D2) is an unpopulated
  alternative footprint for a different detector variant. Never
  fit both.
- Comparator input path: **R7 fitted, R8 not fitted** (see §4).
- HV interlock jumper J5: header fitted; the jumper itself is
  **left off** until the HV step of first power (§7).

## 2. Order the PCB

Fabrication files live in `hw/fab/` (also on this site's
downloads page):

| File | What it is |
|---|---|
| `gerbers.zip` | Gerbers + drill files — upload this to the fab |
| `bom.csv` | Bill of materials, 98 grouped lines |
| `cpl.csv` | Pick-and-place positions, 154 placements |

Board specification to order against:

- 100.05 × 125.05 mm, 4 layers, 1.6 mm thick.
- Stackup: JLCPCB **JLC04161H-7628**, or the fab's equivalent
  4-layer controlled-impedance stackup. The controlled-impedance
  geometry was computed for this stackup (50 Ω single-ended =
  0.405 mm track on the top layer; 100 Ω differential =
  0.300 mm / 0.349 mm gap on In2). If the fab substitutes a
  different stackup, the impedances move — ask before accepting a
  substitution.
- The design does not mandate a surface finish. ENIG is a
  sensible choice (flat pads suit the fine-pitch ICs and the
  APD's LCC package); lead-free HASL also works electrically.
- A solder-paste stencil is strongly recommended. Almost
  everything is on the top side; the single bottom-side part
  (C40) can be hand-soldered afterwards if your stencil/process
  only covers one side.
- **Conformal coating is a design requirement, not an option.**
  After assembly, coat the HV bias island (the APD and boost
  converter area on the west side of the board). The board's
  high-voltage spacings are designed to IPC-2221B Table 6-1
  column B4 — external conductors with a permanent polymer
  coating — because the uncoated column (B2, 1.25 mm at this
  voltage) is physically impossible with the fitted detector:
  the C30737's own anode/cathode pads sit 0.50 mm apart at full
  bias. The same note is on the fab drawing layer of the board
  file. An uncoated board does not meet its design basis and
  must not be powered at full bias.

## 3. Order the parts

Order against `hw/fab/bom.csv`. Three warnings, all learned from
how these files are generated:

1. **The BOM and CPL include the do-not-populate positions.**
   They are real rows in both files. If an assembly house builds
   from these files untouched, it will fit parts that must not be
   fitted. Give the assembler the DNP list in §4 explicitly.
2. **Do not substitute the parts in the table below.** Each was
   chosen against a specific electrical requirement and verified
   in the parts lock (docs/08, docs/09).

   | Ref | Part | Why it is not substitutable casually |
   |---|---|---|
   | D1 | Excelitas C30737LH-500-90 APD | The detector; the bias ceiling, footprint and link budget are all built around it |
   | T1 | Würth WE-FLEX HV 749196518 | Flyback transformer; 1500 VAC insulation, windings used in a specific series arrangement |
   | U1 | TI OPA657 | TIA; simulated with its macromodel |
   | U4 | ADI ADN2813 | CDR; pinout and I²C map are design inputs |
   | U6 | STM32H723ZGT6 | The MCU the firmware targets |
   | U7 | USB3300-EZK | USB-HS PHY; ULPI timing is design-critical |
   | U10 | LT3757EMSE | HV controller; the set-point network assumes its 1.6 V feedback reference |
   | C4 | Panasonic ECWFD2J105JB | 1 µF / 630 V film, radial through-hole — it stands across the full APD bias; no MLCC substitute exists in the drawn footprint |
   | SH1 + CL1–CL5 | Harwin S02-20150300 can + five S1001-46R clips | The RF shield over the TIA/post-amp; the clips are its ground connection |

3. Ordinary passives (0603/0805 resistors and capacitors with the
   values and voltage ratings in the BOM) are generic. Respect
   the voltage ratings — several parts in the HV section are
   630 V components in ordinary-looking packages.

## 4. Do-not-populate list (standard build)

Leave these positions empty. They are in the BOM and CPL; omit
them deliberately.

| Ref | What it is | Why it stays empty |
|---|---|---|
| D2 | Hamamatsu S8664-20K alternate detector | Alternative-detector variant only; mutually exclusive with D1 |
| RJ1, RJ2 | 0 Ω links to D2 | Only fitted with D2 |
| D9, D10, D11 | OVP clamp stack for the S8664 variant | Only fitted with D2 |
| R8 | 0 Ω link, post-amp path | See the R7/R8 rule below |
| R11 | 49.9 Ω SMA test-input series resistor | Bench modification only: fitting it connects the J3 SMA input to the comparator for electrical injection tests (docs/04 step 7–8). Leave it off for optical use |

**The R7/R8 rule — fit exactly one, never both, never neither.**
The comparator input can come straight from the TIA (R7) or from
the THS4304 ×5 post-amplifier (R8). Fitting both shorts the TIA
output to the post-amp output. The standard build fits **R7**
(direct path — the level the link budget is calculated for). The
post-amp path is a bench experiment for work below the design
sensitivity point: to try it, remove R7 and fit R8 instead.

## 5. Assembly notes

Assembly order suggestion (any competent process works; this
order keeps the delicate parts accessible longest):

1. Bottom side first: C40 is the only bottom part.
2. Passives and small ICs. The board uses 0402 in a few places
   (C1 is a 0.4 pF 0402) and 0.5 mm-pitch packages (U6 LQFP-144,
   U4/U7 QFN-32) — plan for reflow, not a hand iron, for those.
3. Orientation checks that matter:
   - **T1**: pin 1 is the dot end of the primary and goes to the
     +5 V end. The secondaries are wired in series by the board;
     a reversed transformer puts the ladder's ground end at the
     wrong side.
   - **D12–D15** (ES1J, the Cockcroft–Walton ladder): all four
     point the same way around the ladder (see the schematic);
     one reversed diode silently kills the HV output.
   - **D8** (BIST LED): it is *not* a 1206 — it is a 3.2 × 2.7 mm
     PLCC-style package. Pin 1 (cathode) is at the chamfered end.
   - **D1** (the APD): LCC-6. Pad 5 is the cathode (it takes the
     full bias voltage); pads 1, 2, 3, 4, 6 are the anode side.
     The footprint's elongated pad is pad 1. Fit D1 late, keep it
     clean, and observe ESD precautions — it is the most delicate
     and most expensive part on the board.
   - **C4**: radial film capacitor, through-hole, standing across
     the full APD bias. It is tall (18.5 mm body) — fit it after
     its SMD neighbours.
4. The shield can SH1 clips onto CL1–CL5 over U1/U2. Solder the
   five clips with everything else, but **snap the can on last**,
   after inspection and first power: the parts under it are the
   ones you will most want to probe, and the can is removable by
   hand. D1 sits west of the can, in the clear — it must stay
   uncovered so light reaches it.
5. Fit the J5 header, but leave the jumper itself off (§7).
6. Before power: wash flux residue off the HV island and the TIA
   area. At 250 V and at femtoamp input currents respectively,
   contamination is a functional defect, not a cosmetic one.

## 6. Program the firmware

```
cd firmware
make host-test   # sanity: codec + USB + HV-control tests, host gcc only
make arm         # needs arm-none-eabi-gcc; produces build/rxfw.elf/.bin
```

**Use SWD via J4 for the first board.** It is the route that
always works, blank chip or not. J4 is a 2×5, 1.27 mm header:

| Pin | Signal | Pin | Signal |
|---|---|---|---|
| 1 | VTREF (+3V3D) | 2 | SWDIO |
| 3 | GND | 4 | SWCLK |
| 5 | GND | 6 | NC |
| 7 | GND | 8 | NC |
| 9 | GND | 10 | NRST |

Any ST-Link or compatible SWD probe works. First checks with the
debugger: the MCU reads its CPU ID, and the firmware's status LED
pattern runs on PC9.

A note on DFU: the design documents describe STM32 ROM-bootloader
DFU over USB as the field-update path, but BOOT0 is pulled to GND
by R16 and there is no boot button in the fitted BOM, so do not
plan on DFU for a first board. Use J4.

## 7. First power — low voltage first, HV last

Equipment: a current-limited bench supply with a USB-C breakout
(docs/04 bring-up order), a DMM, and — for §7.3 — a proper HV
probe. **J5 stays off for §7.1 and §7.2.**

### 7.1 Unpowered inspection

- No rail shorted to GND (continuity check every rail).
- D1 fitted and oriented (§5); D2 position empty; R7 fitted, R8
  empty.
- HV island clearances intact; no solder bridges around T1, the
  ladder (C52–C54, D12–D15) or the APD.

### 7.2 USB power, HV inhibited

1. Power from the current-limited supply via the USB-C breakout,
   limit **500 mA**.
2. Confirm the rails, in this order (docs/03):
   +5V, then **+3V3D = 3.30 V**, **+3V3A = 3.32 V**,
   **+VA = 4.6 V**, **−VA = −5.4 V**. Stop and fix at the first
   rail that is wrong.
3. Program the firmware (§6) if not already done; confirm the
   status LED pattern.
4. Probe ULPI_CK (MCU pin PA5): the USB3300 must be delivering
   **60 MHz**. No clock, no USB — see `firmware/BRINGUP.md`
   step 1 for the suspect list.
5. Move to a normal laptop USB port. The board should enumerate
   as VID **0x1209** / PID **0xD723** with a `/dev/ttyACM*` node
   (Linux). Note the power budget honestly: the USB descriptor
   declares 500 mA, while the design's worst-case draw is
   ≈3.6 W (0.72 A at 5 V). A USB 3 / BC1.2 port (1.5 A) is
   recommended for full-HV operation — docs/03.
6. Talk to it:

   ```
   pip install pyserial        # once, for the hardware path
   python3 host/rxhost.py info       # auto-detects by VID:PID
   python3 host/rxhost.py selftest   # deliberately does NOT enable HV
   ```

   `info` should return the board's `PDRX` identity. Run
   `python3 host/rxhost.py --simulate selftest` any time to see
   the software model pass the same suite with no board attached.
   One interface quirk: on hardware, `config --threshold` takes
   the DAC output in millivolts, 0–2500 (1250 ≈ mid-scale).

### 7.3 Enabling HV — read this whole section first

The bias rail reaches **253 V**. It is current-limited and the
stored energy is small, but it deserves respect:

- HV probe only; one-hand rule; no rework, probing of other
  points, or connector fiddling while bias is on.
- After disabling bias, **confirm the rail has decayed below
  60 V on the meter before touching the HV island — every time.**
  The bleeder should do this in under 10 s (simulation says
  ~1 s); a slow decay is a defect, not a curiosity.

Proof sequence (docs/04 step 9, docs/05 §5):

1. **Interlock proof, jumper still off.** Command a bias:
   `python3 host/rxhost.py config --bias 120`. The board must
   answer **INTERLOCK** and the rail must stay at 0 V. This is a
   hardware gate, not just firmware politeness: with J5 absent,
   no firmware state can start the converter.
2. Power down, fit the J5 jumper.
3. Command bias in ~25 V steps from 116 V up toward 253 V,
   logging commanded vs measured voltage at each step. The top
   of the range is hardware-bounded: the set-point network
   cannot demand more than ≈253 V nominal (259.4 V worst case),
   below the C30737's 260 V maximum.
4. Disable, and time the decay to <60 V (must be <10 s).
5. Optional but recommended: pull J5 while bias is on. The rail
   must fall and the firmware must latch a fault.

## 8. Hand-off to verification

A board that passes §7 is powered and programmable — it is not
yet a verified receiver. The bench test plan (docs/05, the *Bench
test plan* page on this site) takes it from there: sensitivity,
BER waterfall by the paper's method, front-end characterisation,
HV ripple and temperature compensation, LVDS levels and jitter,
overload recovery, and the Manchester mode checks. The host tool
is the driver for most of it:

```
python3 host/rxhost.py config --bias 200 --threshold 1250
python3 host/rxhost.py stream --packets 8
python3 host/rxhost.py ber-test --buffers 100 --timeout 30
```

(Commands while capture is streaming are not possible — the raw
capture buffers share the one CDC channel; stop the stream
first.)

## 9. The other connectors, for reference

- **J1** — USB-C: power in + USB data. The board's only power
  source.
- **J2** — LVDS output header, 2×3, 2.54 mm: 1 = DATP,
  2 = DATN, 3 = GND, 4 = GND, 5 = CLKP, 6 = CLKN. This is the
  bit-transparent main output, for connecting to your own
  downstream logic.
- **J3** — SMA: electrical test input to the comparator, only
  connected if R11 has been fitted as a bench modification (§4).
- **J4** — SWD (§6).
- **J5** — HV interlock (§7.3). Not a power connector, not
  optional decoration: the HV supply cannot start without it.

---

*Sources: hw/circuit.py and hw/CONNECTIONS.md (what is fitted and
what connects where), docs/03 (power tree), docs/04 (bring-up
order), docs/05 (bench verification), docs/08 + docs/09 (parts
lock), firmware/BRINGUP.md (USB bring-up checklist). Where this
guide and an older document disagree — the older firmware notes
in particular predate the rxhost hardware path and the fitted
interlock — this guide follows the shipped design data.*
