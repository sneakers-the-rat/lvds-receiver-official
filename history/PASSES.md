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

Snapshot renders were made later from the board as committed at d0c0bca. Composite render backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass.

### Pass 2 — 2026-11-03T20:52:25Z · commit `3ac1a43`

Board: `hw/pdlvds_rx.kicad_pcb` · Commit: `3ac1a430b6b34aad838f234624f8244d95d50e0e`

First committed routed board. Router gains neck-down where wide tracks meet fine-pitch pads and power-first net ordering (HV > power > LVDS > signals) — the fixes for the uncommitted v1/v2 failures (see gaps). 57 of 112 nets fully routed, 90 pins failed; no audit file was committed with this pass, so clearance violations and unconnected nets are not recorded.

Nets fully routed: 57 of 112 · Pins failed: 90 · Clearance violations: not recorded · Unconnected nets: not recorded · Audit verdict: not recorded Composite render backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass.

### Pass 3 — 2026-11-03T21:25:40Z · commit `41d7196`

Board: `hw/pdlvds_rx.kicad_pcb` · Commit: `41d7196ba016876cd4c570858b575174c105ceee`

Goal-cell exemption fix: a net's own target cells no longer count as blocked for it. 67 of 112 nets fully routed, 59 pins failed. The clearance figure (454) is the audit's violating-pair count as recorded in commit f8b9d1c — no audit file was committed with the pass itself — and the unconnected-net count was not recorded.

Nets fully routed: 67 of 112 · Pins failed: 59 · Clearance violations: 454 · Unconnected nets: not recorded · Audit verdict: FAIL Composite render backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass.

### Pass 4 — 2026-11-03T22:29:05Z · commit `fb2acf7`

Board: `hw/pdlvds_rx.kicad_pcb` · Commit: `fb2acf7b80f74860a8301a3cce6eaf4df1abbb6f`

Stricter clearance model in the router: vias never exempt, segment-midpoint tests, layer-aware HV clearance. Traded connections for correctness — 58 of 112 nets fully routed, 74 pins failed. First pass with a full audit committed: 98 unconnected nets, 341 clearance violations.

Nets fully routed: 58 of 112 · Pins failed: 74 · Clearance violations: 341 · Unconnected nets: 98 · Audit verdict: FAIL Composite render backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass.

### Pass 5 — 2026-11-04T00:18:21Z · commit `162cc87`

Board: `hw/pdlvds_rx.repaired.kicad_pcb` · Commit: `162cc8762f15b8b432861d5dcaf89ba4ce13a7c0`

Repair pass over the pass-4 board — the first repair run to survive to a commit (attempts 1–3 were lost; see gaps). 82 isolated groups connected across 2 sweeps, but clearance violations rose 341 → 445, so it was NOT adopted as the main board; the board is kept as the attempt artifact. Its verdict drove the next rewrite: the router's clearance model (grid-node + segment-midpoint tests) systematically under-protects against the audit's exact shape geometry.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 445 · Unconnected nets: 95 · Audit verdict: FAIL

Audit: results/audit-repair-attempt4.txt, committed with the pass (copper items 2,208). No renders were committed for this pass. Renders backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass. Composite render backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass.

### Pass 6 — 2026-11-04T03:50:41Z · commit `b805fc3`

Board: `hw/pdlvds_rx.kicad_pcb` · Commit: `b805fc37860f13a3d83fb11efe47e1b1ce8da968`

Router rewritten with an exact clearance model — per-segment shape-distance tests in blocked(), zero slack, parity with the audit — and run full-board from the placed board: 30 of 112 nets fully routed, 144 pins failed, 83 unconnected nets, 64 clearance violations, none of them involving router-emitted geometry (46 known placement pad pairs + 18 zone-involved). Model proven; connectivity is what remains. Adopted as the main board.

Nets fully routed: 30 of 112 · Pins failed: 144 · Clearance violations: 64 · Unconnected nets: 83 · Audit verdict: FAIL

Audit: results/audit-v6-attempt1.txt (copper items 1,588). Composite render backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass.

### Pass 7 — 2026-11-04T06:10:45Z · commit `67722e0`

Board: `hw/pdlvds_rx.repaired6.kicad_pcb` · Commit: `67722e038347f08fb7ee20062df80662bb41896a`

Repair over the pass-6 board, with two-segment fanout escapes for pads sitting on grid boundaries: 45 groups connected, unconnected nets 83 → 62, clearance violations unchanged at 64. Board kept as hw/pdlvds_rx.repaired6.kicad_pcb.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 64 · Unconnected nets: 62 · Audit verdict: FAIL

Audit: results/audit-repair6-attempt1.txt, committed with the pass (copper items 2,115). Pins-failed is recorded as not recorded: no figure exists in this pass's own records (the old gallery index carried 74, parsed from a stale build log, not from this pass). Composite render backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass.

### Pass 8 — 2026-11-04T08:21:31Z · commit `f2b2fbe`

Board: `hw/pdlvds_rx.repaired6b.kicad_pcb` · Commit: `f2b2fbebc1693e7055479a407f3cbc098f60b14d`

Bundled change — two strategy changes in a single commit, the practice this counter replaces: diagonal moves added to the repair router AND the repair re-run over the pass-7 board. Result: 0 groups connected, no progress, not adopted. The commit's real payload is the per-pin diagnosis of the residue (results/diagnose-repaired6b.txt): of 99 isolated groups, 50 NO_EXIT, 16 POCKET, 20 WIDE_NO_GOAL, 13 REACHES — pads boxed in by placement, which is what pass 9 changes.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: not recorded · Unconnected nets: not recorded · Audit verdict: not recorded

