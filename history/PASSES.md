# Pass log — the layout history

One monotonic counter for all layout work: **pass 1, pass 2,
pass 3, …** A pass is a commit that produced a new board state
(a routing or placement change to a `hw/*.kicad_pcb` file),
numbered in commit order; pass 1 is the first committed board
state. Strategy changes are described in each pass's changelog
line below — never encoded in names. Named families from before
the counter ("router v3", "repair6 attempt 1", "v6 + diagonals")
survive only inside the descriptions, as history.

Machine-readable twin: `history/passes.json` (the site reads it).
New passes are added by `scripts/commit_pass.py` — one command
that audits, renders, logs and commits. Numbers are never
reused or reordered; a number, once committed, is permanent.
Anything never measured is written as "not recorded" — numbers
are never invented.

## The passes

### Pass 1 — 2026-11-03T19:43:45Z · commit `d0c0bca`

Board: `hw/pdlvds_rx.kicad_pcb` · Commit: `d0c0bca09143177ae7a3f59f2cc6b8dc8500739a`

Placement only: 144 footprints placed, GND zones and the HV isolation slot drawn, saved unrouted — the routing run was interrupted by a VM replacement. First committed board state; 0 of 112 nets routed.

Nets fully routed: 0 of 112 · Pins failed: not recorded · Clearance violations: not recorded · Unconnected nets: not recorded · Audit verdict: not recorded

Snapshot renders were made later from the board as committed at d0c0bca.

### Pass 2 — 2026-11-03T20:52:25Z · commit `3ac1a43`

Board: `hw/pdlvds_rx.kicad_pcb` · Commit: `3ac1a430b6b34aad838f234624f8244d95d50e0e`

First committed routed board. Router gains neck-down where wide tracks meet fine-pitch pads and power-first net ordering (HV > power > LVDS > signals) — the fixes for the uncommitted v1/v2 failures (see gaps). 57 of 112 nets fully routed, 90 pins failed; no audit file was committed with this pass, so clearance violations and unconnected nets are not recorded.

Nets fully routed: 57 of 112 · Pins failed: 90 · Clearance violations: not recorded · Unconnected nets: not recorded · Audit verdict: not recorded

### Pass 3 — 2026-11-03T21:25:40Z · commit `41d7196`

Board: `hw/pdlvds_rx.kicad_pcb` · Commit: `41d7196ba016876cd4c570858b575174c105ceee`

Goal-cell exemption fix: a net's own target cells no longer count as blocked for it. 67 of 112 nets fully routed, 59 pins failed. The clearance figure (454) is the audit's violating-pair count as recorded in commit f8b9d1c — no audit file was committed with the pass itself — and the unconnected-net count was not recorded.

Nets fully routed: 67 of 112 · Pins failed: 59 · Clearance violations: 454 · Unconnected nets: not recorded · Audit verdict: FAIL

### Pass 4 — 2026-11-03T22:29:05Z · commit `fb2acf7`

Board: `hw/pdlvds_rx.kicad_pcb` · Commit: `fb2acf7b80f74860a8301a3cce6eaf4df1abbb6f`

Stricter clearance model in the router: vias never exempt, segment-midpoint tests, layer-aware HV clearance. Traded connections for correctness — 58 of 112 nets fully routed, 74 pins failed. First pass with a full audit committed: 98 unconnected nets, 341 clearance violations.

Nets fully routed: 58 of 112 · Pins failed: 74 · Clearance violations: 341 · Unconnected nets: 98 · Audit verdict: FAIL

### Pass 5 — 2026-11-04T00:18:21Z · commit `162cc87`

Board: `hw/pdlvds_rx.repaired.kicad_pcb` · Commit: `162cc8762f15b8b432861d5dcaf89ba4ce13a7c0`

