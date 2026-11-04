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

## CI speed pass (2026-11-03, branch ci-speed)

Problem, observed from the Actions API ~23:07Z: two concurrent runs
(main 5a70774, routing-history 333cef6) both sat in kicad-validate's
"Install KiCad 8" step for 7+ minutes with no visible progress,
while both runs' sim-and-firmware jobs (plain Ubuntu-archive
installs, no PPA) finished in ~1 minute. Historical KiCad installs
in this workflow took 2–4 min; the sim toolchain install takes
~45 s. In-progress job logs are not retrievable via the API, so a
slow install is indistinguishable from a stall until it finishes.

Root cause priced from the PPA package index (kicad 8.0.9,
2026-11-03): the old step `apt-get install -y kicad xvfb` followed
apt's default Recommends chain — kicad recommends kicad-libraries,
kicad-doc-en and kicad-demos; kicad-libraries in turn recommends
kicad-symbols (2.6 MB), kicad-templates (2.8 MB), kicad-footprints
(22.1 MB) and kicad-packages3d, a 378 MB .deb (4.8 GB installed) of
3D models. Roughly 440 MB came down the Launchpad mirror's variable
throughput on every single run, for packages no step can use: the
only kicad-cli subcommands this pipeline invokes are `sch erc`,
`pcb drc`, `sch export netlist` (scripts/ci.sh step 10) and
`pcb export gerbers|drill|pos|svg|pdf` (scripts/make_fab.sh), and
all of them read the schematic's embedded symbols and the board's
embedded footprints.

Fixes (all in .github/workflows/ci.yml; ci.sh / make_fab.sh /
build_site.py untouched):
- Install is now `apt-get install -y --no-install-recommends kicad
  xvfb` — the 35.7 MB kicad package plus hard Depends (shared
  libraries). xvfb kept deliberately: small, from the fast Ubuntu
  archive, and kicad-cli's wx initialisation has historically
  wanted a display for some export paths.
- actions/cache on /var/cache/apt/archives (restore before install,
  save after on success), keyed on the workflow file's hash — the
  package list lives in that file — with a restore-keys prefix for
  best-effort reuse. /etc/apt/apt.conf.d/docker-clean is removed in
  the install step so downloaded .debs survive to be cached; apt
  reuses version-exact cached .debs without re-downloading. A cache
  miss behaves exactly like the pre-cache workflow.
- update+install in both install steps (KiCad and sim toolchain)
  is wrapped in a 2-attempt retry loop, so a transiently sick
  mirror gets one in-step second chance.
- kicad-validate gains timeout-minutes: 25 (healthy total ~5 min):
  a truly stuck job now fails fast instead of crawling silently.
- Workflow-level concurrency, group <workflow>-<ref> with
  cancel-in-progress: rapid successive pushes to one ref cancel the
  stale run instead of queueing duplicate installs.

NOT claimed: any new install time. The next real runs are the
measurement; before/after will be read from the Actions API.
Watch item for the first slim-install run: hw/sym-lib-table points
its 'power' entry at ${KICAD8_SYMBOL_DIR}/power.kicad_sym from the
kicad-symbols package, which is no longer installed. ERC resolves
this design's symbols from the schematic's embedded definitions
(that is the mechanism CI fix rounds 3–4 proved), so the entry
should be inert — but if the first slim run shows NEW lib-related
ERC diagnostics versus the 0 errors / 8 warnings baseline, that is
the first place to look.
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

## Routing history gallery, round 3 — light-on-dark presentation (2026-11-03, branch routing-history)