Board saved as hw/pdlvds_rx.repaired6b.kicad_pcb (1,587 tracks per results/repair6-attempt2.log). No audit was committed for this pass, so unconnected nets and clearance violations are not recorded. No renders were committed. Renders backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass. Composite render backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass.

### Pass 9 — 2026-11-04T08:30:34Z · commit `e8a0954`

Board: `hw/pdlvds_rx.moved.kicad_pcb` · Commit: `e8a09549b812b52075500880970cce009af8e59f`

Placement change, answering pass 8's diagnosis: the U7/U12/L2/X1 cluster is moved on the pass-7 board to unbox pads that had no exit — 24 pad pairs removed, 0 added. Board saved as hw/pdlvds_rx.moved.kicad_pcb.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 64 · Unconnected nets: 69 · Audit verdict: FAIL

Audit: results/audit-moved.txt, committed with the pass (copper items 1,392). No renders were committed for this pass. Renders backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass. Composite render backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass.

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

### Pass 37 — 2026-11-04T17:15:28Z · commit `38e1fc1`

Board: `hw/pdlvds_rx.fr21.kicad_pcb` · Commit: `38e1fc137559a8a329f9dd99d352e68834cb2624`

APD_K pour clearance resolved geometrically (hw/notch.py): rule-area copper-pour keepouts expanded >1.0 mm around the APD_K copper (northern cluster incl. R30's large pad, D1.5's escape, RJ2.2) on F/B, plus the In1 plane clearance raised 0.25 -> 0.35 so its antipads meet the 0.3 buried-HV rule. Audit: clearance 20 -> 3, the remainder exactly the justified D1 package-geometry grazes; GND connectivity unchanged

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 36 · Audit verdict: FAIL

### Pass 38 — 2026-11-04T19:53:30Z · commit `cadd345`

Board: `hw/pdlvds_rx.fr22.kicad_pcb` · Commit: `cadd345d5cb1f37e4b2cb3d0579ea08c10f2058e`

stub campaign 1 (hw/hand_stub.py): 13 of 31 singleton pads given audit-exact edge-anchored escape stubs, incl. D1.6 west, RJ2.2, CDR_DATP U4.29, CDR_NIN U4.4, CF1/CF2, GND R28.2, PHY_1V8A C23.1

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 36 · Audit verdict: FAIL

### Pass 39 — 2026-11-04T19:54:32Z · commit `23547a3`

Board: `hw/pdlvds_rx.fr24.kicad_pcb` · Commit: `23547a35b594c2be591ea5f5950ab99bca586472`

cluster clearing U4 disc (52,52) r4.2 on the stubbed board: 7/9 targets connected through the cleared field (CDR ring pads, +3V3D_CDR U4.24 among them)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 35 · Audit verdict: FAIL

### Pass 40 — 2026-11-04T19:55:21Z · commit `3b07804`

Board: `hw/pdlvds_rx.fr25.kicad_pcb` · Commit: `3b078040b0d3843f83165e865a336e261ce9f171`

cluster clearing U7 disc (30,61) r4.5: 5/7 targets connected incl. +3V3A U7.16/U7.25; ULPI_NXT U7.11 and ULPI_STP U7.13 remain sealed by their own row geometry

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 39 · Audit verdict: FAIL

### Pass 41 — 2026-11-04T19:56:08Z · commit `b8feded`

Board: `hw/pdlvds_rx.fr26.kicad_pcb` · Commit: `b8feded3391365c287c593c33d3281a6a429e622`

cluster clearing U10 disc (16,10) r3.6: 1/2 HV targets connected

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 44 · Audit verdict: FAIL

### Pass 42 — 2026-11-04T19:57:05Z · commit `d247c5c`

Board: `hw/pdlvds_rx.fr27.kicad_pcb` · Commit: `d247c5c9e3ed4b0c305fdae9788a7a96988387ad`

cluster clearing U6 west disc (83,44) r3.5: USB_RST U6.40 not connected by astar even in the cleared field (fanout-model seal)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 49 · Audit verdict: FAIL

### Pass 43 — 2026-11-04T19:57:49Z · commit `043b44e`

Board: `hw/pdlvds_rx.fr28.kicad_pcb` · Commit: `043b44e7ce6564089c7c0fb0d3a7396060a27e64`

cluster clearing U13 disc (48,62) r3.6: ILIM_P U13.5 connected

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 50 · Audit verdict: FAIL

### Pass 44 — 2026-11-04T19:58:31Z · commit `2b9154b`

Board: `hw/pdlvds_rx.fr29.kicad_pcb` · Commit: `2b9154b2c6237443ec035b56dc71ff3192ee4461`

repairg healing after cluster chain 2: 68 groups connected (victims repaid in the cleared fields), sweep 2 connected 0; 37 unconnected nets, 85 groups, clearance 3

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 37 · Audit verdict: FAIL

### Pass 45 — 2026-11-04T19:59:31Z · commit `769f95e`

Board: `hw/pdlvds_rx.fr30.kicad_pcb` · Commit: `769f95e946b0175012572087c588e2cce2cad7bf`

