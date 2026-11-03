# Connection list — PDLVDS-RX rev A (authoritative: hw/circuit.py)

The schematic (`pdlvds_rx.kicad_sch`) is generated from `hw/circuit.py` by
`hw/gen_schematic.py` and verified by `hw/check_netlist.py`: the KiCad
netlist export matches circuit.py pin-for-pin (see results/netlist-check.txt).
This document is the human-readable form of the same data plus the design
notes a reviewer needs. Pin numbers/names are from the datasheets in
`../datasheets/` (see MANIFEST.md) unless marked VERIFY.

## Signal chain
- D1 C30737LH-500-90: cathode (pad 5) -> APD_K (HV bias, through R29 10 kΩ
  post-filter from HV_RAW; C33 100 nF/630 V local; C4 1 µF is on the TIA-side
  low-voltage section — see note below). Anode pads 1,2,3,4,6 -> APD_A.
  NOTE: C4 in the AFE group decouples APD_K's low-frequency return path at
  the TIA end of the board; it is a 1 µF part and must be fitted with a
  ≥450 V rated part in the same footprint if placed on APD_K — as drawn it
  sits between APD_K and GND, so use a 630 V 1206 in that position at
  assembly (BOM note). D2 S8664-20K (DNP alternative) reaches the same nets
  through 0 Ω jumpers RJ1/RJ2 (DNP). S8664 lead identity is NOT verified
  (datasheets/s8664.pdf is an HTML error page — see MANIFEST correction);
  verify against the Hamamatsu drawing before fitting D2.
- APD_A -> U1 OPA657 pin 2 (−IN). Pin 3 (+IN) -> GND. R1 3.3 kΩ + C1 0.4 pF
  between OUT (pin 6, TIA_OUT) and −IN. Supplies ±VA (pins 7/4), C2/C3 decouple.
- TIA_OUT -> C5 1 nF AC coupling -> POST_INP (U2 THS4304 pin 3), biased to
  VMID via R2 1 kΩ. U2 gain +5.03: R3 806 Ω (OUT pin 1 -> IN− pin 4),
  R4 200 Ω (IN− -> VMID). VMID = +VA/2 via R5/R6 10 kΩ + C6 10 µF.
  U2 supplies: pin 5 = +VA, pin 2 = GND (single-supply 2.7–5 V per datasheet).
- Path select: R7 0 Ω (fit default) TIA_OUT -> CMP_IN; R8 0 Ω (DNP)
  POST_OUT -> CMP_IN. Fit exactly one.
- CMP_IN -> U3 LMH7220 pin 6 (IN+). Pin 1 (IN−) = THR_FILT: DAC VOUTA via
  R10 1 kΩ + C11 100 nF. R9 100 kΩ from Q (pin 4) to IN+ = hysteresis.
  Q (pin 4) = CMP_QP, Q̅ (pin 3) = CMP_QN. VCC pin 5 = +VA, GND pin 2.
- CMP_QP/QN -> C8/C9 100 nF AC coupling -> U4 ADN2813 PIN (5) / NIN (4).
- J3 SMA -> R11 49.9 Ω (DNP) -> CMP_IN (electrical test injection).

## CDR (U4 ADN2813, LFCSP-32; pinout per datasheet Rev. C)
VCC pins 1,2,12,18,24,31,32 -> +3V3D_CDR (FB1 ferrite from +3V3D; C50/C51).
VEE 8,13,17,23,30 + EP -> GND. VREF (3) -> C12 1 µF. SLICEP/SLICEN (6,7)
joined by C13 100 nF. THRADJ (9) -> R12 10 kΩ to GND (≈ mid LOS threshold).
REFCLKP (10) <- X2 25 MHz oscillator; REFCLKN (11) -> C14 100 nF to GND.
CF1 (15)/CF2 (14): C15 0.47 µF between. LOL (16) -> MCU PA2. SADDR5 (19)
-> GND (I²C address 0x40). SCK (20)/SDA (21) -> I2C bus. LOS (22) -> MCU
PB14. SQUELCH (27) <- MCU PB15. CLKOUTP/N (26,25), DATAOUTP/N (29,28) LVDS.

