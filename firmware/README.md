# Firmware - photodiode LVDS receiver (STM32H723)

## Build

```
make host-test   # codec library + tests, host gcc, no cross-compiler needed
make arm         # cross-compile to build/rxfw.elf + build/rxfw.bin
                 # (needs arm-none-eabi-gcc; fails with a clear message
                 #  if it is not installed - it never fakes a build)
make clean
```

Status at the time of writing: `make host-test` passes all three
suites (57 PASS lines, exit 0, zero warnings under
`-std=c99 -Wall -Wextra -Werror`): the codec suite (25, unchanged),
the USB descriptor audit (19) and the USB framing round-trip (13).
`make arm` builds cleanly with arm-none-eabi-gcc 13.2.1: text
17732 B, data 36 B, bss 19840 B (16 KB of it the AXI SRAM capture
buffers), vector table at 0x08000000 with the OTG_HS handler at
slot 93 (checked against the built ELF). Against the stub build
(text 4472 B, bss 16488 B) the USB transport costs +13260 B of
flash and +3352 B of bss. A successful compile is **not** a claim
that the firmware runs correctly on the board - nothing here has
touched real hardware yet; see "unverified" below and
`BRINGUP.md`.

## What is complete

`codec/` - portable C99, no hardware or libc dependencies, host-tested:

- **8b/10b** encode/decode with running disparity (Widmer-Franaszek
  tables), K28.5 encode/decode (comma), code-group and disparity
  error flags. Tested exhaustively: all 256 bytes from both starting
  disparities, a 4096-symbol chained-RD stream, error-flag cases.
  Bit-order convention is documented in `codec.h` (K28.5 = 0x0FA at
  RD-, 0x305 at RD+). Only K28.5 is guaranteed as a control decode;
  other K28.y decode best-effort.
- **Manchester** encode (byte -> 16 chips, IEEE 802.3 convention,
  MSB first) and decode from a fed chip stream, plus a 2x-oversampled
  input API that decides each chip by its mid-chip (second) sample.
  Invalid chip pairs (00/11) are counted and dropped.
- **PRBS-15** (x^15 + x^14 + 1) generator/checker replicating the
  Miniscope Zero PER test mode: reseed per buffer with
  `seed = (buffer_count & 0x7FFF) | 1`, 5032-byte (40256-bit) buffers,
  exact bit-error counting, one-shot and streaming checkers. The LFSR
  bit convention is written down in `codec.h`; the test verifies the
  period is exactly 32767 bits and that 5 injected bit flips count
  as exactly 5 errors. Any host-side PRBS implementation must match
  the documented convention bit-for-bit - cross-check that before
  comparing BER numbers across implementations.
- **Paper packet** build/parse: sync word `0xC0FFEE11` (project-
  specific, ours - the paper uses a preamble/dummy words), then the
  11-word little-endian header in the paper's order (frame index,
  global packet, packet in frame, timestamp, pixel count, battery,
  vin, 4 reserved), then the 5032-byte payload. Wire size 5080 bytes.

`src/usb_app.c` - the application-level host protocol is complete
and transport-independent: GET_INFO, SET_BIAS, SET_THRESHOLD,
GET_STATUS, BER_TEST_START/STOP, STREAM_START/STOP over byte
buffers, including BER scoring that applies the paper's rule (a
5032-byte buffer with any error bit is one failed packet).

