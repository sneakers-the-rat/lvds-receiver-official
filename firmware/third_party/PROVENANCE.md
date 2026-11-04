# Third-party code provenance

## TinyUSB — `tinyusb/`

- **What:** TinyUSB USB device stack (device core, CDC class driver,
  Synopsys DWC2 device controller driver). Used as the USB device
  transport under `src/usb_device_if.h`; see `src/usb_device_tinyusb.c`.
- **Source (canonical, upstream):** https://github.com/hathach/tinyusb
- **Release:** tag `0.21.0`
- **Commit:** `dae3f9a366bfcddbf9dcf1b48d7500286a849539`
- **Fetched:** 2026-11-04, `git clone --depth 1 --branch 0.21.0`
  from the official repository above. No other mirror was used.
- **What is vendored here:** the upstream `src/` tree and `LICENSE`,
  copied verbatim (no local modifications to any TinyUSB file).
  Upstream `hw/` (board support packages), `examples/`, `test/` and
  `docs/` are **not** vendored: board support for this board lives in
  this repo (`src/usb_device_tinyusb.c`, `src/tinyusb_port/`), which
  is the split TinyUSB is designed for.
- **License:** MIT (see `tinyusb/LICENSE`).
- **Local interface points (ours, not upstream):**
  - `src/tinyusb_port/tusb_config.h` — stack configuration.
  - `src/tinyusb_port/stm32h7xx.h` — a minimal shim supplying the
    handful of CMSIS symbols TinyUSB's STM32 DWC2 port header
    (`dwc2_stm32.h`) references, because this repo carries no ST
    vendor headers by policy. It defines only: the OTG HS peripheral
    base address, the OTG HS IRQ number, `IRQn_Type`, NVIC
    enable/disable inlines (ARM-architectural NVIC addresses), a
    `__NOP` inline, and the `SystemCoreClock` extern. The address and
    IRQ number carry the same VERIFY-against-RM0468 status as every
    other constant in `src/board.h`.
  - `src/usb_descriptors.c` / `src/usb_descriptors_data.h` —
    descriptors (TinyUSB serves them through its callbacks).