Repair pass over the pass-4 board — the first repair run to survive to a commit (attempts 1–3 were lost; see gaps). 82 isolated groups connected across 2 sweeps, but clearance violations rose 341 → 445, so it was NOT adopted as the main board; the board is kept as the attempt artifact. Its verdict drove the next rewrite: the router's clearance model (grid-node + segment-midpoint tests) systematically under-protects against the audit's exact shape geometry.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 445 · Unconnected nets: 95 · Audit verdict: FAIL

Audit: results/audit-repair-attempt4.txt, committed with the pass (copper items 2,208). No renders were committed for this pass.

### Pass 6 — 2026-11-04T03:50:41Z · commit `b805fc3`

Board: `hw/pdlvds_rx.kicad_pcb` · Commit: `b805fc37860f13a3d83fb11efe47e1b1ce8da968`

Router rewritten with an exact clearance model — per-segment shape-distance tests in blocked(), zero slack, parity with the audit — and run full-board from the placed board: 30 of 112 nets fully routed, 144 pins failed, 83 unconnected nets, 64 clearance violations, none of them involving router-emitted geometry (46 known placement pad pairs + 18 zone-involved). Model proven; connectivity is what remains. Adopted as the main board.

Nets fully routed: 30 of 112 · Pins failed: 144 · Clearance violations: 64 · Unconnected nets: 83 · Audit verdict: FAIL

Audit: results/audit-v6-attempt1.txt (copper items 1,588).

### Pass 7 — 2026-11-04T06:10:45Z · commit `67722e0`

Board: `hw/pdlvds_rx.repaired6.kicad_pcb` · Commit: `67722e038347f08fb7ee20062df80662bb41896a`

Repair over the pass-6 board, with two-segment fanout escapes for pads sitting on grid boundaries: 45 groups connected, unconnected nets 83 → 62, clearance violations unchanged at 64. Board kept as hw/pdlvds_rx.repaired6.kicad_pcb.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 64 · Unconnected nets: 62 · Audit verdict: FAIL

Audit: results/audit-repair6-attempt1.txt, committed with the pass (copper items 2,115). Pins-failed is recorded as not recorded: no figure exists in this pass's own records (the old gallery index carried 74, parsed from a stale build log, not from this pass).

### Pass 8 — 2026-11-04T08:21:31Z · commit `f2b2fbe`

Board: `hw/pdlvds_rx.repaired6b.kicad_pcb` · Commit: `f2b2fbebc1693e7055479a407f3cbc098f60b14d`

Bundled change — two strategy changes in a single commit, the practice this counter replaces: diagonal moves added to the repair router AND the repair re-run over the pass-7 board. Result: 0 groups connected, no progress, not adopted. The commit's real payload is the per-pin diagnosis of the residue (results/diagnose-repaired6b.txt): of 99 isolated groups, 50 NO_EXIT, 16 POCKET, 20 WIDE_NO_GOAL, 13 REACHES — pads boxed in by placement, which is what pass 9 changes.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: not recorded · Unconnected nets: not recorded · Audit verdict: not recorded

Board saved as hw/pdlvds_rx.repaired6b.kicad_pcb (1,587 tracks per results/repair6-attempt2.log). No audit was committed for this pass, so unconnected nets and clearance violations are not recorded. No renders were committed.

### Pass 9 — 2026-11-04T08:30:34Z · commit `e8a0954`

Board: `hw/pdlvds_rx.moved.kicad_pcb` · Commit: `e8a09549b812b52075500880970cce009af8e59f`

Placement change, answering pass 8's diagnosis: the U7/U12/L2/X1 cluster is moved on the pass-7 board to unbox pads that had no exit — 24 pad pairs removed, 0 added. Board saved as hw/pdlvds_rx.moved.kicad_pcb.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 64 · Unconnected nets: 69 · Audit verdict: FAIL

Audit: results/audit-moved.txt, committed with the pass (copper items 1,392). No renders were committed for this pass.

### Pass 10 — 2026-11-04T10:08:43Z · commit `d489c78`

Board: `hw/pdlvds_rx.movedr.ckpt1.kicad_pcb` · Commit: `d489c787af9551c350cec5a0459c838ec1d9f41f`

