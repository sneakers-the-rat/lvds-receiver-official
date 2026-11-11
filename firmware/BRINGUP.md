# USB bring-up — what is proven, what is not, and the bench sequence

The USB device transport (`src/usb_device_tinyusb.c` on TinyUSB
0.21.0, descriptors in `src/usb_descriptors_data.h`) is implemented
and is covered by every test that can run without a board:

- `make arm` compiles and links it for the STM32H723 (see README
  for sizes).
- `make host-test` audits the exact descriptor bytes the firmware
  serves (`tests/test_usb_descriptors.c`) and round-trips the real
  `usb_app.c` protocol framing through the real `usb_device_if.h`
  byte pipe (`tests/test_usb_framing.c`), on top of the codec
  suite.

**None of that proves enumeration.** A USB device enumerates
against a host controller, a PHY and a 60 MHz ULPI bus; until a
physical board is plugged into a physical laptop, the following
remain unverified BY CONSTRUCTION, and this file is the checklist
for retiring them in order. Nothing in the firmware's docs claims
otherwise; if you find a claim that does, it is a bug in the docs.

## First-power-on sequence (USB part; do the README's power/clock
## steps first; for HV see the interlock decision below - this
## firmware can never enable it, verify instead that it stays off)

1. **PHY clock before stack.** With the board powered and the
   firmware running, probe ULPI_CK (PA5): the USB3300 must be
   delivering 60 MHz. Absent clock = stop here; suspects, in
   order: PA4 reset level (USB3300 RESET is active high; firmware
   releases it in `usb_dev_init`), REG_EN / 3.3 V at the PHY,
   24 MHz at XI/XO, crystal load caps.
