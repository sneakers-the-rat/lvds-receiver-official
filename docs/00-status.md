# 00 — Status board (updated by the build coordinator after every stage)

Last update: 2026-11-03 (Stage 1/2 in progress)

## Stages
- [ ] 1 TOOLS — apt install still running (see below)
- [ ] 2 DATASHEETS — partial, downloads in progress
- [ ] 3 LINK BUDGET — delegated, running
- [ ] 4 SIMULATIONS — 4c delegated, running; 4a/4b/4d pending
- [ ] 5 FIRMWARE — delegated, running
- [ ] 6 HOST TOOL — python codec delegated with stage 4c; rxhost CLI pending
- [ ] 7 KICAD — pending (needs kicad-cli from stage 1)
- [ ] 8 FINAL DOCS — pending

## Stage 1 — Tools (in progress)
- apt-get install kicad ngspice gcc-arm-none-eabi ... started by the parent
  agent (log /tmp/apt-install.log). As of this update the fetch phase was
  still running: the last fetched package is the 463 MB
  libstdc++-arm-none-eabi-newlib; `which kicad-cli ngspice arm-none-eabi-gcc`
  returns nothing yet; no error in the log, only slow download.
  This is a WAIT, not a failure — stages not needing these tools proceed.
- Present and verified: python3 with numpy 1.26.4 / scipy 1.11.4 /
  matplotlib 3.6.3 (system packages), host gcc, git, pdftotext/pdftoppm.
- Tool versions will be recorded here verbatim once the install lands.

## Stage 2 — Datasheets (in progress)
Valid PDFs on disk (verified `file` = PDF + pdfinfo + text extraction):
C30737 (Excelitas, 14 pp), opa657, lmh7220, dac8562, tmp117 (TI),
s14645 (Hamamatsu, background only), ths4304 (TI) — see MANIFEST.md.
Invalid in the first fetch (HTML error pages, NOT trusted, replaced):
c15522.pdf, usb3300.pdf (400 B).
Missing in the first fetch and re-downloaded from manufacturer sites:
adn2813.pdf (Analog Devices), stm32h723.pdf (ST), lt3757.pdf (Analog
Devices) — download/verification results recorded in MANIFEST.md.
Alternate sources used where the manufacturer CDN failed: USB3300 from the
Octopart datasheet mirror of Microchip DS00001783; S8664 series and
C15522 series from Hamamatsu official PDFs / a Hamamatsu datasheet copy —
each entry in MANIFEST.md states its source URL and validity check.
Pinouts/footprints in MANIFEST.md are extracted from these PDFs only
(text layer + rendered dimension drawings), never from memory.

Key extracted fact (C30737LH, datasheet Fig. 10, rendered and read):
3.00 x 3.00 mm LCC, 6 pads 1.30 x 0.60 mm, pad pitch 1.10 mm;
PAD 5 = POSITIVE (CATHODE), PADS 1,2,3,4,6 = NEGATIVE (ANODE);
photodetector plane 0.65 mm below the package top surface.
C30737LH-500-90 electricals (Table 1): active dia 500 um, Vbr 180 typ /
260 max V (bins C: 180-220, D: 220-260), tempco 1.3 V/degC, responsivity
55 typ / 60 max A/W @900 nm at M=100, Id 0.1 typ / 1 max nA, noise current
0.1 pA/rtHz, Cd 1 pF typ, tr+tf 0.9 ns, fc 380 MHz.

## Paper additions incorporated (2026-11-03)
docs/01-requirements.md now includes: PER trial structure (2^15-1 buffers
per trial, 5 trials averaged), the ~700 cm2 single-receiver coverage
benchmark at PER 1e-3 (frame loss 0.80%), post-hoc multi-receiver stream
combining, diffuse-light reception through translucent maze walls (wide-FOV
bare mode requirement), and the headstage ATSAMD51J20 note (transmitter
side only).

## Next
Finish stage 2 (MANIFEST), integrate stage 3/4c/5 deliverables, then
4a/4b/4d, host CLI, KiCad.