Repair resumed over the placement-revised board (pass 9) and — the first pass committed under the sharpened rule — committed at checkpoint 1 of the run instead of at run end: 111 groups connected, unconnected nets 69 → 49. The audit committed with the checkpoint reads 1,435 clearance violations on 3,424 copper items; checkpoint saves did not refill zones at the time (fixed in cabbebc), and the figure is recorded exactly as the committed audit states it — a mid-run checkpoint state, not a finished-board audit. The run was still in progress when this was committed.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 1435 · Unconnected nets: 49 · Audit verdict: FAIL

Audit: results/audit-repair6-attempt3-ckpt1.txt, committed with the pass. Pins-failed not recorded (the old gallery index's 74 came from the same stale build-log parse as pass 7's).

### Pass 11 — 2026-11-04T12:30:46Z · commit `2d2114e`

Board: `hw/pdlvds_rx.relief.kicad_pcb` · Commit: `2d2114ea0d33c014b9531aee7766f1e9e97afa0a`

placement relief: J2 shifted -4 mm in x (pads 5/6 were 2.08 mm outside the outline); 40 audit-driven nudges (hw/relief_nudge.py) clear all 22 inter-part pad clearance violations, several at gap 0.000 (touching); only small passives moved, no ICs, APD/TIA cluster untouched; remaining audit items = 20 INTRINSIC same-footprint pairs + 56 stale zone-fill pairs (refilled at route import); unrouted, Freerouting next

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 56 · Unconnected nets: 113 · Audit verdict: FAIL

### Pass 12 — 2026-11-04T13:34:01Z · commit `2120e09`

Board: `hw/pdlvds_rx.fr1.kicad_pcb` · Commit: `2120e096b8b049c09fed553c4c691a2fbd6f996b`

Freerouting v2.5.0 routes the pass-11 relief placement (6 passes, score plateau ~221, best state kept: 148/402 connections unrouted by FR); SES imported via hw/import_ses.py after fixing its unit scaling (SES is in 0.1 um resolution units, importer assumed um and landed at 10x; fix parses (resolution um N)); importer also refills zones. Audit: 44 unconnected nets (power nets dominate: +3V3D 20 groups, +5V 15, +3V3A 13, GND 10), 13 clearance items all one family (APD_K pads/tracks vs F.Cu GND pour, 1.0 mm HV rule), 20 intrinsic; repair6 in checkpointed runs next

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 44 · Audit verdict: FAIL

### Pass 13 — 2026-11-04T13:37:41Z · commit `df01943`

Board: `hw/pdlvds_rx.fr1r.ckpt1.kicad_pcb` · Commit: `df019431c539205e1e46dedb8a9a976be2bd20c8`

repair6 checkpoint 1 on the Freerouting board (pass 12): 10 groups connected in the first ~90 s of sweep 1 (contrast: 0 in 90 min on the pre-relief placement); run continues checkpointing on hw/pdlvds_rx.fr1r.kicad_pcb

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 44 · Audit verdict: FAIL

### Pass 14 — 2026-11-04T13:39:12Z · commit `1ce3d91`

Board: `hw/pdlvds_rx.fr1r.ckpt2.kicad_pcb` · Commit: `1ce3d9158cb642b1f613e37e6d4289b0d35769eb`

repair6 checkpoint 2 on the Freerouting board: 20 groups connected, sweep 1 continuing

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 44 · Audit verdict: FAIL

### Pass 15 — 2026-11-04T13:43:07Z · commit `17d9b29`

Board: `hw/pdlvds_rx.fr1r.ckpt3.kicad_pcb` · Commit: `17d9b29beb16275d0103d5195da306f668e0b167`

repair6 checkpoint 3 on the Freerouting board: 30 groups connected, sweep 1 continuing

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 44 · Audit verdict: FAIL

### Pass 16 — 2026-11-04T13:44:21Z · commit `060416b`

