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
## steps first, HV last and only with the interlock in place)

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
   hardware path (or a serial terminal at any baud — CDC ACM
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

- **PA4 is claimed twice.** The schematic (authoritative,
  `hw/CONNECTIONS.md`) assigns PA4 to USB3300 RESET; `board.h`'s
  older intent and `dac8562.c` use PA4 as the DAC chip select.
  The USB code follows the schematic. Until the DAC path is
  reconciled (schematic: SPI3 + PA15 SYNC), **every
  `dac8562_set_threshold()` call pulses the PHY reset line** and
  will drop USB. This is the single most likely "USB dies when I
  set the threshold" bug; it is a pin-map conflict, not a stack
  bug. (README bring-up item 4.)
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
