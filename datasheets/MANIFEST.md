# Datasheet manifest — sources, validity, and the parameters actually used

Rule (stage 2): pinouts and footprint dimensions used in hw/ come from these
PDFs only (text layer or rendered dimension drawings), never from memory.
Validity = `file` reports PDF + pdfinfo opens + pdftotext extracts the
expected title page. The extracted .txt files sit next to the PDFs (working
aids, same sources).

| File | Part / doc | Source | Valid? | Key parameters used |
|---|---|---|---|---|
| C30737.pdf | Excelitas C30737 series APD, Rev.2017-10, 14 pp | excelitas.com | YES 1.1 MB | see below |
| opa657.pdf | TI OPA657, SBOS197F | ti.com/lit/ds/symlink/opa657.pdf | YES 1.2 MB | see below |
| lmh7220.pdf | TI LMH7220, SNOSAL3E | ti.com | YES 719 KB | see below |
| dac8562.pdf | TI DAC8562 (DACxx6x), SLAS719E | ti.com | YES 2.1 MB | see below |
| tmp117.pdf | TI TMP117, SNOSD82D | ti.com | YES 1.7 MB | see below |
| ths4304.pdf | TI THS4304, SLOS436A | ti.com/lit/ds/symlink/ths4304.pdf | YES | see below |
| usb3300.pdf | Microchip USB3300, DS00001783B | microchip.com (via Octopart mirror of the same doc after the direct CDN fetch returned HTML) | YES 978 KB | see below |
| s8664.pdf | Hamamatsu S8664 series Si APD, KAPD1012E | hamamatsu.com/content/dam/.../s8664_series_kapd1012e.pdf | YES 639 KB | see below |
| smt740.pdf (in results/partsfix/datasheets/) | Ushio Epitex SMT740 740 nm top IR LED, Ushio Opto Semiconductors data sheet 2019.03, 7 pp | laser-opto.com mirror of the Ushio sheet (the 2026-11-04 copy was truncated at 55,927 bytes with no EOF; replaced 2026-11-10 by the complete 177,263-byte copy) | YES 173 KB | see below |
| c15522.pdf | Hamamatsu C15522 series MPPC modules, KACC-series | hamamatsu.com datasheet copy via laser-opto.com mirror (direct fetch returned an HTML error page; the first 20 KB c15522.pdf in git history was that HTML page and has been REPLACED) | YES 766 KB | reference only (the part being replaced) |
| s14645.pdf | Hamamatsu S14645 series | hamamatsu.com | YES 608 KB | background only (not in design) |
| adn2813.pdf | ADI ADN2813 CDR, Rev. C | analog.com/media/.../ADN2813.pdf | PDF download BLOCKED (repeated 0-byte stalls), BUT full datasheet text extracted via the browser cache of the same official URL on 2026-11-03 — pinout/registers below are from that official text. See ADN2813 section. |
| lt3757.pdf | ADI LT3757/LT3757A | analog.com/media/.../3757fb.pdf | PDF download BLOCKED (same stalls; one browser fetch failed with a network error and was not retried per policy). Pin configuration + pin functions extracted from two independent datasheet copies found in search (Mouser-hosted LT3757_3757A datasheet and a full-text mirror) — identical in both. See LT3757 section. |
| stm32h723.pdf | ST STM32H723 DS13313 | st.com/resource/en/datasheet/stm32h723zg.pdf | PDF download BLOCKED (repeated 0-byte stalls incl. a 100 s attempt; still blocked 2026-11-10). FALLBACK USED at the time: pinout from the KiCad 7 symbol library (STM32H723VGTx = LQFP-100), hw/h723vgt_pins.json — that VG phase was SUPERSEDED: the design as built is the ZG (LQFP-144), its pin map parsed from the installed KiCad 8 library symbol STM32H723ZGTx (144 pins). F-08 CLOSED 2026-11-10 (docs/09): AN5419 Rev 2 read in full from st.com (browser route) — VCAP rule 2.2 µF ESR < 100 mΩ per pin, LDO mode; exact-block symbol extraction gives VCAP on pins 71/106, matching C18/C17 as designed. |