stub campaign 2 on the healed field: +3V3A U7.30/U7.31 stubbed; CF1/CF2 re-stubbed (their campaign-1 stubs were ripped as cluster victims)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 37 · Audit verdict: FAIL

### Pass 46 — 2026-11-04T20:00:27Z · commit `a71a04e`

Board: `hw/pdlvds_rx.fr31.kicad_pcb` · Commit: `a71a04e62d3713b2d10007b737ea3c2d3eb81fbd`

small-disc clear (31.5,63.4) r2.4 with immediate audit-exact stubs: ULPI_STP, ULPI_DIR, ULPI_CK stubbed; ULPI_NXT U7.11 still sealed

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 42 · Audit verdict: FAIL

### Pass 47 — 2026-11-04T20:01:49Z · commit `cffc8be`

Board: `hw/pdlvds_rx.fr32.kicad_pcb` · Commit: `cffc8beca43c63fc97fff95a76a3d87ee96a0169`

small-disc clear (30,58.5) r2.6 with immediate stubs: PHY_1V8A U7.29 stubbed; +3V3A U7.6 still sealed

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 44 · Audit verdict: FAIL

### Pass 48 — 2026-11-04T20:03:22Z · commit `69c7cca`

Board: `hw/pdlvds_rx.fr33.kicad_pcb` · Commit: `69c7cca6cef35050814e4518b80d0b5760ffb59a`

small-disc clear (84.5,43.5) r2.5 with immediate stubs: ULPI_D6 U6.74 stubbed; USB_RST U6.40 still sealed

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 49 · Audit verdict: FAIL

### Pass 49 — 2026-11-04T20:04:18Z · commit `32030c5`

Board: `hw/pdlvds_rx.fr34.kicad_pcb` · Commit: `32030c524ea1de6609ad615cc56d04a69530fff1`

small-disc clear (16,10) r3.0: HV_INTVCC U10.8 / HV_SS U10.3 stubs still refused by the stub search's openness test

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 53 · Audit verdict: FAIL

### Pass 50 — 2026-11-04T20:05:10Z · commit `6a5a9b9`

Board: `hw/pdlvds_rx.fr35.kicad_pcb` · Commit: `6a5a9b9335eff9a1b22634f82fb12439571ebfbd`

small-disc clear (52.5,54) r2.6 with immediate stub: REFCLKN U4.11 stubbed; THRADJ U4.9 still sealed

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 54 · Audit verdict: FAIL

### Pass 51 — 2026-11-04T20:06:04Z · commit `dab3529`

Board: `hw/pdlvds_rx.fr37.kicad_pcb` · Commit: `dab352998dba6271cce5cdc932dde399481b061f`

surgery2 (hw/surgery2.py — probe 16 directions, rip the cheapest rippable blockers, place a 0.2 mm neck): +3V3A U7.6 stubbed (1 DP_PHY via ripped), USB_RST U6.40, HV_INTVCC U10.8, HV_SS U10.3 stubbed (their necks were clean all along; the stub search's endpoint-openness test had been the blocker)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 54 · Audit verdict: FAIL

### Pass 52 — 2026-11-04T20:07:19Z · commit `6bd1ae4`

Board: `hw/pdlvds_rx.fr38.kicad_pcb` · Commit: `6bd1ae40bb898fb8feefd20c5cfd4b013bfc4079`

surgery2 with pad-aware blocker pricing (pads cost 10, tracks/vias 1): ULPI_NXT U7.11 stubbed south (3 ULPI_STP items ripped), THRADJ U4.9 stubbed (2 GND tracks ripped) — every formerly singleton pad on the board now has copper

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 54 · Audit verdict: FAIL

### Pass 53 — 2026-11-04T20:08:16Z · commit `6755cd8`

Board: `hw/pdlvds_rx.fr39.kicad_pcb` · Commit: `6755cd89d0eeb28d390b90530444e603c602b2ab`

repairg healing on the surgery board: 40 groups connected, sweep 2 connected 0; 39 unconnected nets, 87 groups, clearance 3

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 39 · Audit verdict: FAIL

### Pass 54 — 2026-11-04T20:09:18Z · commit `a36d5f2`

Board: `hw/pdlvds_rx.fr40.kicad_pcb` · Commit: `a36d5f28a59059bd69a58e4cf2dbd32fa88b5991`

ripup 'all' batch 1 on the healed board: 3 groups connected through ripped fences (victims queued for the next heal)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 47 · Audit verdict: FAIL

### Pass 55 — 2026-11-04T20:10:22Z · commit `a153b60`

Board: `hw/pdlvds_rx.fr41.kicad_pcb` · Commit: `a153b60cd4537d26a354aac30e9609d7dbc6ce97`

ripup 'all' batch 2: 1 group connected

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 49 · Audit verdict: FAIL

### Pass 56 — 2026-11-04T20:12:12Z · commit `a7dc784`

Board: `hw/pdlvds_rx.fr42.kicad_pcb` · Commit: `a7dc78456f13552b7c67fa2347c7a81033b7354d`

repairg healing: 17 groups connected (ripup victims repaid; APD_K's three groups merged); 39 unconnected nets, 83 groups, clearance 3

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 39 · Audit verdict: FAIL

### Pass 57 — 2026-11-04T20:14:26Z · commit `9f1ce83`

Board: `hw/pdlvds_rx.fr43.kicad_pcb` · Commit: `9f1ce83f645b53e190761b2166aeecbd036c0de1`

hand bridges (hw/bridge.py): VBUS_RAW, ULPI_D0 and +5V group pairs bridged across 1.0-1.45 mm gaps, one fence item ripped each

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 37 · Audit verdict: FAIL

### Pass 58 — 2026-11-04T20:15:33Z · commit `577a6b0`

Board: `hw/pdlvds_rx.fr44.kicad_pcb` · Commit: `577a6b066fa0a8730c71f46a66443d8f517eda4f`

hand segment joins the floating fanout chain west of D1 to APD_A's main group (the chain proved to be main-group copper; D1.6's pad itself still lone)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 3 · Unconnected nets: 37 · Audit verdict: FAIL

### Pass 59 — 2026-11-04T20:16:51Z · commit `7ea91c7`

Board: `hw/pdlvds_rx.fr45.kicad_pcb` · Commit: `7ea91c721a3bdc0afca185513cd7c7b167e6ae3c`

D1.6 link segment from the pad's NW corner to its fanout chain: APD_A fully connected (36 unconnected nets). The segment passes D1.5 at ~0.96 mm — the 4th item of the justified D1 package-geometry graze family (the APD's own terminals are 0.5 mm apart; the 1.0 mm board rule cannot be met inside the footprint)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 4 · Unconnected nets: 36 · Audit verdict: FAIL

