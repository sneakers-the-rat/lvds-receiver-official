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

## CI fix pass, round 3 (2026-11-03, branch ci-fix)

Branch CI run 41728446884 gave the first full native KiCad 8 ERC
census after the round-1 grid snap: ERC 875 -> 184 = 8 errors + 176
warnings. endpoint_off_grid and pin_to_pin: ELIMINATED. The two
remaining classes, both fixed at the generator:

1. 8 errors, all [power_pin_not_driven] — root cause was NOT missing
   flags. All 11 PWR_FLAGs existed (one per POWER_NETS net + the two
   PHY rails) with correct stub wires and labels, but the embedded
   lib_symbols definition kept the bare library name "PWR_FLAG"
   while instances reference lib_id "power:PWR_FLAG"; KiCad resolves
   embedded definitions by the nickname-prefixed name (the generator
   already renames its custom defs to "pdlvds:..."), so every flag
   instance was unresolved and electrically inert — no pin, no
   power_out on its net. That is why the round-1 PHY flags changed
   nothing. Proof (minimal probe, kicad-cli netlist, KiCad's own
   verbatim PWR_FLAG block): a pin placed exactly on the flag pin
   stayed "unconnected-(R1-Pad1)" with the bare name and joined a
   real net ("Net-(R1-Pad1)") with the prefixed name. The 8 reported
   nets are exactly the flag-dependent nets containing power_in pins
   but no real power_out pin (GND, +5V, -VA, NEG_RAW, +3V3D,
   +3V3D_CDR, PHY_1V8, PHY_1V8A); each confirmed in hw/circuit.py as
   a genuinely driven rail (connector/regulator pins typed passive)
   — declaration gaps, not undriven nets. +VA/+3V3A have real
   power_out pins (LT3042 OUT); APD_K has no power_in pins. Fix in
   gen_schematic.py: embed the definition as "power:PWR_FLAG".
   The bug survived two rounds because kicadxml netlists never list
   power-symbol nodes (verified for power:GND too), so the netlist
   diff could not see it; check_netlist.py now also verifies that
   every instance lib_id resolves to an embedded definition of the
   same name (tested both ways: PASS now, and it flags the pre-fix
   schematic with exactly the power:PWR_FLAG error).
2. 176 warnings = 88 [no_connect_dangling] + 88
   [no_connect_connected], paired at identical coordinates. The
   generator put explicit NC markers on pins whose symbol pin type
   is already no_connect — a double declaration KiCad flags from
   both sides. Census via the generator's own part_pins(): exactly
   88 net-None pins are typed no_connect (U1 x3, U6/STM32 x83,
   T1 x2), matching 88+88 one-for-one. Fix: markers are now emitted
   only for net-None pins of other types (12 remain: output /
   passive / open_collector pins intentionally unconnected).

Verification (local): schematic regenerated after each fix;
instances/labels/wires coordinate sets unchanged (155/541/541);
markers 100 -> 12; netlist check PASS — 630 connected pins, 213
nets, identical to the pre-fix baseline. No ERC category silenced,
no severity touched. NOT claimed here: a KiCad 8 ERC number (none
exists locally); the expectation that errors reach 0 and both NC
warning classes collapse by 88 rests on the mechanism evidence
above and is for the next CI run's report to confirm.

## CI fix pass, round 4 (2026-11-03, branch ci-fix)

The main-branch CI run on 264d58b (the round-3 merge) confirmed the
round-3 expectation and priced the flags' new electrical life: ERC
184 -> 13 total = 2 errors + 11 warnings. Both remaining classes
trace to the PWR_FLAGs, and both are addressed here.

