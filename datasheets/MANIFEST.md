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
| c15522.pdf | Hamamatsu C15522 series MPPC modules, KACC-series | hamamatsu.com datasheet copy via laser-opto.com mirror (direct fetch returned an HTML error page; the first 20 KB c15522.pdf in git history was that HTML page and has been REPLACED) | YES 766 KB | reference only (the part being replaced) |
| s14645.pdf | Hamamatsu S14645 series | hamamatsu.com | YES 608 KB | background only (not in design) |
| adn2813.pdf | ADI ADN2813 CDR | analog.com/media/.../ADN2813.pdf | PENDING — downloads repeatedly timed out at 0 bytes while the apt install saturated egress; curl retry running in background (it has succeeded intermittently for other files). Pinout in hw/ is BLOCKED on this file; do not substitute memory. |
| lt3757.pdf | ADI LT3757 | analog.com/media/.../3757fb.pdf | PENDING — same egress issue as adn2813. |
| stm32h723.pdf | ST STM32H723ZG DS13313 | st.com/resource/en/datasheet/stm32h723zg.pdf | PENDING — st.com stalls at 0 bytes in repeated attempts (100 s timeout, 0 bytes received, 2026-11-03). Fallback if it stays blocked: the KiCad 7 symbol library's STM32H723 symbol (installed from the Ubuntu kicad-symbols package) as the pinout source, recorded as a deviation here. |

## Parameters actually used

### C30737LH-500-90 (Excelitas) — primary detector
Table 1 (p.2): active dia 500 um; peak sensitivity 900 nm; Vbr 180 typ /
260 max V (ordering bins C 180–220 V, D 220–260 V); tempco of VR for
constant M = 1.3 V/°C; gain M=100 @900 nm; responsivity 55 typ / 60 max
A/W @900 nm at M=100 (=> 0.55 A/W at M=1); total dark current 0.1 typ /
1 max nA; noise current 0.1 pA/√Hz (f=10 kHz); capacitance 1 pF typ;
rise+fall 0.9 ns (RL=50 Ω); cutoff 380 MHz; operating −40..+85 °C.
Package (Fig. 10, p.9, rendered drawing read directly): LH = leadless
ceramic carrier (LCC) top-looking, body 3.00 × 3.00 mm; 6 pads,
pad size 1.30 × 0.60 mm, vertical pitch 1.10 mm;
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
-05K/-10K/-20K common outline). Pin identification from the datasheet
drawing (anode/cathode/case) — VERIFY against the rendered drawing at
layout time; the footprint in hw/ marks the pins as drawn there.

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