### Pass 60 — 2026-11-04T20:52:01Z · commit `6fb8574`

Board: `hw/pdlvds_rx.fr46.kicad_pcb` · Commit: `6fb85749164a6f34f186626686a84028d959c777`

ripup 'all' batch 3: 1 group connected (victims GND, I2C_SDA)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 4 · Unconnected nets: 35 · Audit verdict: FAIL

### Pass 61 — 2026-11-04T20:53:35Z · commit `49900f6`

Board: `hw/pdlvds_rx.fr47.kicad_pcb` · Commit: `49900f6fc319ab7889a644b521397f7d5c3957fb`

ripup 'all' batch 4: 2 groups connected (victims in the CDR differential family)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 4 · Unconnected nets: 38 · Audit verdict: FAIL

### Pass 62 — 2026-11-04T20:55:09Z · commit `a1e4d9d`

Board: `hw/pdlvds_rx.fr48.kicad_pcb` · Commit: `a1e4d9d5d99a188c5853896a8c9524d7185ecfae`

repairg healing: 12 groups connected, victims repaid; 34 unconnected nets, 74 groups, clearance 4 (all D1 family)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 4 · Unconnected nets: 34 · Audit verdict: FAIL

### Pass 63 — 2026-11-04T20:57:44Z · commit `d8ff341`

Board: `hw/pdlvds_rx.fr49.kicad_pcb` · Commit: `d8ff3415f801efd2c03d952a3fc2ee14908f7a1b`

ULPI_NXT escape hand-placed: from U7.11's surgery stub, SW 2.2 mm to open field at (27.69,65.85), 4 ULPI_STP/DIR fence items ripped (heal owes them back); the router's grid could not start from the lone stub cell at any expansion cap

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 4 · Unconnected nets: 35 · Audit verdict: FAIL

### Pass 64 — 2026-11-04T21:24:00Z · commit `28f0b1f`

Board: `hw/pdlvds_rx.fr50.kicad_pcb` · Commit: `28f0b1f67920694147922fec8b7e514a7a908bd6`

repairg healing on the NXT-escape board: 1 group connected — the heal curve is exhausted on this residue (68, 40, 17, 12, 1 across the last five heals); the remaining bridges are astar-proof in the current field and need forced geometry (ripup/hand bridges). A clean re-run (fr51) reproduced this state exactly: 35 unconnected nets

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 4 · Unconnected nets: 35 · Audit verdict: FAIL

### Pass 65 — 2026-11-04T22:10:13Z · commit `2e43811`

Board: `hw/pdlvds_rx.expanded.kicad_pcb` · Commit: `2e43811ed61a07825dc858263b14d76a2769db1f`

EXPANSION: outline 100x80 -> 100x110 mm (+30 mm north — the only side moving neither connector edge (J1 south, J2 east) nor the APD/TIA cluster (D1/U1/R1 west)). 44 footprints moved as 4 rigid groups into the new strip (hw/expand_board.py; membership from signal-net BFS + decoupling radius, hw/groups_expand.py): U7 USB cluster 8 parts, U4 CDR cluster 14 (incl. U5 capture chain), U9 alone, U10 HV cluster 21 (incl. hand-verified secondary chain D5/C32/R29/R34). Copper of the 63 nets touching moved pads ripped (3215 tracks, 195 vias, 181 GND stubs at moved pads); every other net's copper verified untouched (6110 -> 2519 items, exact difference). Courtyard overlap pairs 34 -> 18, pairs involving a moved part 16 -> 0 (6 intra-group grazes cleared by measured nudges); the 18 remaining pairs are all between unmoved parts (2 inside the frozen analog cluster, U6 field, MH5, J3) and cannot be zeroed without breaking the freeze. Cluster moats (min pad-centre distance to nearest foreign part): U7 1.54 -> 4.46 mm, U4 1.13 -> 3.99, U9 3.46 -> 5.09, U10 3.54 -> 3.99. U9's four sealed pins: escape fans 12-13/16 -> 16/16. Unrouted placement state by design — the strip gets routed next.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 2 · Unconnected nets: 69 · Audit verdict: FAIL