1. 2 errors, both [pin_to_pin] "Power output and Power output
   connected": a flag on +VA facing U13 pin 10 [OUT, Power output],
   and a flag on +3V3A facing U14 pin 10 [OUT]. Round 1 flagged
   every rail indiscriminately; while the flags were dead (the
   round-3 lib_id bug) that was invisible. +VA/+3V3A are driven by
   LT3042 OUT pins — genuine power outputs — and were never among
   the 8 power_pin_not_driven nets. Fix: flag placement in
   gen_schematic.py is now data-driven. flag_nets() computes the
   flag set from circuit.py pin data (via part_pins()): a net is
   flagged iff it contains at least one power_in pin and no
   power_out pin — a PWR_FLAG is itself a power_out to ERC, so it
   belongs exactly on nets that have loads to drive and no driver.
   Measured census behind the change: +VA 3 power_in / 1 power_out,
   +3V3A 7 / 1, APD_K 0 power_in (8 passive pins) — precisely the
   three flags the rule removes. APD_K's flag goes too: correct,
   there is nothing on that net for a flag to drive. The PHY rails
   (PHY_1V8, PHY_1V8A) are no longer appended by hand; they fall
   out of the rule (power_in loads on U7, no power_out). Result:
   11 flags -> 8 (GND, +5V, +3V3D, -VA, NEG_RAW, +3V3D_CDR,
   PHY_1V8, PHY_1V8A). Verified locally (KiCad 7.0.11): schematic
   regenerated; the 8 remaining flag instances sit on exactly
   those nets (paired with their stub labels); label count
   541 -> 538 (the three removed flag labels); the kicadxml
   pin->net map is identical to the pre-fix baseline export;
   check_netlist PASS — 630 connected pins, 213 nets, including
   the round-3 lib_id-resolution check.

2. 11 warnings, all [lib_symbol_issues] "The current configuration
   does not include the library 'power'", one per flag instance.
   Action taken: hw/sym-lib-table now also declares the 'power'
   library, at ${KICAD8_SYMBOL_DIR}/power.kicad_sym (CI runs
   KiCad 8.0.9 and installs kicad-symbols, so the file exists
   there). The project table previously declared only 'pdlvds',
   and the headless CI environment has no configured global table
   to fall back on. The embedded flag definitions are kept, so
   the schematic remains self-contained and local KiCad 7 still
   resolves it. Local gate (KiCad 7.0.11): netlist export exits 0
   with no diagnostics, check_netlist PASS at baseline, pin->net
   map identical. Whether the declaration clears the warning
   under KiCad 8 is NOT claimed here — it is for the next CI run's
   report to show. If it persists (e.g. the complaint mutates
   because the stock v8 PWR_FLAG differs from the embedded
   v7-derived copy), the standing justification is: the symbols
   resolve from the embedded definitions; the warning is a
   library-table configuration note in the headless CI
   environment; electrical ERC is unaffected — the proof is item
   1 itself, since ERC could only report power outputs colliding
   on +VA/+3V3A because the flags are electrically live on those
   nets. Note the count coupling: if the warning does recur it
   will number 8, not 11 — one per remaining flag.

Expectation (not a claim): ERC errors 2 -> 0; warnings 11 -> 0 if
the table declaration satisfies KiCad 8's library check, else 8
justified-standing [lib_symbol_issues]. The parent verifies from
the next main CI run's ERC report. No ERC category silenced, no
severity touched, in this round either.
## Routing history gallery (2026-11-03, branch routing-history)

Per the user's direction, every routing attempt is now committed and
snapshotted as it happens, and the site shows the evolution — failed
attempts included, unpolished.

- `scripts/snapshot_route.py` snapshots one attempt into
  `history/<UTC-timestamp>_<short-hash>/` (kicad-cli top/bottom SVG
  renders, stats.txt) and maintains `history/index.json`. Stats are
  parsed from the audit/build log or given explicitly; anything not
  measured is recorded as "not recorded". Idempotent per commit hash.
  Convention for future attempts: commit the attempt, run the script,
  commit the history/ update. See `history/README.md`.
- Backfilled six entries from git history (boards extracted read-only
  from the main repo at their real hashes/timestamps): router v1
  (dc6a010, 125 pins failed, no board committed), placed-unrouted
  waypoint (d0c0bca, renders), router v2 (c79defe, no board committed),
  router v3 (3ac1a43, 57/112 nets, 90 failed, renders), router v4
  (41d7196, 67/112, 59 failed, 454 violating pairs per f8b9d1c,
  renders), router v5 (fb2acf7, 58/112, 74 failed, 341 clearance /
  98 unconnected / audit FAIL from its committed audit, renders).