## Capture + LVDS output
CDR_DATP/N and CDR_CLKP/N each have R13/R14 100 Ω termination at U5 and
also feed J2 (LVDS out header: 1 DATP, 2 DATN, 3/4 GND, 5 CLKP, 6 CLKN).
U5 SN65LVDS32: 1A/1B = DATP/DATN -> 1Y (3) = CAP_DATA -> MCU PA1;
2A/2B = CLKP/CLKN -> 2Y (5) = CAP_CLK -> MCU PA0. Enables: G (4) = +3V3D,
Ḡ (12) = GND. Channels 3/4 inputs tied to rails, outputs NC.

## MCU (U6 STM32H723ZGT6, LQFP-144; pin numbers from ST KiCad symbol)
ULPI: D0 PA3, D1 PB0, D2 PB1, D3 PB10, D4 PB11, D5 PB12, D6 PB13, D7 PB5,
CK PA5, STP PC0, DIR PC2_C, NXT PC3_C. ** PC2_C/PC3_C are the H723's
analog-switch pads: firmware must close the SYSCFG PMCR analog switches
before ULPI will work — bring-up item #1 (docs/04). **
SWD: PA13/PA14 -> J4. I2C1: PB6/PB7 (ADN2813 + TMP117, R20/R21 4.7 kΩ
pull-ups). SPI3: PC10 SCK, PC12 MOSI -> DAC8562; PA15 = DAC_SYNC.
GPIO: PA0 CAP_CLK, PA1 CAP_DATA, PA2 CDR_LOL, PB14 CDR_LOS, PB15 SQUELCH,
PC7 HV_SHDN, PC8 BIST_DRV, PC9 LED_STAT, PB8 TMP_ALERT, PB9 PG_3V3,
PA4 USB_RST, PA9/PA10 DBG_TX/RX -> TP2/TP3.
Power: all VDD -> +3V3D, VDDA/VREF+ -> +3V3A, VBAT -> +3V3D, PDR_ON ->
+3V3D, VCAP×2 -> C17/C18 2.2 µF, NRST pull-up R15 + C19, BOOT0 R16 to GND.
(AF assignments for SPI3/I2C1/timers remain firmware VERIFY items.)

## USB (U7 USB3300 QFN-32; pinout per datasheet Table 3-1 + pin table)
DP/DM (7,8) <- D3 USBLC6-2SC6 (I/O1/I/O2 connector side DP_CON/DM_CON from
J1; VBUS pin 5 = +5V). ULPI pins per table above (DATA0 = pin 24 …
DATA7 = pin 17). CLKOUT (14) -> ULPI_CK. RESET (9) <- MCU PA4. VBUS (4) =
+5V. ID (5) = GND (device-mode builds commonly ground ID; ULPI function
control selects peripheral mode — VERIFY at bring-up). EXTVBUS (10) = GND
(internal VBUS source). VDD1.8 (15,26) = PHY_1V8 (internal regulator
output, C22 4.7 µF — do not power externally). VDDA1.8 (29) = PHY_1V8A,
C23. REG_EN (31) = +3V3A. RBIAS (32) -> R17 12 kΩ 1% to GND. XI/XO (28,27)
-> X1 24 MHz crystal, C20/C21 18 pF. EP + pins 1,2 = GND.
J1 USB-C: VBUS -> F1 PTC -> +5V (D4 SMBJ5.0A TVS, C25 bulk). CC1/CC2 ->
R18/R19 5.1 kΩ to GND (UFP sink). A6/B6 DP, A7/B7 DN. SH + A1/A12/B1/B12
= GND. SBU1/SBU2 unconnected.

## DAC + temperature
U8 DAC8562 (VSSOP-10): VOUTA (1) = THR_DAC, VOUTB (2) = HV_DAC, AVDD (9)
= +3V3D, VREF (10) decoupled C26 (internal reference), LDAC (4) = GND,
CLR (5) = +3V3D, SYNC/SCLK/DIN (6,7,8) = SPI3 + PA15.
U9 TMP117 (WSON-6, beside D1 for thermal coupling): SCL/SDA (1,6) = I2C,
ADD0 (4) = GND (addr 0x48), ALERT (3) -> MCU PB8 with R22 pull-up,
V+ (5) = +3V3A, EP = GND.

