# 00 — Status board (updated by the build coordinator after every stage)

## LATEST — 2026-11-03 12:36 PST — CI fix for GH Actions run 41710107325

**Failure (diagnosed from the real Actions log, head f531258):** the
single-job workflow died at "Install toolchain" (exit 100, dpkg):
Ubuntu jammy's `ngspice` package and the KiCad 8 PPA's
`libngspice-kicad` both ship `/usr/lib/x86_64-linux-gnu/ngspice/*.cm`
with no Conflicts/Replaces declared, so installing both in one apt
transaction fails. The deploy-pages job was skipped only because its
upstream job failed; Pages itself is enabled (build_type=workflow,
custom domain jon-e.net) and ENABLE_PAGES_DEPLOY is set.

**Fix (chosen: the preferred job split, not --force-overwrite):**
- `.github/workflows/ci.yml` is now four jobs: `kicad-validate`
  (KiCad 8 PPA, **no standalone ngspice**; runs ci.sh step 10 +
  make_fab; uploads `fab-outputs`), `sim-and-firmware` (ngspice +
  ARM gcc + python, **no KiCad**; runs ci.sh steps 1–9; uploads
  `sim-results`), `build-site` (needs both; downloads the two
  artifacts, builds the site, uploads `project-site` + the Pages
  artifact), and `deploy-pages` (unchanged guard:
  `vars.ENABLE_PAGES_DEPLOY == 'true'`).
- `scripts/ci.sh` gained step selection: steps are functions, run per
  the `CI_STEPS` env var (comma list). No CI_STEPS = all 10 steps in
  order, so the local one-command pipeline is unchanged. The ngspice
  TIA step (step 3) is kept and runs in the sim job.
- Validated locally before commit: `bash -n` clean, workflow YAML
  parses (4 jobs), `CI_STEPS=1,9` PASS, `CI_STEPS=3` (TIA/ngspice)
  PASS standalone, unknown step correctly fails the run.

**Local build state at this checkpoint:** the 19:34 VM replacement
wiped the apt toolchain mid-routing; KiCad 7.0.11 / ngspice / ARM gcc
were reinstalled (apt exit 0) and routing resumed with router v3
(neck-down at fine-pitch pads — see git log). PCB audit, fab outputs,
the full local `scripts/ci.sh` run (`results/ci-local-run.txt`) and
the full rewrite of this status board follow when routing lands.

---

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

## CI fix pass (2026-11-03, branch ci-fix)

User-ordered: fix the CI tests and the website deploy so CI gives
useful information. Three root causes, all fixed at the source:

1. TIA sim failed ONLY in CI. Local ngspice is v42, CI (ubuntu-22.04)
   is ngspice 36; the generated AC deck's photocurrent source was
   `Iph 0 inn ac 1` — no DC value. ngspice-36 rejects that ("iph: has
   no value, DC 0 assumed", no analysis runs, exit 1); v42 accepts it.
   sim/run_tia.py now emits `dc 0 ac 1` at both AC-deck sites (the
   noise deck already did). Local rerun: TIA PASS, f-3dB 153.6 MHz,
   peaking 0.00 dB, settle 3.3 ns, noise 0.567 mV rms — unchanged.
   Full local steps 1-9: ALL PASS.
2. KiCad 8 ERC reported 875 violations. Census: 683 endpoint_off_grid,
   88 no_connect_dangling, 88 no_connect_connected, 8
   power_pin_not_driven, 8 pin_to_pin. The schematic generator now
   snaps every placement/pin/wire/label/no-connect coordinate to
   KiCad's 1.27 mm connection grid (verified: 3756 coordinates, 0
   off-grid) with collision-avoiding placement (snapping alone merged
   7 pin pairs across stacked parts; the netlist check caught it and
   passes again: 630 pins / 213 nets, identical connectivity).
   PWR_FLAGs added for PHY_1V8/PHY_1V8A (USB3300 internal rails).
   pin_to_pin was exactly the paralleled same-device pins: TPS62130
   SW x3 (U11/U12) and LT3042 OUTS sense pins (U13/U14) retyped
   "passive" per KiCad convention, one driver pin kept per net.
   Schematic paper A1 -> A0 (the generated layout is ~740 mm tall and
   always overflowed A1). No ERC category silenced, no severity
   changed. Residual ERC census is for the branch CI run (no native
   ERC exists locally — KiCad 7).
   ci.sh step 10 now also prints ERC errors/warnings as separate
   counts; pass/fail semantics unchanged.
3. The site had NEVER built: build-site needed both validation jobs
   green. ci.yml restructured: build-site runs with !cancelled() and
   tolerant artefact downloads; validation jobs upload a status JSON
   (ci step outcome) that the site merges into a new build-status
   panel (per-check PASS/FAIL/not-run from results/ verdicts + ERC/
   DRC counts); deploy-pages publishes whenever build-site succeeded
   and ENABLE_PAGES_DEPLOY is set — regardless of validation outcome.
   Validation jobs still fail honestly (no continue-on-error on any
   check). Fab export and sim-results upload now also run on failure
   so a red run's site shows the current board and partial results.