## Parameters actually used

### C30737LH-500-90 (Excelitas) — primary detector
Table 1 (p.2): active dia 500 um; peak sensitivity 900 nm; Vbr 180 typ /
260 max V (ordering bins C 180–220 V, D 220–260 V); tempco of VR for
constant M = 1.3 V/°C; gain M=100 @900 nm; responsivity 55 typ / 60 max
A/W @900 nm at M=100 (=> 0.55 A/W at M=1); total dark current 0.1 typ /
1 max nA; noise current 0.1 pA/√Hz (f=10 kHz); capacitance 1 pF typ;
rise+fall 0.9 ns (RL=50 Ω); cutoff 380 MHz; operating −40..+85 °C.
Package (Fig. 10, p.9; dimension extension lines traced at 600 dpi
2026-11-10, docs/07): LH = leadless ceramic carrier (LCC)
top-looking, body 3.00 × 3.00 mm; 6 pads — the printed 1.30 mm is
the inner-edge-to-inner-edge gap, NOT the pad size: pads are
0.70 (radial) × 0.60 mm, starting 0.15 mm inside the package edge
and ending 0.85 mm from it (centres ±1.00 mm), vertical pitch
1.10 mm; pad 1 elongated inward to the centreline;
CONNECTION: PAD 5 = POSITIVE (CATHODE); PADS 1,2,3,4,6 = NEGATIVE (ANODE);
photodetector plane 0.65 mm below package top.
Spectral curve (Fig. 2): responsivity at M=1 ≈ 0.50 A/W @740 nm,
≈ 0.37 A/W @630 nm (read from the 900 nm-PSW curve; used in link budget).

### OPA657 (TI) — TIA
SOIC-8 (D): 1 NC, 2 −IN, 3 +IN, 4 V−, 5 NC, 6 OUT, 7 V+, 8 NC.
GBP 1.6 GHz (decompensated); en 4.8 nV/√Hz; in 1.3 fA/√Hz class;
supply ±5 V or single 5 V operation per datasheet conditions used here:
single +5 V, +IN biased at +1.0 V (design choice, docs/02).

### LMH7220 (TI) — comparator / LVDS out
TSOT-6 (MK): 1 IN−, 2 GND, 3 Q̅, 4 Q, 5 VCC, 6 IN+
(from the datasheet Connection Diagram: top row 6 IN+, 5 VCC, 4 OUT Q;
bottom row 1 IN−, 2 GND, 3 OUT Q̅).
Propagation delay 2.9 ns @100 mV overdrive; LVDS output 325 mV typ into
100 Ω; supply 2.7–12 V. Adjustable hysteresis is via the variant with
extra pins in the full doc — rev A uses external positive feedback
resistors on the TSOT-6 (recorded in docs/02 deviations if changed).

### DAC8562 (TI) — dual DAC
VSSOP-10 (DGS): 1 VOUTA, 2 VOUTB, 3 GND, 4 LDAC, 5 CLR, 6 SYNC,
7 SCLK, 8 DIN, 9 AVDD, 10 VREFIN/VREFOUT.
16-bit, internal 2.5 V reference (gain x2 -> 0–5 V output range option:
internal ref with gain 2 gives 5 V full scale per datasheet §8);
SPI up to 50 MHz, 24-bit frames, data clocked on SCLK falling edge.

### TMP117 (TI) — temperature
WSON-6 (DRV): 1 SCL, 2 GND, 3 ALERT, 4 ADD0, 5 V+, 6 SDA.
Resolution 0.0078125 °C/LSB; accuracy ±0.1 °C (−20..50 °C);
I2C address 0x48–0x4B by ADD0.

### THS4304 (TI) — post-amp
SOT-23-5 (DBV): 1 VOUT, 2 VS−(GND in single-supply use), 3 IN+, 4 IN−, 5 VS+.
Unity-gain stable per datasheet family description (wideband VFB amp);
used at gain +5 (Rf/Rg = 4) — see schematic notes.