- `scripts/build_site.py` gained a "Routing history" section (nav
  linked): chronological gallery with timestamp, commit hash, the
  real stats and renders per attempt; board-less attempts show an
  explicit no-render note; the section builds with zero entries too.
  Verified in a full local build (all 6 entries present) and a
  zero-history build (placeholder line).
- CI: no workflow change needed — build-site already builds from a
  fresh full checkout (history/ is tracked) and runs build_site.py
  there; the tolerant artifact downloads do not touch history/.

## Routing history gallery, round 2 (2026-11-03, branch routing-history)

The combined top/bottom renders stack all four copper layers in one
export, but opaque F.Cu copper and pours hide the inner layers — the
gallery read as top-layer-only. Now every board-bearing snapshot
also carries one recoloured render per copper layer, and the
gallery leads with a composite that stacks all four:

- `scripts/snapshot_route.py` additionally exports each copper
  layer singly (`kicad-cli pcb export svg --layers <one>`) and
  rewrites the layer geometry colour to the fixed palette
  (F.Cu #FF3B30, In1.Cu #FF9500, In2.Cu #34C759, B.Cu #0A84FF);
  the white/grey hole rendering and black wrapper groups are kept.
  Verified on the v4 board: recoloured counts equal the raw census
  (2194/58/250/162 geometry tokens) and all four exports share the
  combined view's viewBox (105.6894 x 85.0138), so stacked layers
  register pixel-perfectly. `index.json` entries gained a `layers`
  map; `stats.txt` lists the layer renders.
- `scripts/build_site.py` gallery: per board-bearing entry, a
  composite (four layer SVGs stacked, `mix-blend-mode: screen`,
  opacity 0.55, background #111), a palette legend, the four
  individual layer panels, then the existing top/bottom reference
  renders. Board-less entries unchanged (explicit no-render note);
  zero-history builds still show the placeholder.
- The four board-bearing backfills (d0c0bca placed, 3ac1a43 v3,
  41d7196 v4, fb2acf7 v5) were regenerated in place — same dirs,
  timestamps, hashes, labels, notes and stats (cross-checked
  field-by-field against the previous index.json); boards were
  re-extracted read-only via `git show` at the original commits
  and stats pinned with explicit flags. Verified in a full local
  site build: 16 layer SVGs copied to `site/assets/history/`,
  4 composites / 12 stacked images in the HTML, each layer file
  referenced exactly twice per entry (composite + panel).
  `history/README.md` documents the palette, file layout and
  composite convention.

## Routing history gallery, round 2 addendum — route-only renders (2026-11-03)

Spec change from the user (14:51 PST): the opaque layers block the
actual routes — renders must show routes only. All gallery renders
(per-layer, composite, and the top/bottom references) are now made
from a temp pcbnew copy of the board with its zones deleted, so
they show tracks, vias and pads with no GND pours.

- Method, with the failed first attempt on record:
  `ZONE.SetIsFilled(False)` persists in the saved board but KiCad
  7's plotter draws the zones' stored filled polygons regardless
  (F.Cu export 830,046 → 830,055 bytes, identical path count).
  Deleting the zones from the temp copy works — largest filled
  F.Cu shape 7,821 mm² (pour) → 10 mm² (pad); 1,123 tracks and
  144 footprints intact on the v5 board. The source board is never
  modified (sha256 identical across a snapshot run); the method
  is recorded per snapshot in `stats.txt` / index `render_method`.
- Silkscreen is excluded from the per-layer and composite views
  (single-layer exports never contained it); it remains only in
  the top/bottom reference renders, which are now also exported
  from the zone-deleted copy.
- The four board-bearing backfills were regenerated a second time
  under this method — same dirs/timestamps/hashes/labels/notes/
  stats (cross-checked field-by-field again), plus a new
  objective check: no layer render of any entry contains a filled
  shape larger than 10 mm². Site rebuilt and re-verified
  (4 composites, 12 stacked images, 16 layer assets, route-only
  wording in the gallery intro and headings; built site shrank
  24.9 MB → 19.8 MB with the pours gone). `history/README.md`
  documents the method, including why SetIsFilled was rejected.