## HV bias (U10 LT3757 MSOP-10E; FBX ref 1.6 V — VERIFY, docs/04)
VIN (10) = +5V. SHDN/UVLO (9) = HV_SHDN: R25 100 kΩ/R26 33 kΩ divider
from +5V (≈1.24 V, just above the 1.22 V threshold) with MCU PC7 able to
pull the node down through R26 to disable. GATE (7) -> R27 10 Ω -> Q1
IRLML0030 gate; Q1 drain = FLY_PRI, source -> R28 0.05 Ω sense -> GND;
SENSE (6) at source. T1 flyback 1:20: primary between +5V and FLY_PRI
(dot at +5V end), secondary dot at GND end, SEC_A -> D5 ES1J anode;
cathode = HV_RAW. C32 100 nF/630 V reservoir. R29 10 kΩ + C33 form the
post-filter to APD_K (the APD node). R30 4.7 MΩ bleeder (<10 s to <60 V).
Divider: R31 7.68 MΩ (APD_K) / R32 49.9 kΩ (GND) -> HV_FBX (node at FBX
pin 2); R33 71.5 kΩ injects HV_DAC into the node. With V_FBX = 1.6 V:
V_HV = 1.6·(1+7680/49.9) + (1.6−V_DAC)·(7680/71.5) ≈ 247.8 + 107.4·(1.6−V_DAC)
→ V_DAC 0 V ≈ 420 V, 1.25 V ≈ 285 V, 2.5 V ≈ 151 V (see docs/03).
VC (1): R23 10 kΩ + C29 10 nF compensation (nominal, tune at bring-up).
SS (3): C30 100 nF. RT (4): R24 24.9 kΩ (≈250 kHz — VERIFY against the
datasheet RT table, docs/04). SYNC (5) = GND. INTVCC (8): C31 4.7 µF.
TP1: APD_K via R34 10 MΩ (safe probe point, reads V_HV·(meter loading)).

## Power (docs/03 has the full budget)
U11 TPS62130 #1: +5V -> +3V3D, FB divider R35 312 kΩ/R36 100 kΩ
(V_REF 0.8 V → 3.296 V), L1 2.2 µH, C38 22 µF out, SS C36 3.3 nF,
FSW/DEF = GND (2.5 MHz, nominal Vout), VOS = +3V3D, PG -> R37 pull-up =
PG_3V3 -> MCU. Pinout per TI SLVSAG7 Table 6-1 (SW 1-3, PG 4, FB 5,
AGND 6, FSW 7, DEF 8, SS/TR 9, AVIN 10, PVIN 11-12, EN 13, VOS 14,
PGND 15-16, EP = GND).
U12 TPS62130 #2 INVERTING (TI datasheet §10.3.3 topology): the IC's ground
pins (AGND/PGND/EP/FSW/DEF/VOS/SS return) sit on NEG_RAW (−5.5 V rail);
L2 from SW to NEG_RAW; FB divider R38 587 kΩ (to system GND) / R39 100 kΩ
(to NEG_RAW) sets −5.50 V; C40 22 µF output (GND side +). PG left NC
(its swing would exceed rating vs system rails). NEG_RAW -> FB2 ferrite
-> −VA (C41 22 µF). Feeds OPA657 V− only (≈15 mA).
U13 LT3042 -> +VA = +4.6 V: IN = +5V, RSET R40 46 kΩ (100 µA × 46 kΩ),
CSET C42 4.7 µF, ILIM R41 1 kΩ (125 mA), PGFB tied to IN (PG unused),
OUT/OUTS (10,9) = +VA. Pinout per LT3042 datasheet pin configuration
(1,2 IN; 3 EN/UV; 4 PG; 5 ILIM; 6 PGFB; 7 SET; 8 GND; 9 OUTS; 10 OUT;
EP GND). +VA is 4.6 V, not 5.0 V, because USB VBUS (4.75 V worst case)
cannot feed a 5.0 V LDO output — see docs/03.
U14 LT3042 -> +3V3A = 3.32 V: RSET R42 33.2 kΩ, same hookup; feeds
USB3300, TMP117, MCU VDDA.
LEDs: D6 power (+3V3D, R44), D7 status (MCU PC9 via R45), D8 = BIST
740 nm source LED near D1 (R46 100 Ω from +3V3D, cathode = BIST_DRV,
MCU PC8 sinks ≈20 mA pulses).
Mechanical: MH1–MH4 M3 corners (GND), MH5/MH6 M2.5 lens-holder holes
flanking D1 on the optical axis, SH1 shield-can footprint (4 GND pads)
over the AFE.