### USB3300 (Microchip) — ULPI PHY
QFN-32, 5 × 5 mm, 0.5 mm pitch, exposed GND flag (main ground, via array):
1 GND, 2 GND, 3 CPEN, 4 VBUS, 5 ID, 6 VDD3.3, 7 DP, 8 DM, 9 RESET,
10 EXTVBUS, 11 NXT, 12 DIR, 13 STP, 14 CLKOUT (60 MHz), 15 VDD1.8,
16 VDD3.3, 17 DATA7, 18 DATA6, 19 DATA5, 20 DATA4, 21 DATA3, 22 DATA2,
23 DATA1, 24 DATA0, 25 VDD3.3, 26 VDD1.8, 27 XO, 28 XI (24 MHz crystal),
29 VDDA1.8, 30 VDD3.3, 31 REG_EN, 32 RBIAS (Table 3-1: "External
12KΩ ±1% bias resistor to ground" — that is the value used).
Device-only use: CPEN/EXTVBUS per the datasheet peripheral application
diagram (Fig. 7-1); ID floated (non-OTG allowed per pin table).

### S8664-20K (Hamamatsu) — alternate detector footprint
TO-5 metal can: photosensitive dia 2.0 mm (area 3.14 mm²); spectral
320–1000 nm; peak 600 nm; photosensitivity 0.24 A/W @420 nm (M=1);
dark current max 6 nA; cutoff 280 MHz; Ct 11 pF; Vbr typ 400 V;
tempco 0.78 V/°C; gain typ 50.
Can outline (datasheet dimensional drawing): flange dia 9.1 ±0.2 mm,
can dia 8.1 ±0.1 mm, window-to-base 5.9 ±0.1 mm class dims (S8664-02K/
-05K/-10K/-20K common outline). Pin identification VERIFIED 2026-11-10 from drawing KAPDA0026EC
(p.4): lead circle dia 5.08 +-0.2 mm, leads dia 0.45 mm; in the
lead-side view pin 1 is east, pin 2 west, pin 3 north, index tab NE
(SE in the top/window view), which converts to part-frame (top view,
tab SE): 1 = (+2.54, 0), 2 = (-2.54, 0), 3 = (0, -2.54). The
connection diagram's pin 3 dot ties to the dashed case circle only:
pin 3 = case. The diode glyph was read at vector level from the
PDF (filled triangle, apex pointing at the cathode bar on the
pin-2 side): **pin 1 = anode, pin 2 = cathode, pin 3 = case** —
circuit.py's D2 map (1->APD_A_ALT, 2->APD_K_ALT, 3->GND) and
footprint S8664_TO5 (pads as above with pin 3 at KiCad (0, +2.54)
= part-frame south; drill 0.9; tab silk SE; pin-1 mark east) are
both correct as built. No change.

### SMT740 (Ushio Epitex) — BIST source LED D8
Outline (data sheet p.1, read from the rendered drawing): PLCC-style
top LED, body 3.2 (lead axis) x 2.7 mm, height 1.8 mm, overall lead
span 3.5 mm, lens dia 2.4 mm; terminals 2.2 +-0.1 mm wide with a
0.8 +-0.2 mm flat contact from each body end face; anode mark =
chamfered corner at the anode end. **Not a 1206** — footprint
pdlvds:SMT740_3227 drawn from these dims (pass 224).
Electricals (Tc = 25 C): peak 740 nm typ (730-750 at IF = 50 mA);
VF 1.9 min / 2.2 typ at 50 mA; VFP 3.8 V at IFP = 500 mA; ratings
PD 170 mW, IF 75 mA, IFP 500 mA, VR 5 V. R46 100 ohm from +3V3D
delivers 11-14 mA — inside all ratings (docs/09 F-13).

### C15522-3010SA (Hamamatsu) — the replaced SiPM module (reference)
Built-in MPPC S14160-3010PS class: effective area 3 × 3 mm, pixel pitch
10 µm, 89,984 pixels; module = MPPC + amplifier + HV supply + temperature
compensation, ±5 V supply, analog output. (Why it is replaced: docs/01/02.)

## Still pending when this file was written
adn2813.pdf, lt3757.pdf, stm32h723.pdf — see table. The KiCad stage must
not invent those pinouts; if the PDFs have not landed when layout starts,
use (in order): (1) the installed KiCad symbol library for STM32H723,
(2) vendor HTML datasheet via browser text for ADN2813/LT3757 with the
URL recorded here, and mark the affected footprints PROVISIONAL in hw/.

### ADN2813 (ADI) — CDR (from official datasheet Rev. C text)
LFCSP-32, 5 x 5 mm, exposed pad = GND:
1 VCC, 2 VCC, 3 VREF (decouple 0.1 uF), 4 NIN, 5 PIN (differential data
input, internally biased ~2.5 V, 50 ohm internal termination, AC-couple),
6 SLICEP, 7 SLICEN (slice adjust; tie to VEE for no adjust),
8 VEE, 9 THRADJ (LOS threshold resistor: 0 ohm -> ~16.5 mV trip,
100 kohm -> ~3.5 mV), 10 REFCLKP, 11 REFCLKN (optional, unused here),
12 VCC, 13 VEE, 14 CF2, 15 CF1 (loop filter capacitor CF = 0.47 uF
between CF1/CF2 per the specifications header), 16 LOL (LVTTL, active
high), 17 VEE, 18 VCC, 19 SADDR5 (I2C address bit 5), 20 SCK, 21 SDA,
22 LOS (LVTTL active high), 23 VEE, 24 VCC, 25 CLKOUTN, 26 CLKOUTP,
27 SQUELCH (LVTTL, active high disables outputs), 28 DATAOUTN,
29 DATAOUTP, 30 VEE, 31 VCC, 32 VCC.
OUTPUTS ARE LVDS (datasheet Table 3: VOD 250-400 mV, VOS ~1.2 V) —
this corrects doc 02's "CML outputs" line (see doc 02 deviations).
Specs used: data rate 10 Mb/s-1.25 Gb/s; quantizer sensitivity 3.3 mVpp
typ; supply 3.3 V, 139 mA typ at 1.25 Gb/s; jitter generation (OC-12)
0.003 UI rms typ / 0.026 UI pp max class.
I2C: 7-bit slave address = {1, SADDR5, 0,0,0,0,0} (0x40 with SADDR5=0);
registers: FREQ0 0x0, FREQ1 0x1, FREQ2 0x2, RATE 0x3 (coarse readback),
MISC 0x4 (LOS/LOL status), CTRLA 0x8, CTRLB 0x9, CTRLC 0x11.

### LT3757 (ADI) — HV controller (datasheet copies, Rev. F/G/H agree)
MSOP-10 MSE with exposed pad (pin 11 = GND, must be soldered):
1 VC (error-amp compensation), 2 FBX (feedback; positive-output mode
reference — the value 1.6 V is used in the design and flagged VERIFY
against the full datasheet at bring-up, the pin-function text confirms
the servo behaviour but the extracted text truncated the number),
3 SS (soft-start cap), 4 RT (frequency-set resistor to GND;
250 kHz per the datasheet RT table — value VERIFY), 5 SYNC (tie GND if
unused), 6 SENSE (current-sense, kelvin), 7 GATE, 8 INTVCC (7.2 V
internal regulator output, bypass >= 4.7 uF), 9 SHDN/UVLO (1.22 V
falling threshold, 2 uA pull-down), 10 VIN (bypass >= 0.22 uF).
Input range 2.9-40 V; drives external low-side N-MOSFET.

### STM32H723VGTx (ST) — MCU (KiCad library extraction)
LQFP-100 pin map: hw/h723vgt_pins.json (100 pins; pin 99 = VSS).
Pins used by function are listed in hw/CONNECTIONS.md; alternate-function
numbers for ULPI/timers are firmware-side VERIFY items (RM0468), the
schematic only commits pin number + GPIO name + net.

## Addendum (Stage 7, 2026-11-03) — parts added during schematic capture
- SN65LVDS32 (U5): TI SLLS262R pinout via search snippet of the TI
  datasheet: SOIC-16: 1=1B, 2=1A, 3=1Y, 4=G, 5=2Y, 6=2A, 7=2B, 8=GND,
  9=3B, 10=3A, 11=3Y, 12=G̅, 13=4Y, 14=4A, 15=4B, 16=VCC.
- TPS62130 (U11/U12): TI SLVSAG7F Table 6-1 read in full via DigiKey's
  datasheet rendering: SW 1-3, PG 4, FB 5, AGND 6, FSW 7, DEF 8, SS/TR 9,
  AVIN 10, PVIN 11-12, EN 13, VOS 14, PGND 15-16, EP=GND. VFB = 0.8 V.
  Inverting topology per datasheet §10.3.3 (Figure 42).
- LT3042 (U13/U14): pin configuration read from the full datasheet text
  (ADI Rev. C): 1 IN, 2 IN, 3 EN/UV, 4 PG, 5 ILIM, 6 PGFB, 7 SET, 8 GND,
  9 OUTS, 10 OUT, 11 EP=GND. ISET = 100 µA; ILIM scale 125 mA·kΩ.
- LT3094 was evaluated for the −5 V rail and REJECTED: its pin table
  could not be extracted reliably from the sources reachable here.
  The −VA rail uses the TPS62130 inverting topology instead.
- STM32H723ZGT6: pin name->number map parsed programmatically from the
  installed KiCad symbol (ST data). ULPI mapping D0 PA3, D1 PB0, D2 PB1,
  D3 PB10, D4 PB11, D5 PB12, D6 PB13, D7 PB5, CK PA5, STP PC0, DIR PC2_C,
  NXT PC3_C — cross-checked against ST community + mbed pin tables.
  NOTE the variant change: LQFP-100 (VG) does NOT bond PC2/PC3 digitally;
  the design uses LQFP-144 (ZG). PC2_C/PC3_C are analog-switch pads:
  SYSCFG PMCR switches must be closed for ULPI (bring-up item).
- CORRECTION to the Stage-2 record, resolved in Stage 7b: the
  s8664.pdf on disk was found to be an HTML error page, not a PDF
  (verified with `file`) — a later failed re-download had overwritten
  the valid copy obtained earlier the same day. The file was restored
  2026-11-03 from the Hamamatsu official URL (s8664_series_kapd1012e.pdf,
  654,300 bytes, PDF 1.7) and re-verified with `file`/`pdfinfo`.
  S8664-20K lead identity is now VERIFIED from the datasheet p.4
  dimensional outline (drawing 1, KAPDA0026EC), read from a rendered
  image of the page: **pin 1 = ANODE, pin 2 = CATHODE, pin 3 = CASE**
  (equivalent-circuit inset on the drawing). Pins sit on a
  φ5.08 ± 0.2 mm circle — pin 1 east, pin 3 north, pin 2 west in the
  datasheet BOTTOM view; leads φ0.45; flange φ9.1 ± 0.2, cap
  φ8.1 ± 0.1; tab between pins 1 and 3 (SE in top view).
  circuit.py's D2 pin semantics (1→anode net, 2→cathode net, 3→GND)
  were already correct and are unchanged. The S8664_TO5 footprint,
  however, had been drawn with a 120° equilateral pad pattern, which
  contradicts the drawing; it was corrected to the datasheet pattern
  (top view: pin 1 at (+2.54, 0), pin 2 at (−2.54, 0), pin 3 at
  (0, +2.54), tab tick at SE) in Stage 7b.
- THS4304 supply (from ths4304.pdf in this repo): dual ±1.35–±2.5 V or
  single 2.7–5 V; input common-mode VS− −0.2 V to VS+ +0.2 V. The design
  runs it single-supply on +VA with AC coupling and VMID bias.