USB transport - the device layer behind `usb_device_if.h` is now
implemented (`src/usb_device_tinyusb.c` + `src/usb_descriptors.c`,
descriptors in `src/usb_descriptors_data.h`) on **TinyUSB 0.21.0**
(vendored verbatim from github.com/hathach/tinyusb; see
`third_party/PROVENANCE.md`), configured as a **CDC ACM** device
on the OTG HS core in ULPI mode behind the board's USB3300:
SYSCFG analog-switch and power setup, ULPI pin/AF setup, PHY reset
on PA4, DWC2 in slave mode (this firmware's `.bss` is in DTCM,
which the OTG DMA engine cannot address), separate HS/FS
descriptor sets (bulk 512 B / 64 B), the OTG_HS interrupt wired to
vector slot 93. The usb_app frames, command responses and streamed
capture data share the one CDC pipe, exactly as `main.c` has
always driven the interface; the host tool's protocol contract is
unchanged. Host-side, the descriptor bytes are audited and the
framing is round-tripped through the real interface
(`tests/`, run by `make host-test`). **None of this proves
enumeration** - that needs a physical board; `BRINGUP.md` is the
bench checklist and lists what remains unprovable without one.
Interface decision recorded: the repo defined no VID/PID and no
class anywhere before this work; CDC ACM (over vendor-specific
bulk) was chosen because it is driver-free on Linux/macOS/Windows
and matches docs/02's stated "CDC control channel". The VID/PID
are unregistered development ids (0x1209 / 0xD723) - see
`BRINGUP.md`.

## What is register-level but UNVERIFIED

`src/` targets the STM32H723 with hand-written register code - no
HAL, no vendor headers exist in this repo. **Every** address,
register offset and bit position in `src/board.h` (and the constants
inside the .c files) is marked `VERIFY against RM0468 at bring-up`.
Known soft spots, called out where they live:

- `clocks.c`: PLL plan is computed and stated (HSE 25 MHz, M=5 ->
  5 MHz, N=110 -> 550 MHz VCO, P=1 -> 550 MHz SYSCLK, AHB /2,
  APB /2), but the VOS0 encoding, flash latency, PLL register field
  positions and divider encodings all need RM0468 checks before the
  clock is raised on real silicon.
- `i2c.c`: transaction logic is complete (pointer write, repeated
  start, polling with timeouts, NACK handling); the TIMINGR value is
  an explicitly-marked placeholder, not a computed one.
- `spi.c`: H7 SPI register layout assumed; field positions marked.
- `dac8562.c`: command/address packing written from the part's
  standard frame format; marked VERIFY against `datasheets/dac8562.pdf`.
- `tmp117.c`: standard TMP117 register map (0x00 temp, 0x0F ID =
  0x0117), 0.0078125 C/LSB; marked VERIFY against the datasheet.
- `adn2813.c`: transaction logic complete. The I2C register numbers
  and rate-readback scaling are placeholders, marked VERIFY (the
  register map is not in `datasheets/`); do not trust values from
  those paths yet. The pin-level facts are settled: I2C address
  0x40 (SADDR5 grounded), LOS (PB14) and LOL (PA2) read as GPIOs,
  both active high per `datasheets/MANIFEST.md`.
- `hv_ctrl.c`: logic complete (temperature compensation
  Vset(T) = Vset25 + 1.3 V/C x (T - 25) for the C30737, 5 V/s slew
  limit, interlock gate with drop-out, fail-safe on invalid
  temperature); the DAC-counts-to-volts scale assumes a 0-420 V
  feedback divider - VERIFY against the HV design. Note the gate
  can never be satisfied on rev A (no interlock input is drawn),
  so as shipped the converter is held off - see BRINGUP.md.
- `capture.c`: state machine + AXI SRAM double buffer complete; the
  DMA/timer feed is a commented sketch (`capture_board_dma_init_sketch`,
  deliberately writes no registers).
- Pin assignments in `board.h` are design intent. The schematic
  (`hw/CONNECTIONS.md`) has since settled three conflicts against
  board.h's initial guesses, and board.h now follows it: the
  status LED is PC9, not PA5 (PA5 is ULPI_CK), and PA4 is the
  USB3300 reset, not the DAC chip select. A third pass found the
  HV/interlock/LOS pins (PB0/PB1/PB2) were invented outright -
  PB0/PB1 are ULPI data lines; the drawn pins are PC7 (HV_SHDN),
  PB14 (CDR LOS) and PA2 (CDR LOL), and no interlock input exists
  (`docs/06-hv-cdr-pin-inventory.md`). The DAC path has since
  been reconciled to the schematic (SPI3 + PA15 SYNC), so
  `dac8562_set_threshold()` no longer touches the PHY reset
  line; a host test locks the pin map. See `BRINGUP.md`.