2. **Analog switches.** There is no software readout that proves
   the SYSCFG PMCR step worked; its observable symptom is "clock
   present, DIR/NXT dead, no enumeration". If step 1 passes and
   step 3 fails, re-check the PMCR offset and the PC2SO/PC3SO bit
   positions in `usb_device_tinyusb.c` against RM0468 before
   suspecting anything else (docs/04, bring-up item #1).
3. **Enumeration.** Plug into a Linux host and watch `dmesg`:
   expect VID 0x1209 / PID 0xD723 and a `/dev/ttyACM*` node. Any
   failure, capture the exchange on a USB protocol analyser and
   diff the descriptors against `src/usb_descriptors_data.h`
   (they are host-audited, so a mismatch means the wire, not the
   bytes). Repeat on macOS and Windows — usbser.sys binds standard
   CDC ACM on Windows 10/11, but "binds" is a claim only a Windows
   machine can cash.
4. **Interrupt path.** In a debugger, confirm after `usb_dev_init`:
   NVIC ISER2 bit 13 set (OTG_HS IRQ 77 enabled by the stack) and
   vector slot 93 = `OTG_HS_IRQHandler` (statically checked
   against the built ELF at software time; re-confirm on the
   flashed image).
5. **Command round trip on hardware.** Run the host tool's
   hardware path — `python3 host/rxhost.py info` (needs pyserial:
   `pip install pyserial`; it auto-detects the board by VID:PID,
   or pass `--port`) — or a serial terminal at any baud (CDC ACM
   ignores line coding for the data pipe) and issue GET_INFO:
   expect the `PDRX` reply. Then SET_THRESHOLD / GET_STATUS, and
   only then STREAM_START against the CDR.
6. **Suspend / resume.** Let the host sleep the port
   (laptop lid, `uhubctl`, OS sleep): the device must suspend
   (TinyUSB handles the state machine; the descriptors do not
   advertise remote wakeup, so the host must not expect any) and
   either resume or cleanly re-enumerate on wake. Repeat against
   at least two different host controllers.
7. **Stream soak.** Stream capture data continuously for an hour.
   Known performance unknown: the DWC2 runs in slave mode (CPU
   copies the FIFOs) because this firmware's `.bss` lives in DTCM,
   which the OTG DMA engine cannot address. If throughput or CPU
   load disappoints, the fix is mechanical — move TinyUSB's
   buffers into the AXI SRAM section, add M7 cache maintenance,
   flip `CFG_TUD_DWC2_DMA_ENABLE` — but it reopens exactly the
   verification this step performs.

## Decisions and conflicts a human must close

- **PA4 double-claim — RESOLVED (2026-11-04, commit on
  `fw-dac-spi3`).** The schematic (authoritative,
  `hw/CONNECTIONS.md`; generator `hw/circuit.py` agrees) assigns
  PA4 to USB3300 RESET, and the DAC8562 to SPI3 (PC10 SCK,
  PC12 MOSI) with PA15 as SYNC. `board.h` now matches: PA4 is
  referenced only as USB_RST, the DAC defines name SPI3 + PA15,
  `spi.c` points at SPI3 and performs the PC10/PC12 AF hookup,
  and the SPI3 clock gate is enabled in `clocks.c` (the SPI1
  gate it replaced is gone). Before this fix every
  `dac8562_set_threshold()` call pulsed the PHY reset line;
  that failure mode no longer exists in the pin map. A host test
  (`tests/test_dac8562.c`, in `make host-test`) links the real
  driver against mock backends and asserts SYNC is framed on
  PA15 and PA4 is never touched. What remains unverified is the
  usual register-level kind: SPI3 base/AF number/RCC bit are
  marked VERIFY against RM0468 and the datasheet AF table.
- **HV pins were invented; interlock did not exist — pins
  RESOLVED (2026-11-04, `fw-hv-pins`); interlock FITTED as J5 and
  the HV rail hardware-bounded in the hvfix change (same day).**
  `board.h` claimed PB0 = HV enable, PB1 = interlock sense,
  PB2 = ADN2813 LOS, with comments describing an AND gate and a
  series interlock jumper. The drawn design (inventory:
  `docs/06-hv-cdr-pin-inventory.md`) has none of it: PB0/PB1 are
  ULPI data lines D1/D2, PB2 is unassigned. As drawn, the real
  converter could never have been driven by that firmware at all.
  Now: HV control is **PC7 (net HV_EN)**, reaching the LT3757's
  SHDN/UVLO node (net HV_SHDN) through the J5 interlock jumper;
  the re-ratioed R25 143 kΩ / R26 33 kΩ divider holds the node at
  0.94 V, below the 1.17 V minimum threshold, so the converter is
  off at power-up by hardware and firmware's PC7-low init is the
  fitted-jumper clamp, not the only thing keeping HV off. The
  set-point network is likewise re-valued so no DAC state can
  demand more than 253.2 V (259.4 V worst-case) from the fitted
  C30737 (docs/03). ADN2813 **LOS is PB14,
  LOL is PA2**, both LVTTL active-high, read as GPIOs (they were
  previously an unconnected pin and an unverified I2C register bit
  respectively). SQUELCH (PB15), drawn but previously undriven, is
  now driven low (outputs enabled) at init instead of floating.
  **The interlock:** the requirement text (docs/01 R9, docs/02)
  assumed an interlock the original rev A did not fit — the
  inventory searched all 213 nets, every part and the full MCU
  pin list. The owner then delegated the decision (2026-11-04)
  and it is implemented (docs/06): J5, a 2-pin jumper in series
  in the PC7 path — absent, no firmware state can start the
  converter; fitted, PC7 control works — plus a PA6/ADC1 sense
  of the node so `hv_ctrl_enable()` refuses (SET_BIAS →
  INTERLOCK) exactly while the jumper is sensed absent, and
  drops HV if it is pulled mid-run. The bench checks: J5 absent —
  rail 0 V under any command, SET_BIAS answered with INTERLOCK,
  SHDN node at its ≈0.94 V divider level; J5 fitted — enable,
  ramp and the docs/05 §5 interlock sequence. Also corrected
  while here: `hv_ctrl.h` credited the board with an independent
  OVP zener clamp from docs/02; no such part is drawn — the drawn
  protections are the LT3757 current limit, the R30 bleeder, the
  fitted network's hardware ceiling and the J5 gate.
- **VID/PID are unregistered development ids** (0x1209 /
  0xD723, the former being pid.codes' open-source VID). Register
  a PID at pid.codes or obtain a VID before any distribution;
  the host tool must be updated to match whatever is chosen.
- **Declared power vs. design budget.** The configuration
  descriptor declares 500 mA — the most a USB 2.0 device may
  declare — while docs/03 budgets the board at < 4.5 W from the
  USB-C input. Whether the difference is carried by USB-C current
  advertisement (a sink-side matter, outside the USB device
  descriptors) is a design-review decision; the descriptor was
  not made to lie about it.
- **Serial number** is the placeholder string "0001". Deriving
  it from the STM32's 96-bit UID is a small, contained change in
  `usb_descriptors.c` if per-unit serials are ever wanted.
- **VBUS sensing** is disabled in the OTG core (explicit in
  `usb_dev_init`): the USB3300 owns VBUS on this board (its VBUS
  pin is the connector's) and reports session state over ULPI.
  If plug/unplug behaviour is odd on some host, this is the knob
  (`tud_configure` DWC2 `vbus_sensing`), to be changed only with
  analyser evidence in hand.