Board: `hw/pdlvds_rx.fr1r.ckpt4.kicad_pcb` · Commit: `060416bc280766a98ea6518b3f67351ab07d1931`

repair6 checkpoint 4 on the Freerouting board: 40 groups connected; first still-isolated groups appear (U4.12/U4.18 +3V3D_CDR, J1.A4 VBUS_RAW) - later sweeps retry them

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 44 · Audit verdict: FAIL

### Pass 17 — 2026-11-04T13:45:26Z · commit `32fa1a8`

Board: `hw/pdlvds_rx.fr1r.ckpt5.kicad_pcb` · Commit: `32fa1a8c5c766c0a97e50b7976218902be22d237`

repair6 checkpoint 5 on the Freerouting board: 50 groups connected, sweep 1 continuing (53 connected vs 25 still-isolated attempts so far)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 43 · Audit verdict: FAIL

### Pass 18 — 2026-11-04T13:50:48Z · commit `bb962a3`

Board: `hw/pdlvds_rx.fr1r.ckpt6.kicad_pcb` · Commit: `bb962a37b36993b5bcd4563c4170016d4d5ea1ff`

repair6 checkpoint 6 on the Freerouting board: 60 groups connected, sweep 1 continuing

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 33 · Audit verdict: FAIL

### Pass 19 — 2026-11-04T14:06:35Z · commit `da3cc77`

Board: `hw/pdlvds_rx.fr1r.s2.kicad_pcb` · Commit: `da3cc774f61afa610f6e69f671032489068509bb`

repair6 final state on the Freerouting board: sweep 1 connected 64 groups, sweep 2 connected 0 (residue is copper-walled, per results/diagnose-fr1r.log census: NO_EXIT 23, POCKET 14, WIDE_NO_GOAL 2 of 39 classified); run stopped during the provably futile identical sweep 3; board state is the sweep-2-end save

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 30 · Audit verdict: FAIL

### Pass 20 — 2026-11-04T14:35:37Z · commit `c7ed6a2`

Board: `hw/pdlvds_rx.fr4.kicad_pcb` · Commit: `c7ed6a223224796ac7df97e12f157bdc9b700b89`

cluster clearing at the U7 south row: 66 foreign items (the XI/XO/RBIAS/+VA fanout thicket) ripped in three process batches of <=25 removes (KiCad 7 SWIG corrupts beyond a few dozen removes per process); +3V3A U7.25/30/31 then connected in seconds each through the cleared field — +3V3A is down to its main group plus U9.5. Victim nets fragmented by the clearing (unconnected-net count rises to 38; +VA/XI/XO/RBIAS/ULPI stubs to be healed by repair in the cleared field). PHY_1V8 U7.26 and PHY_1V8A U7.29 still sealed with empty fanout even in the cleared field — a pad-geometry seal, not copper. APD_A is down to D1.4 alone; clearance unchanged at the 13 APD_K-vs-pour items

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 38 · Audit verdict: FAIL

### Pass 21 — 2026-11-04T14:43:35Z · commit `11126fb`

Board: `hw/pdlvds_rx.fr5.ckpt1.kicad_pcb` · Commit: `11126fbac1f2d8f31bb33a469dacce0f246b4d0f`

repair6 healing checkpoint 1 on the cluster-cleared board (fr4): victims of the U7 clearing reconnecting in the cleared field; unconnected nets 38 -> 35, copper items 3210 -> 3392. Run continues; further checkpoints follow as passes

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 35 · Audit verdict: FAIL

### Pass 22 — 2026-11-04T14:49:45Z · commit `910b627`

Board: `hw/pdlvds_rx.fr5.kicad_pcb` · Commit: `910b627e8b2880ce53ad1c11d1dd4c890869d59b`

repair6 healing run on the cluster-cleared board, final state: unconnected nets 38 -> 35; -VA, SET_A and ULPI_D1 healed outright, the U7-clearing victims partially reconnected; a final sweep connected 0 and the run stopped. Residue is now almost entirely pad-ring clusters (U4, U13, U10, U9, U7 rows) plus D1.4/D1.5, J1.A9, U11.14 and GND islands — cluster clearing is the next tool for each

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 35 · Audit verdict: FAIL