- The USB glue in `src/usb_device_tinyusb.c` (SYSCFG PMCR,
  RCC/PWR bit positions, ULPI AF numbers) carries the same VERIFY
  status as the rest of `src/`; the TinyUSB stack itself is
  upstream, unmodified.

## What does NOT work yet (honest list)

- **USB enumeration is unproven on hardware.** The device layer
  is implemented (TinyUSB, above) and the stub is gone, but no
  board exists yet: enumeration, the ULPI link, suspend/resume
  against a real host controller and stream throughput in slave
  mode are all unverified until first power-on. `BRINGUP.md`
  lists them as the bench checklist. Board programming does not
  depend on any of it (STM32 ROM DFU bootloader, per docs/02).
- Nothing has run on hardware: no clock, bus, DAC, sensor, CDR, HV
  or capture behaviour has been observed on a real board.

## Remaining for bring-up (in order)

1. Obtain RM0468 + the STM32H723 datasheet; walk every `VERIFY`
   marker in `src/` and correct addresses/offsets/bit fields,
   starting with clocks (VOS0, flash latency) and I2C TIMINGR
   (compute for the real kernel clock).
2. Add the ADN2813 datasheet to `datasheets/`; fill in its register
   map, I2C address and rate scaling in `adn2813.c`.
3. Check DAC8562 frame packing against `datasheets/dac8562.pdf`;
   check TMP117 map against `datasheets/tmp117.pdf`.
4. Pin conflicts: RESOLVED. The schematic's PA5 assignment
   (ULPI_CK; LED on PC9) and PA4 assignment (USB3300 reset) both
   stand, and the DAC path now follows the schematic too (SPI3,
   PC10/PC12, PA15 SYNC) in `board.h` + `gpio.c` + `spi.c` +
   `clocks.c`. Remaining pin work is verification, not
   reconciliation: confirm the AF numbers and RCC bits marked
   VERIFY in `board.h` against RM0468 and the datasheet AF table.
5. Verify the HV feedback divider ratio; fix `HV_FULL_SCALE_V` in
   `hv_ctrl.h`. (LOS/LOL polarities are settled - active high, see
   `adn2813.h`. There is no interlock polarity to confirm: no
   interlock input is drawn on rev A.)
6. First power-up on a current-limited supply: confirm 550 MHz
   SYSCLK (e.g. MCO or a SysTick-timed LED), then I2C presence of
   TMP117 (ID register) and ADN2813, then DAC output voltages on a
   meter. HV **last**, and know that this firmware as shipped can
   never enable it (no interlock input - owner design decision,
   BRINGUP.md); the bench check for HV is that PC7 holds HV_SHDN
   low and the rail stays at 0 V.
7. Decide the CDR-to-MCU capture peripheral (SPI slave vs timer
   path) at schematic time; implement the DMA programming sketched
   in `capture.c`; verify DMA can reach the AXI SRAM buffers.
8. USB device layer: implemented in code (TinyUSB CDC ACM over
   ULPI, above). What remains is hardware verification per
   `BRINGUP.md`: ULPI clock, enumeration on real hosts,
   suspend/resume, stream soak, plus implementing the host tool's
   hardware path (today `host/rxhost.py` speaks to its simulator;
   point it at the CDC device and match the recorded VID/PID).
9. Cross-check the firmware PRBS-15 bit convention against the host
   tool's implementation on a loopback before trusting BER numbers.
10. `startup.c`'s vector table now extends to the OTG_HS slot
    (93), the only peripheral interrupt enabled; extend it the
    same way before enabling any other peripheral IRQ.