### Pass 66 — 2026-11-04T22:56:57Z · commit `fbc5369`

Board: `hw/pdlvds_rx.expanded.kicad_pcb` · Commit: `fbc53693ff48117f66c84ca17d2c28a755caa1b8`

expansion routing 1: GND pours extended into the strip (zone outlines y 0.3 -> -29.7 on F/In1/B, hw/refill_strip.py) + HV keepout notches carved from the moved U10 cluster's HV copper extents (hw/notch_strip.py, rule areas as in notch.py). GND 51 -> 9 groups; clearance 2 (justified D1 pair) after an intermediate refill-only state read 10 (8 HV-vs-pour in the strip, results/audit-refill-candidate.txt) — the notch removed all 8. Rails untouched yet: +3V3D 40, +5V 27, +3V3A 13, +3V3D_CDR 10 groups.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 2 · Unconnected nets: 69 · Audit verdict: FAIL

Intermediate audits: results/audit-refill-candidate.txt (pour extension only: GND 51->7, violations 2->10) and results/audit-notch-candidate.txt (after notch: violations back to 2, GND 7->9 — two GND pads inside the notch rects lost pour contact, left for stitch/repair).

### Pass 67 — 2026-11-04T23:56:47Z · commit `bf7487d`

Board: `hw/pdlvds_rx.exp2.kicad_pcb` · Commit: `bf7487d18ea474483a8c126247bf264d02f05171`

expansion routing 2: bridge campaign (4 rounds, hw/bridge.py batched) on the repairg exp1 checkpoint board. Total groups 253 -> 226, unconnected nets 69 -> 65, violations 2 (justified D1 pair). Round yields -16/-6/-3/-2: nearest-pair bridges consumed; rails merged one pair per round (+3V3D/+5V/+3V3A/+3V3D_CDR all connected once per round), HV cluster nets bridged in the strip (HV_FBX, HV_SHDN, HV_RAW, HV_SENSE, FLY_PRI, HV_SEC, HV_VC2), +/-VA joined. ULPI bus (U7<->U6) untouched: nearest fragments >3 mm apart (bridge gap sentinel 9.9) — A* territory. Decay curve says change shape: next = rails bridge-chain, thread.py on geometry-stuck pairs, repairg2 sweep for long hauls.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 2 · Unconnected nets: 65 · Audit verdict: FAIL

bridge rounds in results/bridge-r1..r4.log; audits in results/audit-bridge-r1..r4.txt

### Pass 68 — 2026-11-05T00:16:50Z · commit `c6f4a3c`

Board: `hw/pdlvds_rx.exp3.kicad_pcb` · Commit: `c6f4a3c13bb4719a2720751200109a38fe14d766`

repairg2 GND phase STOPPED: 22 merges + 18 failed searches in ~16 min bought 1 audit group (226 -> 225, GND 5 -> 4) — its pour-blind grouping spends the sweep stitching clusters the GND pour already joins. Checkpoint board kept as the working base (copper is real). Main line changes shape per the stall rule: thread.py chains under my net order (rails first, GND excluded — its grouping is pour-blind too), one save+refill per invocation = checkpoint by construction; GND's 4 audit groups get targeted stitches from the audit's own group membership at the end.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 2 · Unconnected nets: 65 · Audit verdict: FAIL

repairg2 log: results/repairg2-exp3.log; checkpoint audit: results/audit-exp3-ckpt.txt

### Pass 69 — 2026-11-05T00:29:35Z · commit `810cb02`

Board: `hw/pdlvds_rx.exp4.kicad_pcb` · Commit: `810cb02d823fc1c4b4da12994056a97a1967105c`

