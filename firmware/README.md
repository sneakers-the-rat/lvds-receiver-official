# Firmware - photodiode LVDS receiver (STM32H723)

## Build

```
make host-test   # codec library + tests, host gcc, no cross-compiler needed
make arm         # cross-compile to build/rxfw.elf + build/rxfw.bin
                 # (needs arm-none-eabi-gcc; fails with a clear message
                 #  if it is not installed - it never fakes a build)
make clean
```

Status at the time of writing: `make host-test` passes (25 PASS lines,
exit 0, zero warnings under `-std=c99 -Wall -Wextra -Werror`), and
`make arm` builds cleanly with arm-none-eabi-gcc 13.2.1
(text 4472 B, bss 104 B in DTCM, 16 KB capture buffers in AXI SRAM,
vector table at 0x08000000). A successful compile is **not** a claim
that the firmware runs correctly on the board - nothing here has
touched real hardware yet; see "unverified" below.

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
- `adn2813.c`: transaction logic complete, but the ADN2813 is **not**
  in `datasheets/` - its register numbers, rate-readback scaling and
  the I2C address are placeholders, all marked VERIFY. Do not trust
  any value from this driver until they are filled in.
- `hv_ctrl.c`: logic complete (temperature compensation
  Vset(T) = Vset25 + 1.3 V/C x (T - 25) for the C30737, 5 V/s slew
  limit, interlock drop-out, fail-safe on invalid temperature); the
  DAC-counts-to-volts scale assumes a 0-420 V feedback divider -
  VERIFY against the HV design.
- `capture.c`: state machine + AXI SRAM double buffer complete; the
  DMA/timer feed is a commented sketch (`capture_board_dma_init_sketch`,
  deliberately writes no registers).
- Pin assignments in `board.h` are design intent, including one
  known unresolved conflict (PA5 = status LED vs SPI1 SCK) that the
  schematic must settle.

## What does NOT work yet (honest list)

- **USB enumeration does not work.** The device layer
  (`usb_device_if.h` / `usb_device_stub.c`) is a stub returning
  `USB_DEV_NOT_IMPLEMENTED`. Implementing it needs the ULPI/USB3300
  bring-up sequence + OTG HS core init + a device protocol engine,
  listed step by step in `usb_device_if.h`. Board programming does
  not depend on it (STM32 ROM DFU bootloader, per docs/02).
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
4. Resolve the PA5 LED-vs-SCK pin conflict with the schematic;
   finalise all pin/AF assignments in `board.h` + `gpio.c` + `spi.c`.
5. Verify the HV feedback divider ratio; fix `HV_FULL_SCALE_V` in
   `hv_ctrl.h`; confirm the interlock and LOS polarities.
6. First power-up on a current-limited supply: confirm 550 MHz
   SYSCLK (e.g. MCO or a SysTick-timed LED), then I2C presence of
   TMP117 (ID register) and ADN2813, then DAC output voltages on a
   meter, HV **last** and only with the interlock in place.
7. Decide the CDR-to-MCU capture peripheral (SPI slave vs timer
   path) at schematic time; implement the DMA programming sketched
   in `capture.c`; verify DMA can reach the AXI SRAM buffers.
8. Implement the USB device layer per `usb_device_if.h`
   (ULPI PHY + OTG HS + descriptors + bulk/CDC endpoints); wire
   `usb_app_process()` frames to it.
9. Cross-check the firmware PRBS-15 bit convention against the host
   tool's implementation on a loopback before trusting BER numbers.
10. Extend `startup.c`'s vector table before enabling any peripheral
    interrupt (it currently covers only the core exceptions).
