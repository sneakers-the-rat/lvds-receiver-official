# 04 — Open risks and bring-up plan

Honest register of everything that is **not** proven by the simulations
and scripted checks in this repo, ordered by how much it matters. The
bench procedures that close each item are in `docs/05-test-plan.md`.

## Resolved during the build (kept here so the history is visible)

- **S8664-20K lead identity** — the datasheet file on disk had been
  overwritten by an HTML error page, so the pin assignment was
  unverified. Resolved in Stage 7b: the datasheet was restored from
  Hamamatsu's official URL and the p.4 drawing was read directly —
  pin 1 = anode, pin 2 = cathode, pin 3 = case. The TO-5 footprint's
  pad pattern was also corrected (it had been drawn 120° equilateral;
  the drawing shows pins on a φ5.08 mm circle, E/N/W in bottom view).
  D2 remains a DNP alternate; see `datasheets/MANIFEST.md`.
- **MCU variant** — an intermediate note chose the LQFP-100 VG; Stage 7
  analysis showed the VG does not bond ULPI_DIR/ULPI_NXT digitally.
  The design uses the STM32H723ZG (LQFP-144). See `docs/02`.

## Open risks

### R-1. Overload recovery ≤ 10 UI (requirement R3) is unproven
The link budget establishes overload *level* (+0 dBm) but not recovery
time. TIA saturation recovery depends on the OPA657 macromodel's
behaviour outside its linear range, which a single-pole macromodel
cannot represent honestly. Only a bench measurement (docs/05 §7)
closes this. If it fails, the standard mitigations are a clamp at the
TIA input or reduced Rf — both are layout-compatible changes, but
neither is in rev A.

### R-2. Comparator behaviour at small overdrive
At the R2 sensitivity point the TIA output swing is ~14× the noise, so
the LMH7220 sees healthy overdrive in the design case. Below the design
point (deep fades, diffuse paths), overdrive falls under ~20 mV where
the LMH7220's propagation-delay dispersion grows; the datasheet does
not characterise it tightly there. The external hysteresis network
(~8 mV) trades a small sensitivity loss for clean edges. The BER
waterfall (docs/05 §2) is the measurement that shows whether this
matters in practice.

### R-3. Two LT3757 numbers are flagged VERIFY
The LT3757 datasheet PDF could not be downloaded from this environment
(manufacturer CDN stalled at 0 bytes; see `datasheets/MANIFEST.md`).
The pinout was cross-checked between two independent copies, but the
**FBX positive-mode reference (taken as 1.6 V)** and the **RT value for
250 kHz (taken as 24.9 kΩ)** come from extracted text that truncated
around those numbers. Both feed the HV set-point network: if FBX is
not 1.6 V, the DAC-to-voltage map in `firmware/hv_ctrl.c` is wrong by
a scale factor (the loop still regulates; the *reported* voltage would
be off, and the DAC injection range would shift). Verify against a
printed datasheet before first HV power-up; the bench HV calibration
(docs/05 §5) measures the true map in any case.

### R-4. STM32 alternate-function numbers are VERIFY items
`firmware/board.h` carries register addresses and AF numbers marked
"VERIFY against RM0468" — the STM32H723 datasheet/reference manual
PDFs were likewise blocked (pinout itself came from ST's KiCad symbol
library, parsed programmatically). A wrong AF number fails loudly at
bring-up (peripheral silent), not silently, but expect to spend time
here. The ULPI pin *numbers* are cross-checked and trusted; the AF
*encoding* is the soft part.

### R-5. USB high-speed device stack is a stub
`firmware/usb_device_stub.c` implements the board protocol on top of a
documented interface, but the ULPI/OTG-HS peripheral initialisation
and the USB device stack itself are bring-up work, listed step by step
below. **No USB enumeration has been claimed or tested.** This is the
single largest block of remaining firmware work. The protocol layer
(commands, capture state machine, codec) is complete and host-tested.

### R-6. PC2_C / PC3_C analog switches gate the whole USB link
On the STM32H723ZG, ULPI_DIR (PC2_C) and ULPI_NXT (PC3_C) are
analog-switch pads. Unless firmware closes the SYSCFG PMCR analog
switches, the ULPI bus is electrically disconnected and USB will
simply never respond — with no error anywhere. This is bring-up
item #1, deliberately: check it before debugging anything else USB.

### R-7. USB3300 ID pin tied to GND
The design is a USB *device*; the USB3300 ID pin is tied to GND and
the ULPI function-control register is expected to select peripheral
mode. If the PHY comes up in host/OTG mode instead, strap/register
behaviour must be revisited at bring-up. Low probability, cheap check
(read the ULPI function-control register after reset).

### R-8. HV enable (SHDN) divider is marginal by design intent
The LT3757 SHDN/UVLO threshold is 1.22 V; the enable divider delivers
≈1.24 V when the MCU asserts PC7. That is only ~20 mV of margin. The
failure direction is safe (HV stays off), but if the first boards
refuse to enable HV, this divider is the first suspect — R values were
chosen so a one-step E12 change raises the margin. Separately: the
DAC8562 powers up at zero-scale, which the set-point network reads as
a ≈420 V demand. HV is held off by SHDN at power-up, and the firmware
sequence (set DAC to the 150 V code *before* asserting SHDN) is a
named bring-up test, not an assumption.

**RESOLVED (2026-11-04 HV fix, docs/03/docs/06).** Both halves of
this risk are closed by design change, not by procedure: the SHDN
divider is re-ratioed (R25 143 kΩ → idle node 0.94 V nominal,
1.03 V worst-case, below the 1.17 V minimum falling threshold, so
the converter is off at power-up by hardware and the divider alone
can never enable it), PC7 reaches the node only through the fitted
J5 interlock jumper, and the set-point network is re-valued so the
DAC's zero-scale state demands at most 253.2 V nominal /
259.4 V worst-case — inside the fitted C30737's envelope. The
bring-up sequence below is updated to match; what remains at
bring-up is verification (idle node voltage, J5 blocking, sense
thresholds), not margin-hunting.