heal_nets rails phase (hw/heal_nets.py, repairg engine under a named net list): +3V3D/+5V/+3V3A/+3V3D_CDR. 48 groups connected in 536 s, EVERY merge audit-real: total groups 225 -> 177, nets 65, violations 2. +3V3D 38 -> 7, +5V 23 -> 10, +3V3A 9 -> 5, +3V3D_CDR 7 -> 7 (zero merges — U4's rail pins are walled; rip-priced threading next). 25 groups STILL isolated, failing fast (1-12 s): U5 power pins x4, X2.1/X2.4 group, FB1.1, R25.1, U7.4 et al. — named residue for thread.py (rip pricing) after the signal phase.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 2 · Unconnected nets: 65 · Audit verdict: FAIL

heal log: results/heal-rails.log; audit: results/audit-exp4.txt

### Pass 70 — 2026-11-05T01:09:41Z · commit `5028477`

Board: `hw/pdlvds_rx.exp6n.kicad_pcb` · Commit: `502847785a9ca9e1cfe80070c7fb0f534ffccd8a`

fanout campaign + tool fix: hand_stub batch on 165 sealed pads (targets from the audit's non-main groups) placed 150 stubs after fixing a real bug in hw/hand_stub.py/hw/hand_via.py (bbox support function used as pad-edge distance -> diagonal stubs floated off their pads; first run's audit signature: 8 nets +1 group each as lone track groups; fix = ray-exit distance minus inset, tools commit fece b01). Zero floating stubs after the fix (only lone track group is GND's pre-existing one). Groups 171 -> 163, nets 59. HV keepout notches re-cut on current copper (hw/notch_strip.py): the pass-67 bridge APD_K tracks in the strip sat outside the pass-66 rects (violations had risen to 5); re-notch restored violations to 2 (justified D1 pair). 15 pads still have no stub (U9.5, U7.4/6, D1.5, J1.B5, U10.7/8/9, U13.7, U6.26/29/40/70/74, U14.6) — via-first escapes next.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 2 · Unconnected nets: 59 · Audit verdict: FAIL

stub logs: results/hand-stub-1.log (buggy run, discarded board) + hand-stub-2.log (fixed); notch: results/notch2.log; audit: results/audit-exp6n.txt

### Pass 71 — 2026-11-05T01:35:35Z · commit `8d17402`

Board: `hw/pdlvds_rx.exp7.kicad_pcb` · Commit: `8d17402bba0d6178daa567436f191a0f6f911b15`

heal-all on the stubbed board (58 nets): only 8 groups connected in 1101 s (APD_K x3, HV_FBX, I2C_SCL/SDA, HV_SHDN, TMP_ALERT) vs 93 STILL isolated — and violations REGRESSED 2 -> 32 (30x APD_K copper vs GND pour; groups 163 -> 156, nets 59). Root cause found in hw/router.py: the A* grid is still sized for the pre-expansion board (W,H = 400,320 = 100x80 mm, cell_of clamps y to [0,80]) — every strip pad/track (y<0) crushes onto grid row 0, so strip searches tested phantom geometry along the old field's congested north edge and emitted vias at y 0.6-2.1 where no HV keepout exists. The expansion's open space was invisible to the router for passes 65-71. Fix next: grid 400x440 with OY=-30 in router.py/router6.py.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 32 · Unconnected nets: 59 · Audit verdict: FAIL

heal log: results/heal-all.log; audit: results/audit-exp7.txt (violations itemized: 30 APD_K-vs-zone + 2 justified D1)

### Pass 72 — 2026-11-05T02:27:07Z · commit `c98592c`

Board: `hw/pdlvds_rx.exp8.kicad_pcb` · Commit: `c98592c67e1bab9f98d0a9d1d3f898afdc86ede6`

heal-all2 with the FIXED router grid (d4a9e0d) on the pass-71 board (exp7 -> exp8): 56 groups connected in 2383 s — the strip nets that were 0-second phantom failures under the clamped grid now route in real geometry. Pass 71's phantom-geometry damage state superseded.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 40 · Unconnected nets: 33 · Audit verdict: FAIL

### Pass 73 — 2026-11-05T02:32:56Z · commit `d8347be`

Board: `hw/pdlvds_rx.exp9.kicad_pcb` · Commit: `d8347becf263210813b188cbc5920c353301fa50`

hand_via campaign on the 16 no-stub pads from the pass-70 record (exp8 -> exp9): only 1/16 placed (ULPI_STP U6.26, via@(64.83,36.96) + In2 tail). The other 15 are proven outside hand_via's straight-neck/single-via shape space on exp8 geometry, each by 1-3 blockers (probe: results/probe-via.txt): U9.5 neck blocked solely by GND pad U9.7; U10.7 via disc solely by one +5V track; D1.5 by APD_A pads D1.4/D1.6 at the 1.0 mm HV class (intrinsic package geometry); J1.B5 by VBUS_RAW in the connector field; U6.74 by the NRST track bundle across the pin tips. These pads go to the residue loop's rip-up healing, which can move the blockers.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 40 · Unconnected nets: 33 · Audit verdict: FAIL

### Pass 74 — 2026-11-05T02:36:09Z · commit `ea80d52`

Board: `hw/pdlvds_rx.exp10.kicad_pcb` · Commit: `ea80d5209f14e852b2787b7d5ccb169ddcd2662e`

re-notch board-wide (exp9 -> exp10): notch_strip's strip filter (centre y < 5) removed — pass 72's audit charged 6 of its 38 APD_K-vs-pour violations to old-field APD_K copper outside the filter (via (13.625,30.625) and its run south to y 19.1). Rects now computed from ALL HV copper: 3 merged rects (the strip cluster and the west-side APD_K run merge into one (7.93,-19.25)-(44.58,33.23); D1.5 and RJ2.2 separate). Rule areas block pour only; GND fallout is measured by this audit and repaired by the stitch step next.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 2 · Unconnected nets: 33 · Audit verdict: FAIL

### Pass 75 — 2026-11-05T02:40:54Z · commit `404dc5c`

Board: `hw/pdlvds_rx.exp12.kicad_pcb` · Commit: `404dc5cfab4a29c61fc507f50959495d38d06333`

GND stitches (exp10 -> exp12): the 8 non-main audit groups were all single F.Cu items inside the board-wide notch rect, cut off from the F/B pours — but the notch rule areas carve F/B only, so each was stitched by a via down to the continuous In1 GND plane. 7 pad stitches via hand_via (C32.2, C29.2, C30.2, U10.5, U10.11, T1.4, R28.2 — 7/7 placed) + 1 via on the lone GND track segment at (27.296,12.092) (hw/stitch_track.py, sampled along the segment under hand_via's all-layer disc test). Group membership from hw/dump_groups.py (audit-exact union-find, full lists).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 2 · Unconnected nets: 32 · Audit verdict: FAIL

### Pass 76 — 2026-11-05T04:43:58Z · commit `2462a08`

Board: `hw/pdlvds_rx.exp13.kicad_pcb` · Commit: `2462a08a722e35cf02148bf6dc16423677aff155`

thread_far round 1 (exp12 -> exp13): the exact lattice threader with its pair gate raised 3 -> 15 mm (hw/thread_far.py) — 7 pairs threaded: CDR_VREF (gap 3.81, rips 2), REFCLKN (6.04, rips 2), SLICEP (4.46, rips 0), HV_SS (4.08, rips 3), HV_GATE (3.87, rips 1 — a diagnose-NO_EXIT group), HV_INTVCC (5.27, rips 3), +5V (0.19, rips 0). Proven en route: heal's astar6 fails this residue at cap 1.5M AND at 15M (heal_big probe on CDR_VREF, 162 s, 0 connected) while the diagnostic BFS reaches the goal halo — the grid A* model, not the geometry, refuses these hops. Failure classes pinned by the parent: CLASS A = NO_EXIT pads (local surgery per pad, blocker named — queue in WORKING_NOTES), CLASS B = two-island long hauls (ULPI x8, CDR chain, CAP, APD_K — the parallel Freerouting lane's territory; U6-side respread authorized if FR loses and diagnosis indicts U6 exits). 11 ripped victim items are repaid inside the class fixes, not by undirected heal sweeps. D1 exemption: STOPPED at the evidence gate (docs/07) — the 2 D1 lines remain violations as written.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 17 · Unconnected nets: 28 · Audit verdict: FAIL

### Pass 77 — 2026-11-05T05:38:21Z · commit `3f2e2cd`

Board: `hw/pdlvds_rx.exp14.kicad_pcb` · Commit: `3f2e2cd86798f77b0f3c2045cbd0c6d1d3f6428f`

Class T board repair: fixed thread_far redo on exp12 — CDR_VREF (rips 2), REFCLKN (rips 2), SLICEP (rips 6) threaded with exactly-executed priced rips; violations 17 -> 2 (only the standing D1 APD lines remain; all 15 Class T lines gone). Nets 28 -> 31 honestly: SLICEP's real rips split SLICEN and CDR_NIN (Class B repayment), and the HV threads are absent — HV_SS no-thread at honest prices, HV_GATE and +5V anchor stubs walled at start (named U10/Class A locality items). HV_INTVCC solo attempt follows.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 2 · Unconnected nets: 31 · Audit verdict: FAIL

### Pass 78 — 2026-11-05T05:55:12Z · commit `6b8c0bc`

Board: `hw/pdlvds_rx.exp15.kicad_pcb` · Commit: `6b8c0bc27e008c52c006b047df6f885ddb3fcce9`

U10 locality surgery 1 (Class A): U10.7 via escape placed in its proven east window — F neck (16.79,-14.50)->(17.20,-14.50), via 0.6/0.3 @(17.20,-14.50), In2 tail ->(19.20,-14.50), every shape collision-tested pre-placement (results/surgery-u10-escape.txt). Audit: violations still 2 (D1 standing lines only), nets 31 — HV_GATE's U10.7 group now reaches open field on In2. The companion +5V-trunk jog FAILED and is recorded: a MOS_G track fences every jog depth 18.95-20.10 (results/surgery-u10-jog.txt); U10.8/U10.9/U10.3 remain sealed by row arithmetic (0.5 pitch, 0.30 pads, 0.25 HV class: channel 0.70 < 0.75 demanded) plus that palisade.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 2 · Unconnected nets: 31 · Audit verdict: FAIL

### Pass 79 — 2026-11-05T06:00:28Z · commit `df4ef64`

Board: `hw/pdlvds_rx.exp16.kicad_pcb` · Commit: `df4ef64c9307e24675a044a595271584993fc070`

HV_GATE connected (Class A): targeted heal_nets on exp15 — the group extended by pass 78's In2 tail healed to the R27.1 group in 8 s, 1 via (results/heal-hvgate-exp16.txt). Audit: nets 31 -> 30, violations 2 (D1 standing lines only). HV_GATE leaves Classes A/R; U10.8/U10.9/U10.3 remain sealed (pass 78 findings) and ride the re-sync wave next.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 2 · Unconnected nets: 30 · Audit verdict: FAIL

### Pass 80 — 2026-11-05T06:46:17Z · commit `addb328`

Board: `hw/pdlvds_rx.exp21.kicad_pcb` · Commit: `addb328862b3e3ab29a944e1d8fe52b3ea4e6161`

U10.9 HV_SHDN connected (Class A): step-1 dense retest at the true 0.20 class found the one clear via site (17.25,-15.45) the radial probes never sampled — escape placed (hw/surgery_u10_9_escape.py: neck w=0.20, via 0.6/0.3, In2 tail east). heal_nets and thread_far both refused the pair (gap 6.28); the tail was hand-extended on In2 around the cluster (segments probe-verified with hw/probe_path.py) via (20.5,-21) west to the divider web, via up at (9.5,-18.9), F neck into the main track (hw/surgery_u10_9_connect.py), then zones refilled (hw/refill.py) so the pour carves the landing via's antipad. Audit (corrected checker, tools commit ed0d9b6): nets 30 -> 29; violations 11 = 2 D1 standing + 9 TP_HV (class opened by the census correction, fix queued in the re-sync). HV_SHDN leaves Class A; U10.8/U10.3 seals survive correct classes and ride the re-sync. (Record note: this pass was first committed against commit_pass.py's default board — the pre-expansion hw/pdlvds_rx.kicad_pcb — and redone in place before any push; always pass --board.)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 11 · Unconnected nets: 29 · Audit verdict: FAIL

### Pass 81 — 2026-11-05T07:06:04Z · commit `9cd6b93`

Board: `hw/pdlvds_rx.exp22.kicad_pcb` · Commit: `9cd6b93bc039263a12905217dea1962371aeb992`

RE-SYNC (pass 81): board absorbed the corrected 152-part schematic (hw/resync.py phases A+B, scratch/netlist_map.json). Footprint swaps in place: C4->ECWFD film (placed (18,16)), D4->D_SMB, L1/L2->Murata DFE, X1->HC49-SD, U9->redrawn TMP117_WSON6. HV cluster iterated: R31 string (R31+R49+R50) and R29 string (R29+R47) to the north row (y=-1.8), R34->(43,-6), R48 south of R30; D9-D11 OVP stack placed west strip (HV_RAW/HV_OVP1/HV_OVP2/GND). Board GREW again (user standing order): north edge -30 -> -45 after the grid placer proved the EFD20 T1 (23.11x26.1 body) has no feasible point in the 30 mm strip (flyback cluster fills its window); C9 nudged east, T1 placed (32.9,-31.4) in the new band. J5 interlock fitted at the west edge (3.5,-16.5): HV_SHDN run severed at the In2 segment above the divider via, 168 U6-side items reassigned to HV_EN (U6.97=PC7), J5 bridges HV_EN->HV_SHDN (SHDN side landed on the pass-80 via (9.5,-18.9)); HV_EN fully connected. TP_HV class: TP1 pad CLOSED (moved (45,20)->(39.5,20.5), disc-clear site, stub joined at (43.125,16.875)); the web's NE tail still grazes the GND run (3 lines) — class stays open on the tail only. Audit (corrected checker): nets 29 -> 44, violations 11 -> 69 — the recorded cost of the corrections: string/OVP midpoint hops unrouted, APD_K web in 10 groups, stale tracks to dead pad positions grazing the moved HV pads (drain classes, in order: HV-area campaign, Class A U10.8/U10.3, Class R, Class B).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 69 · Unconnected nets: 44 · Audit verdict: FAIL

### Pass 82 — 2026-11-05T08:27:06Z · commit `929ba23`

Board: `hw/pdlvds_rx.exp33.kicad_pcb` · Commit: `929ba23638bd8ee3ac81615e8b2cf77484dc1a6a`

SECURE (pass 82): commit the best on-disk board after the coordinator succession + VM replacement. Audited every exp board exp29-exp34 with the corrected checker: exp29 44/69, exp30 44/92, exp31 43/87, exp32 44/69, exp33 43/69, exp34 43/92. exp33 dominates: same 43 unconnected as exp34 with 23 fewer violations. Predecessor's hops.py surgery (written against exp34) never saved -- it crashed on the TP_HV re-stitch (blocked by HV_FBX at R50.2) before board.Save, so exp35 does not exist; the surgery script is committed separately and will be re-based onto exp33. bridge.py verified clean vs HEAD (no uncommitted changes). This pass changes no copper: it records exp33 as the secured base for the drain.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 87 · Unconnected nets: 43 · Audit verdict: FAIL

### Pass 83 — 2026-11-05T08:42:33Z · commit `606fe0c`

Board: `hw/pdlvds_rx.exp35.kicad_pcb` · Commit: `606fe0ca4da53274880547211bbc552439377fe2`

HV hops landed (hw/hops2.py on exp33 -> exp35): the predecessor's crashed surgery, rebased and completed. HV_R31A, HV_R31B, HV_R29M hops placed direct; GND stitch re-laid on In2 to clear the R29M corridor; R48 moved + HV_R30M In2 underpass; APD_K fence ripped (24 segs) and B.Cu re-feed placed (final via refused in-script by HV_FBX -- heal takes APD_K next); TP_HV re-stitch: hops.py's diagonal was geometrically impossible (crosses R50.2's 1.0 mm shadow) and the x=39.38 slot is empty at the 1.0 need -- routed F east at y=2.2, In2 drop at x=44.46 (0.3 internal need), via up at (44.9,-7.6), stub into R34.2; tail island deleted. Audit (corrected checker): nets 43 -> 39, violations 87 -> 67. Known residue in this state: TP_HV still audits 2 groups -- the In2 run ends at (44.46,-7.6), 0.14 mm short of the moved via at (44.9,-7.6); the link segment lands next pass. TP_HV zone grazes (8 lines) queue for the notch campaign.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 67 · Unconnected nets: 39 · Audit verdict: FAIL

### Pass 84 — 2026-11-05T08:46:56Z · commit `pending`

Board: `hw/pdlvds_rx.exp36.kicad_pcb` · Commit: `pending`

TP_HV closed: In2 link segment (44.46,-7.6)->(44.9,-7.6) joins the drop to the moved via (hw/fix_tphv_link.py). TP_HV leaves the unconnected list entirely -- the R50.2 block that killed the predecessor's run is broken and the net is routed end to end (F east at y=2.2, In2 drop, via up east of the CMP_QN run, stub into R34.2). Audit: nets 39 -> 38, violations 67 (TP_HV zone grazes remain for the notch campaign). Next: heal batches over the 2-group residue (ULPI x8, USB_RST, I2C, TMP_ALERT first).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 67 · Unconnected nets: 38 · Audit verdict: FAIL

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
is pass 11 here. Composite render backfilled on 2026-11-04 by rendering the board file as of this pass's commit; not contemporaneous with the pass.