### Pass 23 — 2026-11-04T15:04:44Z · commit `9fef1ac`

Board: `hw/pdlvds_rx.fr6.kicad_pcb` · Commit: `9fef1ac758984156b2113e7c8715c5163f79c92e`

U4 cluster clearing (disc 52,52 r4.2): +3V3D_CDR U4.12/18, CDR_CLKP U4.26, CDR_DATN U4.28, CDR_NIN U4.4, REFCLK U4.10 connected; CDR_LOS U4.22 and CDR_VREF U4.3 fanout-empty (sibling-pad seal, hand-stub next); victims fragmented, nets 35 -> 45 by count pending healing

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 45 · Audit verdict: FAIL

### Pass 24 — 2026-11-04T15:05:16Z · commit `7f565dc`

Board: `hw/pdlvds_rx.fr7.kicad_pcb` · Commit: `7f565dc84c90dbc717c7da1f55ea57bddab3ffbc`

U13 cluster clearing (disc 48,62 r3.6): all five targets connected — +5V U13.1/3, +VA U13.9/10, SET_P U13.7

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 46 · Audit verdict: FAIL

### Pass 25 — 2026-11-04T15:05:45Z · commit `aea23c7`

Board: `hw/pdlvds_rx.fr8.kicad_pcb` · Commit: `aea23c7a810b0961863253c140deada3b3f8e77c`

U7 full-chip cluster clearing (disc 30,61 r4.5, 101 items): 9/16 connected incl. PHY_1V8A U7.29, ULPI_D0/D2/DIR, XI, +3V3A U7.30/31; ULPI_D3/D4/D6 fanout-empty; USB_RST and RBIAS search-failed; clearing also cut U7.6/16/25's +3V3A stubs (healing owes them back)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 46 · Audit verdict: FAIL

### Pass 26 — 2026-11-04T15:06:18Z · commit `8b9cb9d`

Board: `hw/pdlvds_rx.fr9.kicad_pcb` · Commit: `8b9cb9d84ecd18163dc5f8d70eadc4cf7c995e4d`

U10 cluster clearing (disc 16,10 r3.6): HV_FBX U10.2 connected; HV_GATE U10.7 and HV_SHDN U10.9 fanout-empty (sibling-pad seal)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 50 · Audit verdict: FAIL

### Pass 27 — 2026-11-04T15:06:52Z · commit `8b6204d`

Board: `hw/pdlvds_rx.fr10.kicad_pcb` · Commit: `8b6204dfcbe60967165e9a2e6a93e0287ae7a9d1`

U9 cluster clearing (disc 8,48 r3.4): 0/4 — full clearing changed nothing; U9's pins are sealed by their own exposed pad (0.075 mm) inside the router's centre-anchored fanout model; hand-placed stubs are the route (the audit judges exact shapes, the model anchors at pad centres)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 50 · Audit verdict: FAIL

### Pass 28 — 2026-11-04T15:18:50Z · commit `d57c57a`

Board: `hw/pdlvds_rx.fr11.kicad_pcb` · Commit: `d57c57ae6ba190935b34e49d76ab12c5968eaeb0`

