# Photodiode LVDS Receiver — 50 Mbps optical receiver module

Replacement for the SiPM-based receiver (Hamamatsu C15522-3010SA module) used for the
optical uplink in Miniscope Zero (Sasatani et al., bioRxiv 2026.09.05.745822).

Design target (set by the customer, not taken from the paper):
- 50 Mbps line rate, 8b/10b coding, 40 Mbps payload, UI = 20 ns
- The paper's mode, as transmitted: Manchester-coded 8 Mbps data (16 Mbaud)
- Optical in (630 nm red / 740 nm NIR channels of the paper), LVDS out (TIA/EIA-644)
- USB-programmable and USB-verifiable from any laptop, no FPGA, no programmer dongle
- Detector: linear-mode Si APD (SiPM rejected: see docs/02-architecture.md)

Status board, stage log and test results: docs/00-status.md
Requirements derived from the paper: docs/01-requirements.md
Architecture and part selection: docs/02-architecture.md
Link budget / noise calculations: sim/link_budget.py (outputs results/link_budget.txt)
Simulations: sim/ (ngspice + Python, each with a pass/fail check)
Firmware: firmware/ (STM32H723 + USB3300 USB-HS, CDC + vendor bulk)
Host tool: host/ (Python, pyusb/serial, PRBS + 8b/10b + Manchester verify)
Hardware: hw/ (KiCad 7 project, generated fabrication outputs in hw/fab/)

Clean-room statement: this design was written from the paper, manufacturer
datasheets (in datasheets/) and first-principles calculations only. No existing
KiCad project was consulted or copied.