Direction history, for the record: the round-3 brief first asked
for white-background-safe (darkened) colours, because several
elements of the round-2 renders are pale. Before any of that was
implemented — investigation only, no commits — the user corrected
the call (15:19 PST): they prefer light-on-dark ("i'd rather you
have it be light-on-dark than dark-on-light, if there's a choice
between them"). Round 3 implements light-on-dark throughout.

- Every gallery render now sits on a dark panel in the site: the
  composite (unchanged round-2 treatment: screen blend on #111),
  the per-layer panels (already #111), and the top/bottom
  reference renders, which previously sat directly on the white
  page — they now carry a `refview` style (#111 background, subtle
  #444 border) so the panel reads as intentional.
- The bright round-2 palette is kept verbatim (F.Cu #FF3B30,
  In1.Cu #FF9500, In2.Cu #34C759, B.Cu #0A84FF) — it was chosen
  for dark. The top/bottom references, previously not recoloured
  at all, now map KiCad's muted theme colours onto that palette.
- Polarity flip handled in the snapshot script's recolouring:
  the invisible-on-dark class is near-black, and the glowing
  class is drill-hole white. Drill holes (#FFFFFF) are rendered
  in the panel tone #111111 so a hole reads as a hole against its
  pad; #000000 → #9E9E9E (verified beforehand: black occurs only
  in inert wrapper group styles — zero circles/paths in black
  groups in every export, layer and reference alike); pads
  (#ECECEC) and silkscreen (#F2EDA1) are kept verbatim, both
  clearly visible on dark.
- The four board-bearing backfills were regenerated under this
  mapping — dirs, timestamps, hashes, labels, notes and stats
  unchanged (index entries and every stats.txt verified
  byte-identical against pre-regen copies; exactly the 24 SVGs
  changed). Objective scan of all 24 produced SVGs: zero
  fill/stroke colours with relative luminance < 0.08 other than
  the designated #111111 panel tone; #000000 and #FFFFFF token
  counts are 0 everywhere; hole-token counts match the pre-regen
  #FFFFFF counts exactly (e.g. v4 top reference 5,880 → 5,880).
  Pale classes survived where the source exports contain them:
  #ECECEC > 0 in every routed snapshot, #F2EDA1 > 0 in all four
  top references; both are absent from the bottom references and
  the unrouted placed board because the raw exports contain none
  there (pre-regen census) — a property of the source, not a loss.
- Site rebuilt locally and verified: 4 composites + 12 stacked
  images, 8 refview reference images on dark panels, 16 layer +
  8 reference SVGs copied into site assets (spot-checked asset
  carries the new mapping), legend shows the bright palette, and
  the gallery intro states the light-on-dark presentation.

## Stage 7c — v6 model rewrite + Freerouting baseline (2026-11-03)

Successor coordinator took over the routing lane at 3211eac.

### Model-gap analysis of the v5 board (hw/analyze_model_gap.py,
results/model-gap-v5.txt)

Every audit-flagged via/track on the v5 board was re-tested against
the v5 router's own clearance model (point-sampled dist_to_item) and
against an exact segment-capsule distance test, using a registry
rebuilt from the final board:

- Vias: 108 flagged positions; the router's own model REJECTS 107 of
  them on the final geometry (worst margin -0.55 mm); 2 accepted are
  APD_K vias whose audit pairs are against zone fills (the registry
  contains no zones).
- Tracks: 131 flagged start points; 110 rejected by BOTH the point
  model and the exact test; only 18 are pure point-sampling gaps
  (point model accepts, exact rejects); 4 accepted by both (3 APD_K +
  1 +3V3D, zone-pair suspects).

Conclusion, superseding the simpler "sampling" story: point sampling
is a real but minority defect (18 tracks). The dominant defect is
that emitted copper pervasively fails the router's own model on the
final board — i.e. emission paths whose tests do not cover the final
geometry: via tests cover only the source+target layers (a via
barrel also occupies the third routing layer), the neck-down width
is chosen by the search from distance-to-any-own-pad but by emit
from distance-along-path (goal-end approaches are drawn wider than
they were tested), goal/own-cell entry steps are exempt from the
track test, and GND stitch vias use an ad-hoc test. The v6 rewrite
therefore makes the invariant structural: every emitted segment and
via is exact-tested, on every layer it occupies, with the same width
the search tested, and no entry exemptions.

Known non-router audit residue on v5 (for the final accounting):
46 cross-footprint pad-pad pairs (placement geometry, e.g. U7 pins
vs U12/L2 pads at the 0.25 mm power clearance) and 18 zone-involved
pairs (mostly HV vias vs the In1 GND plane: audit's buried-HV rule
is 0.3 mm, zone local clearance carves 0.25 mm).

### Freerouting baseline (permitted by the user 2026-11-03 16:21 PST)

- freerouting/freerouting v2.5.0, official GitHub release asset
  freerouting-cli-2.5.0-linux-x64.tar.gz.
- sha256 64a957a9ef2a2fbde6ab2001bb32800f5ba34f9fd15575e363512934b870d63a
  — matches the release's own checksums file exactly.
- Self-contained native CLI (no JRE needed); kept OUTSIDE the repo at
  ~/workspace/tools/freerouting/ with a PROVENANCE.md; binary is not
  committed. Role: baseline/fallback only — the home-grown v6 line
  continues to its own completion regardless (user, 16:22 PST).

## CI signal fix — DRC ratchet instead of a permanent red (2026-11-03, branch ci-signal)

The user's reasoning, in one line (2026-11-03 16:24 PST): an
always-failing CI is worse than none, because a genuinely broken
pipeline step can hide inside the permanent red and send the work
down dead ends.

The problem: the kicad-validate job hard-failed on the raw DRC
count of a board that is known to be mid-routing, so the job was
red on every run regardless of whether anything else broke.

Design (implemented in this branch; board state is reported, never
hidden):

- ERC and DRC are now separate CI steps (scripts/ci.sh steps 10
  and 11). ERC stays a HARD GATE: `kicad-cli sch erc
  --exit-code-violations`, 0 errors required, exactly as before —
  it currently passes and keeps biting.
- DRC (step 11) runs `kicad-cli pcb drc --severity-all` WITHOUT
  --exit-code-violations and hands the report to
  scripts/drc_gate.py, which applies three duties:
  - TOOL HEALTH (hard fail): kicad-cli must run, the board file
    must exist, and the report must be produced, parse (both
    "Found N DRC violations" and "Found N unconnected items"
    summary lines), and carry a plausible census (total items
    > 0 while the baseline says the board is unfinished). Exit 2.
    A crash/empty/unparseable report fails the job — a silently
    broken DRC is precisely the failure mode being fixed.
  - RATCHET (hard fail on regression): counts above
    ci/drc-baseline.json fail the step (exit 1) — routing
    regressed, or the checker changed behaviour; either must be
    seen. Counts at/below baseline pass, printing both numbers.
  - VISIBILITY: the counts are printed prominently in the job
    log, appended to $GITHUB_STEP_SUMMARY, written to
    results/drc-status.json, merged into the site's kicad status
    JSON by the workflow, and shown in the build-status panel
    worded as board state — "DRC (board in progress): 807
    violations, 175 unconnected — baseline 807/175, no
    regression" — never as "DRC passed". The DRC report itself
    still uploads as evidence on every run, pass or fail.
- Baseline seed: 807 violations, 175 unconnected, from the last
  measured KiCad 8 DRC of the current v5 board (main run on
  b5c2b57; the board on main is unchanged since). Provenance is
  recorded inside ci/drc-baseline.json; no run id was available
  in the tasking, so none is claimed. If the first CI run with
  this gate measures the unchanged board differently (report
  format counting differences), that is a calibration event to
  document here, not a silent baseline edit.
- What still HARD-FAILS, unchanged: any ERC error; DRC tool
  health; DRC regression above baseline; and every sim/firmware
  check (codec, link budget, TIA, digital, HV, impedance,
  firmware host tests, ARM build, host tool) in the other job.
- What no longer fails: in-progress DRC counts at or below the
  baseline. The job can now be green while the board is honestly
  unfinished — and red only when something actually broke or
  got worse.
- End state: when routing completes (0 violations, 0
  unconnected), set ci/drc-baseline.json to 0/0. The same gate
  is then a hard zero-tolerance DRC gate by construction (the
  census check applies only while the baseline is > 0, so a
  clean report passes) — no code change beyond the baseline
  file. The workflow comments record this flip next to the job.
- KiCad 7 fallback (local runs) keeps the scripted equivalents:
  netlist check in step 10, the hw/check_pcb.py audit as a hard
  gate in step 11, both loudly labelled as fallbacks. The
  ratchet applies to the native KiCad 8 path used by CI.
- Local verification performed: scripts/drc_gate.py run against
  fixture reports in the summary-line format the repo already
  parses (scripts/build_site.py) — no real DRC report file
  exists under results/ in the repo, so no KiCad 8 report was
  available locally and none is claimed. Results: at-baseline
  (807/175) exit 0; below baseline (700/100) exit 0; doctored
  over-baseline copies (808/175 and 807/176) exit 1; corrupt
  and empty reports exit 2; a 0/0 report against the seeded
  baseline exits 2 (implausible census); a 0/0 report against
  a 0/0 baseline exits 0; missing report exit 2. The workflow
  status-merge snippet was executed standalone and produced
  the expected drc_* fields; the site's drc_row() was executed
  against status-JSON and local-report fixtures for the
  at-baseline, regression, tool-failure, not-run and finished
  0/0 cases with the exact wordings above. ci.yml parses as
  YAML; ci.sh passes bash -n. Local KiCad is v7, so no KiCad 8
  DRC behaviour is claimed from local runs — the first CI run
  on this branch is the calibration check for the counts.

## CI signal fix, round 2 — the first live run caught three real things (2026-11-03, branch ci-signal)

Round 1's design goal was that a broken pipeline step could no
longer hide inside a permanently red job. Its first live run —
GitHub Actions run 41750532660 on main @ ec773ed — proved the
point by catching three real defects in the signal itself, all
invisible before the split. The parent extracted the actual ERC
and DRC reports from that run's evidence artifact; both are now
committed byte-pristine as test fixtures
(ci/fixtures/drc-report-run41750532660.txt,
ci/fixtures/erc-report-run41750532660.txt).

What the run caught:

1. **The ERC step failed over a clean report.**
   `kicad-cli sch erc --exit-code-violations` exits non-zero on
   WARNINGS too in KiCad 8. The step went red while its own
   report said 0 errors / 8 warnings. Round 1 had trusted the
   exit code — the same disease as the old DRC step, one step
   over.
2. **The DRC gate parser failed on the real report format.**
   The gate expected the bare console wording ("Found N
   unconnected items"); the report FILE says
   `** Found 726 DRC violations **` and
   `** Found 190 unconnected pads **` — `**` framing, and pads,
   not items. The gate failed tool-health (exit 2): loudly, as
   designed — the signal caught its own parser.
3. **The seeded baseline measured a different board.** The run
   measured 726 violations / 190 unconnected (console output
   and report file agree) against the seeded 807 / 175.

Fixes (this round):

- **DRC parser** (scripts/drc_gate.py): both summary regexes
  now accept the `**`-framed file format and the bare console
  format, and both nouns (`pads|items`). The identical regex
  pair in scripts/build_site.py's fallback DRC parse got the
  same fix (verified: drc_row() on the real fixture returns
  "DRC (board in progress): 726 violations, 190 unconnected —
  baseline 726/190, no regression").
- **ERC gate** (new scripts/erc_gate.py; ci.sh step 10): ERC
  is invoked WITHOUT --exit-code-violations, any stale report
  is deleted first, the kicad-cli exit code is logged as
  informational only, and the verdict is parsed from the
  report's `** ERC messages: N  Errors E  Warnings W` summary:
  FAIL (exit 1) iff E > 0; missing/empty/unparseable or
  internally inconsistent (N != E + W) report is a tool-health
  FAIL (exit 2) — the same philosophy as the DRC gate. Success
  prints "ERC: 0 errors, 8 warnings (known lib_symbol_issues,
  justified in docs/00-status.md)". The gate stays a HARD gate:
  any real ERC error still fails the job, always. Workflow
  step renamed accordingly; job comments record why.
- **Baseline calibration** (ci/drc-baseline.json): violations
  726, unconnected 190. Justification, git-verified: did
  hw/pdlvds_rx.kicad_pcb change between b5c2b57 (the seed's
  provenance commit) and ec773ed (the run's commit)? YES —
  exactly once. The blob at b5c2b57 is ebe97655 (the pre-v5
  board); commit fb2acf7 (router v5 result) replaced it with
  blob 6a377ebc, which reached main via the routing-work
  merges, and both parents of ec773ed carry 6a377ebc. So the
  seed 807/175 measured the PREVIOUS board and 726/190 is the
  first true measurement of the current (v5) board. The delta
  direction matches v5's own documented trade: its stricter
  clearance model produced fewer violations, and it routed
  fewer nets (58/112 vs v4's 67/112), leaving more
  unconnected. This corrects round 1's statement above that
  the seed came from "the current v5 board" with "the board
  on main unchanged since b5c2b57" — that was wrong; the v5
  board landed on the coordinator line and only later merged.
  The calibration is therefore to a first measurement of a
  changed board, not ratchet-loosening to fit a regression:
  no count was raised above a same-board measurement, because
  none existed. (Violations went DOWN against the seed;
  unconnected went UP — above the stale seed, which is
  precisely why the first live run flagged it instead of
  silently passing.)
- **Committed tests** (ci/test_gates.py, 21 checks, all
  passing): round-1 semantics recreated as synthetic
  console-format cases against a temporary 807/175 baseline;
  round-2 cases run both gates against the REAL fixtures —
  DRC exit 0 at 726/190, exit 1 on either doctored count,
  exit 2 on corrupt/empty/missing; ERC exit 0 with the exact
  success line, exit 1 on a doctored Errors 1, exit 2 on
  corrupt/empty/missing/inconsistent. ci.sh passes bash -n;
  ci.yml parses as YAML. Local KiCad is v7, so no local
  kicad-cli ERC/DRC behaviour is claimed — the gates were
  tested against the captured KiCad 8 reports, which are the
  ground truth for the formats.

Remaining verification: the next CI run on main with this
round merged should be GREEN — sim-and-firmware unchanged,
ERC hard-pass on the parsed report (0 errors / 8 warnings),
DRC step passing as board state at 726 violations / 190
unconnected against the calibrated baseline, site deploying
with the panel showing those counts as board state. If that
run measures different DRC counts for the unchanged board,
that is a new calibration event to document here, not a
silent baseline edit.

## CI signal fix, round 3 — checker jitter is not a regression (2026-11-03, branch ci-signal)

Round 2's closing paragraph said: if a later run measures
different DRC counts for the unchanged board, that is a new
calibration event to document here, not a silent baseline edit.
That event happened on the very next run. GitHub Actions run
41751841325 measured **727 violations / 190 unconnected** where
run 41750532660 had measured **726 / 190** — on the IDENTICAL
board: both runs carry board blob
`6a377ebcdb64282f3e0857f522c2f4b960e9fe93`, and the ci-signal
rounds touched no board files, so nothing about the board
changed between the two measurements. The round-2 ratchet did
exactly what it was built to do — it fired REGRESSION on the
rise — but the rise is the checker, not the routing: KiCad 8's
DRC has ±1 run-to-run jitter on violations for this board
(unconnected was stable at 190 in both runs). A gate that cries
regression on jitter trains everyone to ignore it, which is
the permanently-red disease in a subtler form.

The fix is a tolerance, not a re-baseline:

- **ci/drc-baseline.json** gains `tolerance_violations: 5` and
  `tolerance_unconnected: 2`. The baseline itself STAYS
  726/190 — the reference measurement from run 41750532660.
  The baseline is deliberately NOT raised to 727: the tolerance
  is the jitter mechanism, the baseline stays the reference, so
  drift remains visible against a fixed point instead of being
  absorbed into a moving one.
- **Sizing rationale.** The single observed jitter sample is
  ±1 on violations, 0 on unconnected. The tolerances (5 / 2)
  give that sample headroom while remaining far below any real
  routing regression: the v3→v4→v5 re-routes moved the
  violation count by 100+, and even one net's worth of new
  copper moves counts by more than the jitter band. A genuine
  regression cannot hide inside +5/+2; jitter cannot escape
  it either, on the evidence of the two runs.
- **scripts/drc_gate.py**: regression iff violations >
  baseline + tolerance_violations OR unconnected > baseline +
  tolerance_unconnected. Three healthy/unhealthy outcomes now
  have three distinct wordings everywhere the verdict appears
  (job-log banner, results/drc-status.json, $GITHUB_STEP_SUMMARY,
  site panel): at/below baseline → "no regression"; above
  baseline but within tolerance → verdict `WITHIN JITTER
  TOLERANCE`, board state "… — within checker jitter tolerance
  (+N over baseline, tolerance +T)", exit 0; above tolerance →
  REGRESSION, exit 1. The status JSON gains
  `tolerance_violations`, `tolerance_unconnected`,
  `over_violations`, `over_unconnected` and a `case` field
  (`no_regression` / `within_jitter_tolerance` / `regression` /
  `tool_failure`); `regression` keeps its CI meaning (the hard
  failure) and is true only in the regression case. Baseline
  files without tolerance keys default to 0 — pre-round-3
  strict semantics. The finished-board end state is guarded:
  when the baseline is 0/0 the gate forces both tolerances to
  0, so the hard zero-tolerance gate cannot be softened by
  tolerance keys left in the file (verified: 0/0 baseline with
  tolerances recorded, 3/0 report → REGRESSION, exit 1).
- **scripts/build_site.py** `drc_row()`: the CI-status path
  keys on the gate's verdict — `WITHIN JITTER TOLERANCE`
  renders BOARD STATE carrying the gate's jitter wording, and
  REGRESSION stays red with the tolerance in its line; the
  local fallback applies the same baseline + tolerance
  arithmetic. Verified for 726/190 (no regression), 727/190
  (jitter, both paths), 732/190 (REGRESSION) and the
  TOOL FAILURE row (unchanged).
- **ci/test_gates.py**: 21 → 27 checks, all passing. New
  round-3 cases run the REAL fixture doctored against the
  SHIPPED baseline: 727/190 → exit 0 with the jitter banner
  wording and the status-JSON case/tolerance fields asserted;
  731/192 (exactly at the tolerance edge on both counts) →
  exit 0; 732/190 → exit 1; 726/193 → exit 1. The round-2
  doctored-727 case is kept against a tolerance-less temporary
  baseline (exit 1), pinning the strict default. The ERC gate
  is untouched this round — its parsed verdict already passed
  on run 41751841325 — and all its cases stay green.

**Standing rule from this round:** the baseline is a fixed
reference point and the tolerance is the only jitter absorber.
Further upward drift beyond the tolerance is real signal —
investigate it and document it here; never silently re-baseline
to absorb it, and never widen the tolerance to fit a drift
without the same two-run, identical-blob evidence that
justified this one.

Remaining verification: the next CI run on main with round 3
merged should show the DRC step passing as board state — at
726/190 as "no regression", or at 727/190 (if the jitter lands
that way again) as "within checker jitter tolerance", with the
site panel showing the matching wording.

### Stage 7c in-flight report (2026-11-03 ~17:20 PST)

Two runs were in flight in /tmp scratch trees when the VM was
replaced again (~01:43 UTC; uptime 1 min on return, /tmp a fresh
tmpfs). Both scratch trees, their logs and checkpoints are LOST.
The repo and ~/workspace/tools survived intact. Numbers below are
from log tails read at 01:18 UTC, before the loss.

v6 full-board route (gen_pcb --router6, SAFE tolerance fixed):
main pass COMPLETED — all 112 nets attempted in 1,830 s (~2x the
v5 router's per-net pace, inside the expected band), checkpoint
saves verified on disk at net 110; retry pass 1 was running with
138 failed pins when the VM died. The final board was never saved
(gen_pcb saves after route + zone fill). RELAUNCHED from a durable
workspace scratch tree (see below); the 138-failed-pins figure is
the number the retries + repair6 must beat down.

Freerouting FR-1: DEAD-IN-PLACE, root cause identified before the
VM loss. The v2.5.0 native CLI's autorouter thread throws
UnsupportedFeatureError (GraalVM native-image: no serialization
constructor for board.model.items.ComponentOutline) seconds after
job start; the process then idles forever (46 min elapsed, 2 s
CPU). Reproduced identically with -mt 1. The native CLI build is
therefore unusable for this board. Plan B in progress: the same
release's AppImage (JVM build — no GraalVM serialization path),
extracted under ~/workspace/tools/freerouting/; its bundled JRE
can also run the plain jar. FR-1's own log noted, for the record:
140 pre-existing pin-to-pin clearance violations by Freerouting's
reading of the unrouted board, and J2 pins 5/6 lying outside the
board outline at x = 102.08 mm (a placement fact — J2 overhangs
the edge; to be accounted in the final write-up).

Recovery change: all scratch state now lives under ~/workspace
(pdlvds-v6run/, pdlvds-fr/) — /tmp does not survive this VM's
replacements, the workspace does.

### Stage 7c — v6 full-board attempt 1 (2026-11-03 eve)

Clean full-board route with router6 (exact model), from the
placed board: main pass 112 nets in 2,276 s, two retry passes
(2.5M cap) in 2,372 s more, then zone fill + save. The run that
produced it survived one VM replacement only because the scratch
tree had been moved into the workspace (pdlvds-v6run/).

Result (results/pcb_build_v6.log, results/audit-v6-attempt1.txt):
- router6: 30/112 nets fully routed, 144 pin connections failed,
  67 signal vias + 87 GND vias. Retry passes made ZERO progress
  (144 -> 144) — the failures are structural, not budget.
- Audit vs v5 board: copper items 1,588 (v5 1,651); unconnected
  nets 83 (v5 98); clearance violations 64 (v5 341); intrinsic 42.
- THE MODEL VERDICT: of the 64 violations, 46 are the known
  cross-footprint pad-pad placement pairs (identical to v5) and 18
  are zone-involved (10 via-zone, 4 pad-zone, 4 track-zone — the
  HV/buried-clearance residue). ZERO pairs involve router-emitted
  track/via geometry against other copper. The exact-clearance
  invariant held on every emitted item — the v6 model rewrite is
  proven; what remains is connectivity.
- Failed pins concentrate in power nets (+3V3D 13, +3V3A 12,
  APD_A 8, NEG_RAW 7, VBUS_RAW 4, +5V 3) and fine-pitch parts
  (U7 24, U6 17, U4 14, U12 11, J1 7).

Adopted as the main board (strictly better than v5 on both audit
axes; v5 remains in history at fb2acf7). Next: pocket diagnosis on
THIS board for the structural blocker, then repair6 passes.

## Token metrics (2026-11-04) — progress vs tokens used

New `metrics/` directory: the project's agent-token usage, exported from the
runtime's `agent.agent_message_token_usage` records (the per-request table
`agent.token_usage` is empty — see metrics/README.md for the full methodology,
scope rules, exact SQL, and caveats).

Headline at the 2026-11-04T08:04:23Z snapshot: **124,730,218 gross tokens
processed** (124,105,756 input + 624,462 output) across 63 in-scope agents and
143 usage records — chat tree 108,914,972 input (main agent + subagents),
checkpoint cron 15,190,784 input. "Gross" = full context re-sent per request,
summed; in-flight agents (coordinator #2) have no records until they complete,
so the true figure is higher. `metrics/token_series.csv` is the timestamped
cumulative series; `metrics/commit_alignment.csv` aligns every commit with
cumulative tokens and the board state from the audit committed at that
revision; `metrics/progress_vs_tokens.svg` plots board state against tokens
(v5 plateau 98 unconnected / 341 violations → repair-4 spike 445 → v6 drop to
83 / 64 → repair6 62 / 64). To be re-exported at project end for the final
"designed in X tokens" figure.

## Token graph (2026-11-04) — per-message chart on the site, data refreshed

- **Data refreshed**: the metrics export was re-run with the verbatim
  SQL in `metrics/README.md`, bound `created_at <= 1793780974`
  (2026-11-04T08:29:34Z), sums asserted equal to the database probe
  aggregates before anything was written. New snapshot:
  **151 usage rows, 133,920,588 gross tokens** (133,253,984 input +
  666,604 output) — chat tree 117 rows / 117,890,120 gross, checkpoint
  cron 34 rows / 16,030,468 gross; 66 agents in scope, 50 with rows.
  The refresh caught the first export's worker's own completion row
  (6,231,047 in / 31,461 out), which landed after its snapshot.
  `metrics/README.md`'s headline, scope table and caveats were updated
  to match (they still showed the 08:04:23Z first export).
- **Per-message chart** (`metrics/token_per_message.svg`, generated by
  the committed `metrics/make_token_chart.py`, matplotlib): top panel =
  gross tokens per usage record over time (log scale, vertical bars
  colour-coded main chat / subagent / checkpoint cron; subagent records
  are whole-run lumps timestamped at completion, main-chat records are
  true per-message), bottom panel = cumulative gross tokens. Thirteen
  epochs are annotated as dashed markers with staggered labels, each
  timestamped from its commit in `git log`: project start (073664b),
  schematic + netlist verified (0d6622d), router v1 (dc6a010), v3
  (3ac1a43), v4 (41d7196), v5 (fb2acf7), ERC 0 errors (6d66aaf),
  repair passes 1-4 (162cc87), router v6 (9fcb471), CI fully green
  (0e7e532, the merge run 41752825210 built), fanout macro (aa04b66),
  repair6 (67722e0), token metrics (7a55543). Spot-checked 3 epochs
  against `git log` — exact matches. The chart is white-background /
  dark-text by design.
- **Site**: new "Token usage" section between Board and Routing
  history (nav link included). Headline totals and the per-scope table
  are computed by `scripts/build_site.py` from the committed CSVs at
  build time — never hardcoded — with the method in brief and a link
  to `metrics/README.md` (copied to downloads as
  `token-metrics-README.md`); the chart sits on an explicit white
  `.tokenpanel` so it stays legible. Verified on a local build:
  section present, both metrics SVGs copied byte-identical (md5
  match), headline renders 133,920,588 at snapshot
  2026-11-04T08:29:34Z.
- **Bug found by this verification**: the first local build's chart
  asset silently vanished while its copy reported success.
  `schematic_svg()` in `scripts/build_site.py` renamed EVERY `.svg`
  in `site/assets/` onto `schematic.svg` — it now renames only files
  the kicad-cli export just produced. (The same rename would have
  eaten the board top/bottom SVGs on any build where they were
  copied before the schematic export ran.)
- Still excluded, as before: agents still running have no usage rows
  (build coordinator #2's v6 routing work, this section's own worker),
  so the snapshot understates the running total. Final re-export
  remains a project-end step, now including
  `python3 metrics/make_token_chart.py .`.

## Pass numbering (adopted 2026-11-04, user directive)

All layout work is numbered with ONE monotonic counter — pass 1,
2, 3, … — in commit subjects as `pass NNNN: <what changed>`.
Named families ("repair6 attempt N", "v6 + diagonals") are
retired as organizing labels; strategy changes are changelog
lines, not names. The structure worker's history/PASSES.md
backfill is authoritative for the early count; if its numbering
differs from the count below by an offset, the log wins and
later entries reconcile.

Counting basis used here (committed layout states in commit
order): passes 1-5 = v1..v5 routes; 6-9 = repair attempts 1-4;
10 = v6 full-board route 1 (b805fc3); 11 = repair6 attempt 1
(67722e0); 12 = diagonals run (f2b2fbe); 13 = placement revision
(e8a0954); **14 = repair6-on-placement-revised-board checkpoint
1 (d489c78)**. Pass 15 will be that run's next checkpoint/sweep
state, and so on.

## Pass system — structure (2026-11-04, branch pass-structure)

The pass counter now has its machinery, built by the structure
worker on the `pass-structure` branch:

- **The log**: `history/PASSES.md` (human) + `history/passes.json`
  (machine; the site reads it). Numbering rule: a pass is a commit
  that produced a new board state (a routing or placement change to
  a `hw/*.kicad_pcb`), numbered in commit order; pass 1 is the first
  committed board state. Strategy changes are changelog lines, never
  names.
- **Backfilled sequence: 10 passes.** 1 = placed board (d0c0bca);
  2 = first routed board, neck-down + power-first (3ac1a43);
  3 = goal-cell exemption fix (41d7196); 4 = stricter clearance
  model, first committed audit (fb2acf7); 5 = repair over pass 4,
  not adopted, model-gap verdict (162cc87); 6 = exact-model router,
  full-board route, adopted (b805fc3); 7 = repair + fanout escapes
  (67722e0); 8 = diagonals + repair re-run bundled, 0 groups
  (f2b2fbe); 9 = placement revision unboxing U7/U12/L2/X1
  (e8a0954); **10 = repair on the placement-revised board,
  checkpoint 1 (d489c78)**. The next pass is 11.
- **Reconciliation**: the "Pass numbering" section above counted
  d489c78 provisionally as 14, including five runs whose boards
  were never committed (router v1/v2, repair attempts 1–3) and not
  counting the placed board. That section defers to the pass log;
  under the log's rule the offset is −4, and any future "pass 15"
  subject written against the provisional count is pass 11 in the
  log. The uncommitted runs are accounted in PASSES.md's "Gaps"
  section — not numbered, not silently dropped.
- **One-command flow**: `python3 scripts/commit_pass.py "what
  changed"` audits the board (saved as `history/pass-NNNN/
  audit.txt`), renders the pass's image set into
  `history/pass-NNNN/`, appends the log entries, stages exactly the
  pass's files and commits `pass NNNN: <description>`, then a small
  bookkeeping commit records the pass commit's hash (a commit
  cannot contain its own hash). Push is the only step left. Tested
  end-to-end with a dummy pass (audit read the current main board
  at 83 unconnected / 64 violations; commit carried board + audit +
  6 renders + log entries; site built with the entry) and the dummy
  was then removed by resetting the branch — the delivered log
  contains only real passes.
- **Site**: the Routing history section reads `passes.json` and
  copies each pass's committed render files; it never re-renders
  old boards, so the site builds from any commit's tree alone (the
  build-matrix property). No CI workflow change was needed.
  Verified locally: all 10 entries render — 7 with their committed
  image sets, passes 5/8/9 with an explicit "no renders were
  committed" note. `history/index.json` and the two-step
  snapshot_route flow are retired (frozen legacy); commit_pass.py
  reuses snapshot_route's render machinery.
