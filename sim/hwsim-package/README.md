# Hardware-simulation package (UNTESTED — see REFUSAL-RECORD.md)

Goal: boot the receiver's **real firmware binary** on an emulated STM32H723
wired per the design, bridge its host interface out as a serial device, and
drive it with the repo's own host tool — the closest thing to the physical
device that exists before fabrication.

Every file in this folder was authored without a single execution of the
simulation itself. Expect to debug the platform file; the scoring section
says what counts as success at each stage so a partial run still produces a
verdict.

## Run order

1. `./01-build-firmware.sh`
   Builds the production firmware from this repo (`make arm` in
   `firmware/`). Output: `firmware/build/rxfw.elf`. Requires
   `arm-none-eabi-gcc` (the same toolchain the project already uses).

2. `./02-install-renode.sh`
   Downloads the latest Renode release (portable tarball) from the
   canonical source, github.com/renode/renode, into `./renode/`, and
   prints its SHA-256 for the record. Renode's portable build needs a
   Mono runtime on Linux (`mono` on PATH); the script checks and says so.

3. Start from Renode's bundled STM32H7 platform and apply this design:
   - In the Renode tree, find the bundled H7 platform:
     `find renode -iname '*stm32h7*' -name '*.repl'`
   - Copy it next to `pdlvds_h723.repl` in this folder and reconcile the
     memory map with `pdlvds_h723.repl` (which is generated from
     `firmware/linker.ld`: FLASH 1 MB @ 0x08000000, DTCM 128 KB @
     0x20000000, AXI SRAM 512 KB @ 0x24000000) and the peripheral wiring
     notes in that file (OTG_HS/ULPI, SPI3 DAC, I2C, capture inputs, per
     `hw/CONNECTIONS.md` and `firmware/src/board.h`).

4. `./renode/renode --console run-device.resc`
   Boots the ELF on the platform. `run-device.resc` is staged: Stage A
   boots to the main loop; Stage B (commented) attempts the USB device
   bridge. Uncomment B only after A scores.

5. Host test: follow `03-host-tool-test.md` — point `host/rxhost.py` at
   the bridged serial endpoint and run the full command sequence.

## Capture — save these for every run

- The full Renode console log, with wall-clock timestamps.
- The firmware's own boot output if the platform routes a UART/console.
- The host-tool transcript (commands sent, responses received, verbatim).
- A note of every edit you had to make to `pdlvds_h723.repl` /
  `run-device.resc` to get a stage to run — those edits ARE the platform
  bring-up record.

Save captures under `sim/hwsim-package/captures/<date>/` and commit them;
they convert this package from untested to scored.

## Scoring

- **Stage A CONFIRMED**: the unmodified ELF executes past peripheral init
  into its main loop on the emulated machine (Renode log shows sustained
  execution, no fault/abort), repeatably, from a cold start.
- **Stage B CONFIRMED**: the emulated device enumerates as a USB CDC
  device to a host (or, if bridged at the byte-pipe boundary instead,
  presents a serial endpoint that answers bytes) AND `host/rxhost.py`
  completes the `03-host-tool-test.md` sequence: GET_INFO returns the
  PDRX magic, SET_THRESHOLD reads back in GET_STATUS, SET_BIAS respects
  the interlock both ways, a BER run completes, STREAM starts and stops
  cleanly.
- **INCONCLUSIVE**: a stage runs partially (boots but faults in USB init;
  enumerates but a command hangs). Record where it stopped; that is a
  platform-fidelity finding, not a firmware verdict.
- **REFUTED** (about the approach, not the device): Renode's H7 OTG/USB
  model cannot carry the CDC link at all after a genuine platform
  effort — then the fallback is to record exactly which peripheral model
  is missing, and test the firmware's protocol at the closest real
  boundary the platform does support, labeled as such.

## Cleanup

Remove `./renode/` and any machine state (`rm -rf` is the owner's call,
in the owner's own shell — the project's agents do not run it). The repo
tree returns to baseline by deleting `sim/hwsim-package/captures/` runs
you do not want to keep.