### R-9. Asymmetric analogue rails (+VA = 4.6 V, −VA ≈ −5.4 V)
USB VBUS worst case (4.75 V) cannot feed a 5.0 V LDO, so +VA is 4.6 V
(LT3042). The OPA657 then runs at +4.6/−5.4 V (10.0 V total), inside
its datasheet operating point, and the TIA bias point shifts slightly
from the symmetric-rail simulation. The link budget's noise figures
move negligibly (they are Rf/APD dominated), but the first-article
TIA measurements in docs/05 §4 are the real check. VMID (+VA/2 ≈ 2.3 V)
biases the THS4304 post stage; if the post stage is fitted, confirm
its output common-mode sits inside the LMH7220 input range.

### R-10. THS4304 path-select: fit exactly one of R7/R8
The ×5 post stage is a bench option selected by fitting exactly one of
two 0 Ω links (direct path vs post-amp path). Fitting both shorts the
stage output to the comparator input node through two paths; fitting
neither leaves the comparator input floating. The BOM marks this
explicitly; it is called out here because it is the easiest assembly
mistake on the board.

### R-11. U12 power-good left unconnected
On the inverting TPS62130 (−VA rail), the PG output's swing would
exceed its rating referred to system rails, so PG is NC and the MCU
infers −VA health indirectly (AFE noise/offset behaviour). Acceptable
for rev A; noted so nobody "fixes" it by routing PG to the MCU.

### R-12. ERC/DRC are scripted equivalents on KiCad 7
KiCad 7.0.11's `kicad-cli` has no `sch erc` / `pcb drc` subcommands
(they arrived in KiCad 8), and installing KiCad 8 from the official
PPA was blocked in this environment (permission error writing the
apt sources file). Locally, ERC is replaced by a netlist diff against
`hw/circuit.py` plus structural checks (`hw/check_netlist.py`), and
DRC by a connectivity + clearance audit over KiCad's own geometry
engine (`hw/check_pcb.py`). These are strong checks, but they are not
the vendor DRC: rule classes they do not model (e.g. solder-mask
slivers, courtyard overlaps) are unchecked locally. CI runs the real
KiCad 8 ERC/DRC on every push (`.github/workflows/ci.yml`), and a
native KiCad 8 DRC pass is a required gate before ordering boards.

### R-13. ADN2813 loss-of-signal thresholds
THRADJ is fitted at 0 Ω (≈16.5 mV LOS trip). The comparator output
swing at low light may cross LOS near the sensitivity floor and
squelch the CDR before the BER actually reaches 1e-6. If the measured
waterfall shows a cliff instead of a slope, raising THRADJ (up to
100 kΩ ≈ 3.5 mV) is the first experiment. SQUELCH is under MCU control
(PB15) so firmware can also hold the CDR open during characterisation.

## Bring-up plan (ordered; stop and fix at the first failure)

1. **Unpowered inspection.** Continuity: no rail shorted to GND; HV
   island clearances intact; D1 (APD) orientation; D2 not fitted.
2. **USB power only, HV inhibited.** Plug into a current-limited bench
   supply via USB-C breakout (limit 500 mA). Confirm +5V, then the
   power tree in order: +3V3D (3.30 V), +3V3A (3.32 V), +VA (4.6 V),
   −VA (−5.4 V). Budget in `docs/03-power.md`.
3. **MCU alive.** SWD connect (PA13/PA14), read CPU ID; run the
   firmware's LED pattern on PC9.
4. **SYSCFG switches + ULPI link test (R-6).** Close the PMCR analog
   switches for PC2_C/PC3_C; verify ULPI register read/write against
   the USB3300 (vendor ID register) over the ULPI bus.
5. **I2C scan.** PB6/PB7 bus: TMP117, DAC8562 (SPI, check separately),
   ADN2813 at 0x40 (SADDR5 = 0). Read TMP117 temperature; sanity
   ±2 °C vs room.
6. **USB enumeration.** Complete the device stack (R-5); confirm
   enumeration as a vendor-specific HS device on a laptop; run
   `host/rxhost.py info` (no `--simulate`).
7. **Threshold path.** DAC8562 channel A sweep; observe LMH7220 output
   duty cycle vs threshold on a scope with the SMA input driven by a
   function generator (no light yet).
8. **CDR lock.** Inject a 50 Mbps 8b/10b pattern at the SMA; confirm
   ADN2813 LOL deasserts, recovered clock present, capture state
   machine frames packets; repeat at 16 Mbaud Manchester (the paper's
   mode, as transmitted).
9. **HV first power (R-3, R-8).** Current-limited, HV probe on the
   divider tap. First the interlock proof: J5 absent, PC7 driven
   high by test firmware — the rail must stay at 0 V and the SHDN
   node at its ≈0.94 V divider level. Fit J5; firmware init has
   already left the DAC at minimum demand. Assert SHDN (PC7 high).
   Ramp 116 → 253 V in ~25 V steps, logging demanded vs
   measured voltage (this calibrates the true FBX map). Remove power;
   time the bleeder decay from the set ceiling → <60 V (must be
   <10 s; sim says ~1 s). (S8664 variant boards: ramp to 420 V.)
10. **Optical loopback.** BIST LED (PC8) drives the on-board 630 nm
    emitter; confirm received packets via the light-pipe path. Then an
    external 740 nm source for the full bench plan (`docs/05`).

Any step that fails gets a dated note appended to this file with the
measurement, not a workaround from memory.
