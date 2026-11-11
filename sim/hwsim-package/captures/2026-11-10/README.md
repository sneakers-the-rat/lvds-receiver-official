# HWSIM run record — 2026-11-10 (first execution of this package)

**Verdict: Stage A CONFIRMED. Stage B not attempted (disposition below).**

## Environment

- Firmware: `firmware/build/rxfw.elf`, built by `01-build-firmware.sh`
  (unmodified production build; text 18244 B).
- Renode **v1.17.0**, portable x86_64 tarball from the canonical release
  (github.com/renode/renode/releases/tag/v1.17.0), SHA-256
  `4ba7c68b59e2447f188ef4b4b112fcccd2802582c460beedceb63b84e5605a5f`.
  Self-contained .NET build — no Mono needed (the install script's Mono
  warning is stale).
- `02-install-renode.sh` defect found and corrected by hand: its asset
  grep takes the first `portable` match from the release API, which is
  the **linux-arm64** tarball (SHA-256 `e9051578…`); on this x86_64 VM
  that binary cannot execute. The x86_64 asset
  (`renode-1.17.0.linux-portable.tar.gz`) was fetched instead. The
  script's asset selection should pin the architecture.

## Platform bring-up edits (the record the README asks for)

- `pdlvds_h723.repl`: the standalone MappedMemory block was replaced by
  `using "platforms/cpus/stm32h743.repl"`. Verified first: the bundled
  stm32h7 map is identical to `firmware/linker.ld` (flashBank1 1 MB @
  0x08000000, dtcm 128 KB @ 0x20000000, axiSram 512 KB @ 0x24000000),
  and the include brings the Cortex-M7 CPU plus the H7 peripheral
  models. The H743 model stands in for the H723.
- Runs were driven interactively over stdin (monitor commands echoed
  and answered); the package's `run-device.resc` was not used verbatim
  because its post-`start` `sleep`/`pause` chain did not surface its
  query output in the captured log (run 1, `stageA.log`, was killed by
  the harness timeout at 180 s). `captures/2026-11-10/run-stageA.resc`
  is that first attempt, kept as-is.

## What the runs showed

Three cold starts (`stageA.log`, `stageA2.log`, `stageA3.log`), all
reproducing the same boot trajectory:

1. ELF loads at 0x08000000; initial PC = 0x080001A5 (Reset_Handler),
   SP = 0x20020000 (top of DTCM, per linker.ld).
2. Board init executes on the models: RTC, RCC PLL config, GPIO,
   I2C1 timing — warnings only (unhandled bits), no faults.
3. **Platform gap — SPI3 is not instantiated** in the bundled H7
   platform ("non existing peripheral at 0x40003C00"). The firmware's
   `spi_transfer` (DAC8562 on SPI3) polls the void status register at
   0x40003C14 (PC pinned at 0x080008FA; samples 0x080008F6 / 0x080008FE
   in run 2). The phase burns roughly a minute of wall time across
   millions of polls, then **exits** — boot continues. On real hardware
   SPI3 exists, so this is an emulation-platform gap, not a firmware
   finding; the DAC threshold path is *not* validated by this run.
4. Boot proceeds: ADC config, SYSCFG, then the DWC2 USB device
   controller init (`usb1` register writes from TinyUSB's device
   stack — core soft reset, device speed config) — i.e. execution
   reached `usb_app_init` inside `main`.
5. **Main-loop samples** (run 3, pauses at ≈120 s and ≈150 s):
   PC = **0x08001FFC = `tud_task_ext` + 0x10** and
   PC = **0x080015A6 = `usb_dev_recv` + 0x6** — the TinyUSB task and
   the firmware's own USB receive poll, the two halves of the main
   loop, 30 s apart. No PC sample ever landed in `Default_Handler`
   (0x08000180); no abort or fault appears in any log.

That meets the package's Stage A scoring verbatim: the unmodified ELF
executes past peripheral init into its main loop, sustained and
repeatable from a cold start.

## Stage B disposition — NOT ATTEMPTED

Stage B (bridge the emulated CDC endpoint to the host and drive it
with `host/rxhost.py` per `03-host-tool-test.md`) was not attempted in
this run, for two independent reasons, both recorded rather than
worked around silently:

1. The bundled STM32 DWC2 model initialises under the firmware but
   Renode offers no ready host-visible serial bridge for it in this
   platform; building one is a project of its own (the README's
   fallback — bridging at the firmware's byte-pipe boundary — changes
   what would be validated and should be a deliberate choice).
2. `host/rxhost.py`'s hardware transport is itself a stub ("Hardware
   present-check not implemented in this revision; use --simulate"),
   so there is currently no real host endpoint consumer to drive.

What this run does **not** validate (unchanged from the package's own
framing): USB enumeration against a real host, the DAC/threshold path
(SPI3 gap above), the capture path, and everything analog.