hand-placed escape stubs (new tool hw/hand_stub.py — audit-exact SHAPE.Collide search, edge-anchored, the fix for the router's centre-anchored fanout seal): I2C_SCL U9.1, I2C_SDA U9.6, TMP_ALERT U9.3, USB_RST U7.9, RBIAS U7.32 stubbed into open field; the router takes over from the stub ends

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 50 · Audit verdict: FAIL

### Pass 29 — 2026-11-04T15:19:22Z · commit `30aa43d`

Board: `hw/pdlvds_rx.fr12.kicad_pcb` · Commit: `30aa43d08fc16b172bc46439287e0cbe24c3f174`

hand stub: ULPI_D3 U7.21 east along the row (openness test fixed — neck-width step instead of a fat cross; shorter 0.5 mm stubs admitted). Remaining sealed pads classified by blocker: fence tracks (rip+stub), C40's pad (micro-move), D1 pair (custom via escapes)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 50 · Audit verdict: FAIL

### Pass 30 — 2026-11-04T15:32:13Z · commit `ac9435d`

Board: `hw/pdlvds_rx.fr13.kicad_pcb` · Commit: `ac9435d211807d5fa71e7f945fc377e01d41425f`

fence surgery + hand stubs: ripped CDR_NIN x9 / CDR_CLKP x2 / GND x6 / HV_INTVCC via / XI x5 (victims heal next round), then stubbed CDR_VREF U4.3 (W), CDR_LOS U4.22 (E), +3V3D U11.14 (N), HV_GATE U10.7 (E), VBUS_RAW J1.A9 (NE, full 0.6 width), XO U7.27 (N)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 53 · Audit verdict: FAIL

### Pass 31 — 2026-11-04T15:33:01Z · commit `f68880e`

Board: `hw/pdlvds_rx.fr14.kicad_pcb` · Commit: `f68880ec7c66799746562d1bb815c1d3a28598fd`

placement micro-ops: C40 flipped to the bottom side (frees U7's east-row exits; first bottom-side part on the board) and R27 moved north to (20.5,6.0) (frees U10.9's east exit); stubs placed: ULPI_D4 U7.20, ULPI_D6 U7.18, HV_SHDN U10.9

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 36 · Unconnected nets: 55 · Audit verdict: FAIL

### Pass 32 — 2026-11-04T15:33:34Z · commit `d3c2952`

Board: `hw/pdlvds_rx.fr15.kicad_pcb` · Commit: `d3c2952a8374d83f88feaebb256879385555402c`

via-first hand stubs (hw/hand_via.py; via disc tested as a zero-length segment after the plus-shape bug was found): +3V3A U9.5 via@(9.27,48) with In2 tail — the last U9 pin; CDR_LOS U4.22 second escape via@(55.29,51.25)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 36 · Unconnected nets: 55 · Audit verdict: FAIL

### Pass 33 — 2026-11-04T16:00:43Z · commit `128862d`

Board: `hw/pdlvds_rx.fr17.kicad_pcb` · Commit: `128862d766c8434e7b1abff75698481437a9e54b`

placement fixes found by exhaustive audit-exact search (hw/place_search.py): C40 to a clean home at (41.5,62) still flipped on the bottom side (its (35,62) B pads grazed PHY_1V8/ULPI_D2 B-tracks — 21 items), R27 west to (18.1,6.0) (its pad 2 grazed +5V tracks — 2 items); APD_A's D1.6 escape chain ripped (10 items) to open D1.5's exit

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 13 · Unconnected nets: 40 · Audit verdict: FAIL

### Pass 34 — 2026-11-04T16:01:28Z · commit `2a67851`

Board: `hw/pdlvds_rx.fr18.kicad_pcb` · Commit: `2a678510f3eb31cef82fac90596097f22f044c40`

D1 escapes placed (hw/d1_escape.py): APD_K D1.5 neck SE to via@(10.8,36.6) + In2 tail — its neck passes D1.4/D1.6 at 0.70 mm (justified: the APD's own terminals are 0.5 mm apart; the 1.0 mm board rule cannot be met inside the footprint); APD_A D1.4 neck NE to via@(9.9,41.9) + In2 tail, true gap to D1.5 0.975 mm (0.025 graze, same justification class). Both APD pads now have copper; healing bridges them

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 20 · Unconnected nets: 40 · Audit verdict: FAIL

### Pass 35 — 2026-11-04T16:46:56Z · commit `1bf1b3e`

Board: `hw/pdlvds_rx.fr19.kicad_pcb` · Commit: `1bf1b3ea602fed81b45ac122db85ae213a0f348a`

GND-inclusive healing (hw/repairg.py = repair6 without the GND exclusion): 65 groups connected before a VM replacement killed the run mid sweep-2; state recovered from the watcher checkpoint. GND 12 groups -> 2; clearance 36 -> 20 (C40/R27 families gone; rest = 16 APD_K-vs-pour + 3 D1 justified grazes + via antipad); APD_A fragmented to 7 groups in the detector corner by the D1.6-chain rip

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 20 · Unconnected nets: 40 · Audit verdict: FAIL

### Pass 36 — 2026-11-04T17:10:26Z · commit `6a3a728`

Board: `hw/pdlvds_rx.fr20.kicad_pcb` · Commit: `6a3a728d86c9c2372f6815518942f03e7c518ccb`

repairg round 2: 10 more groups in sweep 1 (APD_A corner re-bridged 7 -> 2 groups; HV_GATE, MOS_G, NEG_RAW, ULPI_D4 closed), sweep 2 connected 0 and the run stopped by its own rule; 36 unconnected nets remain, mostly lone-pad vs stub long hauls

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 20 · Unconnected nets: 36 · Audit verdict: FAIL

### Pass 37 — 2026-11-04T17:15:28Z · commit `pending`

Board: `hw/pdlvds_rx.fr21.kicad_pcb` · Commit: `pending`

APD_K pour clearance resolved geometrically (hw/notch.py): rule-area copper-pour keepouts expanded >1.0 mm around the APD_K copper (northern cluster incl. R30's large pad, D1.5's escape, RJ2.2) on F/B, plus the In1 plane clearance raised 0.25 -> 0.35 so its antipads meet the 0.3 buried-HV rule. Audit: clearance 20 -> 3, the remainder exactly the justified D1 package-geometry grazes; GND connectivity unchanged

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 36 · Audit verdict: FAIL

<!-- next-pass -->

## Gaps — runs that were never committed, and so have no number

The counter only counts committed board states. These runs
happened — the record of them is in the commits and files named
— but their boards were never committed, so they hold no pass
number. Listing them is the honest accounting of what the
sequence misses:

- **router v1 run (commit dc6a010, 2026-11-03T19:39:29Z)** — Board routed in memory only; the commit carries router code, no board. Its 125 failed pins are known only from later commit messages (passes 2–3). Not numbered.
- **router v2 run (commit c79defe, 2026-11-03T20:10:21Z)** — Wide-nets-first ordering; board never committed and no result tally recorded. Not numbered.
- **repair attempts 1–3 over the pass-4 board (commits 2add453, 0c20958, 04c90b4)** — Attempt 1's board was lost at save; attempt 2 connected 82 groups in memory, then crashed at the same save (variable `path` shadowing the board path — root cause proven in 0c20958, which also retro-explains attempt 1); attempt 3 was killed by a VM replacement mid-sweep (04c90b4). The commits carry code and logs but no board. Pass 5 is repair attempt 4, the first to be committed. Not numbered.
- **in-flight run state lost to a VM replacement (commit 8d39045)** — Both /tmp scratch trees (v6 routing and the Freerouting line), with their logs and checkpoints, were lost; any board states in them were never committed. Scratch state moved into the workspace afterwards. Not numbered.
- **Freerouting baseline line** — No board produced by Freerouting has ever been committed (the native CLI build is dead — 8d39045; the JVM/AppImage line produced no committed board either), so it holds no pass numbers. If it ever produces a committed board state, it takes the next number like everything else.

## Reconciliation with the provisional count in docs/00-status.md

Commit `81b2942` ("Pass numbering" section of docs/00-status.md)
recorded d489c78 provisionally as "pass 14", counting the five
uncommitted runs in the gaps above (router v1, router v2, repair
attempts 1–3) as passes and not counting the placed board.
That section states this log is authoritative and later entries
reconcile. Under the rule above, d489c78 is **pass 10** (an
offset of −4), and the next pass is **pass 11**. Any "pass 15"
subject written against the provisional count refers to what
is pass 11 here.
