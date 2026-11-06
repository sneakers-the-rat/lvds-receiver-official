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

### Pass 84 — 2026-11-05T08:46:56Z · commit `fca498a`

Board: `hw/pdlvds_rx.exp36.kicad_pcb` · Commit: `fca498a30ef937fa7e96fd2c89a1d920bc01bee8`

TP_HV closed: In2 link segment (44.46,-7.6)->(44.9,-7.6) joins the drop to the moved via (hw/fix_tphv_link.py). TP_HV leaves the unconnected list entirely -- the R50.2 block that killed the predecessor's run is broken and the net is routed end to end (F east at y=2.2, In2 drop, via up east of the CMP_QN run, stub into R34.2). Audit: nets 39 -> 38, violations 67 (TP_HV zone grazes remain for the notch campaign). Next: heal batches over the 2-group residue (ULPI x8, USB_RST, I2C, TMP_ALERT first).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 67 · Unconnected nets: 38 · Audit verdict: FAIL

### Pass 85 — 2026-11-05T08:58:29Z · commit `fb95261`

Board: `hw/pdlvds_rx.exp37.kicad_pcb` · Commit: `fb952610b5e98749521a996c0045fb38dedf3434`

Heal batch A (heal_nets on exp36 -> exp37): I2C_SCL, I2C_SDA, TMP_ALERT connected (the redrawn U9's pads heal at once -- the footprint fix unblocked its locality). ULPI_D1-D6, ULPI_NXT, ULPI_STP, USB_RST refused by heal's A* at both endpoints (U6 lone pads and U7 stub groups) -- Class A seal at the fine-pitch U6/U7 field; they go to thread/escape tools next, not a second heal attempt. Audit: nets 38 -> 35, violations 67.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 67 · Unconnected nets: 35 · Audit verdict: FAIL

### Pass 86 — 2026-11-05T09:20:20Z · commit `6d73c4c`

Board: `hw/pdlvds_rx.exp38.kicad_pcb` · Commit: `6d73c4c7f0bf913502fbd082de3ac4da2c19c7de`

heal_big (15M cap) on exp37 -> exp38: +3V3D_CDR's U4.1 group merged (42 items, 2 vias); +5V 7 -> 5 groups (T1.1 group and the (26.42,-18.54) island connected). Refused in ~5 s each despite the diagnosis BFS reaching the goal halo (cost-model refusal, the Class B signature): U4.12, U11.10-12 cluster, U11.13, U7.4, U14.6 -- these go to thread/hand work, not a third engine attempt. Audit: nets 35, violations 67 (group counts fell; net count unchanged). NOTE: two VM replacements hit during this stretch (diagnose run SIGTERM'd at 805 s, toolchain restored from cache twice); committed work unaffected.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 67 · Unconnected nets: 35 · Audit verdict: FAIL

### Pass 87 — 2026-11-05T09:52:16Z · commit `d79fd23`

Board: `hw/pdlvds_rx.exp39.kicad_pcb` · Commit: `d79fd232350a5bdda5cfea6066460f3cb1b0c9ad`

Thread sweep 1 (thread_far, all 35 nets, exp38 -> exp39): 9 pair merges -- APD_K (0.09 gap), CDR_NIN (1.46), CMP_QN (0.17), GND (0.25), HV_DAC (0.08, net complete), HV_FBX (0.33), HV_RAW (1.16), HV_SEC (8.46, 12 segs 2 vias, net complete), XI (0.78, net complete). Most 'unconnected' groups were hairline stub gaps the audit grouping cannot join. Cost: HV_SEC's thread ripped 6 foreign items; violations 67 -> 75 and HV_RAW's merge was offset by a rip split (still 4 groups) -- rip victims are repaid by heal/thread rounds next. Refusals recorded: anchor-walled (+3V3A, +3V3D_CDR, +5V, CC2, PHY_1V8/A, SLICEN), lattice no-thread (HV_INTVCC, HV_SS, SET_P), pairs > 15 mm (ULPI x8, USB_RST, CAP_DATA, CDR_PIN, CDR_SQUELCH, CF2, DP_PHY, FLY_PRI, HV_SHDN). Audit: nets 35 -> 32, violations 75.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 75 · Unconnected nets: 32 · Audit verdict: FAIL

### Pass 88 — 2026-11-05T10:20:20Z · commit `d7173aa`

Board: `hw/pdlvds_rx.exp40.kicad_pcb` · Commit: `d7173aa4079fb6aefa3a50c0fbe9b3ef65491db9`

Thread sweep 2 (exp39 -> exp40): CDR_NIN completed (9.80 thread, 2 rips), CMP_QN threaded (2.14), GND and HV_FBX one pair each, HV_RAW hairline (0.01). Audit: nets 32 -> 31, violations 75 (thread rips keep the violation count flat while nets drain; the violation campaign follows the drain). Remaining 31 nets by refusal species: anchor-walled (+3V3A, +3V3D_CDR, +5V, APD_K, CC2, PHY_1V8/A, SLICEN), lattice no-thread (HV_INTVCC, HV_SS, SET_P), pairs beyond the 15 mm gate (ULPI x8, USB_RST, CAP_DATA, CDR_PIN, CDR_SQUELCH, CF2, DP_PHY, FLY_PRI, HV_SHDN). Next: heal_big over the full residue (different start machinery than thread's anchor), then hand escapes for what survives.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 75 · Unconnected nets: 31 · Audit verdict: FAIL

### Pass 89 — 2026-11-05T10:46:11Z · commit `74a2044`

Board: `hw/pdlvds_rx.exp41.kicad_pcb` · Commit: `74a20445741559bb4ddbeee2009f2bcce97e1be7`

heal_big batch 2 (exp40 -> exp41, checkpointed; GND tail stopped by hand after 27 connections when its 1-item subgroups proved to be item-model noise under the zone-defined audit): CMP_QN and FLY_PRI completed, +3V3A 3 -> 2 groups, APD_K 9 -> 5 (RJ2.2 group, R31.1, D1.5, R47.2 remain), GND item-subgroups merged without moving its audit count (zone fills define it). Refused again, all in ~0-7 s (sealed first millimetre): U4.12, U11.10-12, U11.13, U7.4, U14.6, U5.3, J1.B5, U4.5, U4.27, C15.2, U7.7. Audit: nets 31 -> 29, violations 75. Next: escape-fan census over the sealed pads, hand escapes into open field, then heal/thread take the lengthened stubs.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 75 · Unconnected nets: 29 · Audit verdict: FAIL

### Pass 90 — 2026-11-05T11:11:16Z · commit `62a9130`

Board: `hw/pdlvds_rx.exp42.kicad_pcb` · Commit: `62a9130bd0ccd8aa74660c1a8d1cb6778b9625d8`

Escape batch 1 (exp41 -> exp42): APD_K island joined to main via R34.1 pad (section I), GND R48.2 stub south (section L). The other 9 sections were refused by named blockers and are reworked in batch 2/3 with measured pad geometry. Audit follows in stats.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 77 · Unconnected nets: 29 · Audit verdict: FAIL

### Pass 91 — 2026-11-05T11:39:02Z · commit `6d96307`

Board: `hw/pdlvds_rx.exp49.kicad_pcb` · Commit: `6d963074a40af544cac00855c919bf1f501d93db`

Escapes 3-8 (exp42 -> exp49): +3V3A COMPLETE (U7.6 west exit, In2 hop under the ULPI bank), HV_INTVCC COMPLETE (neck-width turn through the EP/GATE window, via-up hunted to (13.4,-10.8)), HV_SS stubbed to In2, HV_FBX stubbed to a via, R34 moved 1.5mm north (placement) with APD_K/TP_HV re-joins placed. Board state per audit.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 80 · Unconnected nets: 27 · Audit verdict: FAIL

### Pass 92 — 2026-11-05T11:56:56Z · commit `10642b3`

Board: `hw/pdlvds_rx.exp50.kicad_pcb` · Commit: `10642b30079d3153bd3d60af9a80a5d888d14aca`

Escapes 9 (exp49 -> exp50): R50 moved (-2.0,-0.8) opening the HV_RAW via-gap lane, orphaned FBX/R31B hops ripped for re-route, U14.6 via down to B, VBUS picket ripped for CC2. Audit records the state.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 82 · Unconnected nets: 29 · Audit verdict: FAIL

### Pass 93 — 2026-11-05T12:03:31Z · commit `677fc3e`

Board: `hw/pdlvds_rx.exp51.kicad_pcb` · Commit: `677fc3e65174b22f39ee6f07f6c11246e247f26e`

Escapes 10 (exp50 -> exp51): CC2 COMPLETE (east jog at y=72.3 under the A9/B4 pads) + VBUS_RAW re-feed placed; HV pocket sections refused on named blockers (R31.2 shadow, APD_K via, ILIM_A B track) -- batch 11 re-plans them with real pad bboxes. Audit records the state.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 82 · Unconnected nets: 28 · Audit verdict: FAIL

### Pass 94 — 2026-11-05T12:22:58Z · commit `b0429cb`

Board: `hw/pdlvds_rx.exp52.kicad_pcb` · Commit: `b0429cb4f0bb488fbfa5c17ff111f3f31b446d52`

Escapes 11 (exp51 -> exp52): R50 shifted +1.14 east (fixes the batch-9 pad overlap with R31.2), HV_R31B re-join CONNECTED; FBX and HV_RAW vias refused by the CMP_QN B staircase / FBX In2 vertical (named blockers, batch 12 re-plans with a placement move); HV_SS In2 hop refused -- its seal is geometric (one 1.0-class dive channel at U10 for two HV nets).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 81 · Unconnected nets: 27 · Audit verdict: FAIL

### Pass 95 — 2026-11-05T12:32:01Z · commit `c10f030`

Board: `hw/pdlvds_rx.exp53.kicad_pcb` · Commit: `c10f0307e58c6dfd9195d19eb7e52cec03c1794a`

Escapes 12 (exp52 -> exp53): PLACEMENT BREAK of the pocket seesaw -- R49+R50 moved SW as a unit (-6,-5.5) into the open field south of the FBX web (one GND stitch ripped); HV_R31B re-join and HV_FBX direct hop to the web both landed. HV_RAW via refused on TP_HV stub proximity; FBX dive re-site refused by HV_VC web (restored in batch 13); HV_SS west leg refused on FBX stub -- its U10 seal is geometric, mechanism named in notes.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 78 · Unconnected nets: 28 · Audit verdict: FAIL

### Pass 96 — 2026-11-05T12:38:20Z · commit `801534a`

Board: `hw/pdlvds_rx.exp54.kicad_pcb` · Commit: `801534acd82f7f02cf1bc095e6beb777f9f870a9`

Escapes 13 (exp53 -> exp54): APD_K In2 staircase repaired (5 segments re-placed exactly after batch 12 collateral rip), HV_FBX dive via restored at (10.12,-15.38); HV_RAW F continuation refused by the APD_K via (41.12,-4.38) -- batches 14-16 take the north route instead. (exp55/exp56 were intra-batch waypoints of that route, folded into the next pass.)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 78 · Unconnected nets: 28 · Audit verdict: FAIL

### Pass 97 — 2026-11-05T12:44:41Z · commit `b7e658f`

Board: `hw/pdlvds_rx.exp57.kicad_pcb` · Commit: `b7e658ff65ec416ecb11bf93ada7bfff74d21f50`

Escapes 14-16 (exp54 -> exp57): HV_RAW north route COMPLETE -- F from the R29.1 fan, north around the APD_K via (41.12,-4.38), west at y=-2.7 (dead FBX orphan stub ripped), south at x=39.3 into the island track; HV_RAW down to main + D9.1. Audit: 28 nets / 78 violations; TP_HV and HV_R31B fully connected.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 78 · Unconnected nets: 28 · Audit verdict: FAIL

### Pass 98 — 2026-11-05T12:57:16Z · commit `90df97a`

Board: `hw/pdlvds_rx.exp58.kicad_pcb` · Commit: `90df97aad6696782947a3592194f9e2cd8b8dcc9`

Thread sweep 3 (exp57 -> exp58): VBUS_RAW threaded closed, APD_K + GND one pair each -- but thread rips re-split CC2 (the seesaw in miniature: 28 nets / 77 violations, composition churned). Per parent directive the U6/U7 respread placement is adopted next; this pass is the last on the old geometry.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 77 · Unconnected nets: 28 · Audit verdict: FAIL

### Pass 99 — 2026-11-05T13:01:06Z · commit `3c2d5d6`

Board: `hw/pdlvds_rx.exp59.kicad_pcb` · Commit: `3c2d5d6c4eb043f6a2d77e4f478d567db64a458f`

RESPREAD ADOPTED (exp58 -> exp59): U6 -> (82,-6), U7 -> (76,14), X1 -> (87,14) rot90 + full ring, applied via respread_u6u7_local.py (local-rip path) to the current board -- no restart from exp41. 932 items ripped (severance debt ~36 nets, itemised in results/respread-local-exp59.txt). Post-placement audit: 65 nets / 168 violations (zones un-refilled; refill next). ULPI hauls drop from ~66mm to 8-19mm in the new geometry.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 168 · Unconnected nets: 65 · Audit verdict: FAIL

### Pass 100 — 2026-11-05T13:04:01Z · commit `0eb765f`

Board: `hw/pdlvds_rx.exp60.kicad_pcb` · Commit: `0eb765f57a8517198ecba95511ba38ff934e08ad`

Zone refill after the respread (exp59 -> exp60): violations 168 -> 71 (below the pre-respread 77); 65 unconnected nets = 28 pre-existing + ~37 severance debt, the recovery campaign follows. ULPI fanout-first heal rounds next per parent order.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 65 · Audit verdict: FAIL

### Pass 101 — 2026-11-05T13:08:43Z · commit `268880a`

Board: `hw/pdlvds_rx.exp61.kicad_pcb` · Commit: `268880aa0cb6ce0712174edad98e2e415544cef8`

ULPI fanout heal round 1 (exp60 -> exp61): D0, D1, D4, D6, D7, NXT CONNECTED in the new geometry (audit 65 -> 59 nets). Residue: single U7 pads D2/D3/D5/DIR/CK/STP/RST sealed at heal's first move (fanout-order problem) -- round 2 stubs them by hand first, then heals. Violations 71 -> 81 from heal grazes, violation campaign queued.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 81 · Unconnected nets: 59 · Audit verdict: FAIL

### Pass 102 — 2026-11-05T13:14:26Z · commit `a66d6cd`

Board: `hw/pdlvds_rx.exp62.kicad_pcb` · Commit: `a66d6cdfeb583ddd1bbe5f9803b320b1f0633f1e`

Escapes 17 (exp61 -> exp62): ULPI residue-first stubs -- fence segments of D7/NXT ripped (they re-heal after the residue), D4 diagonal ripped back to its pad stub; stubs placed for D2, D3, DIR, STP, CK. D5 stub refused (one D4 staircase segment survived a shifted rip match) and RST stub refused by an NXT diagonal -- both fixed in batch 18.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 81 · Unconnected nets: 62 · Audit verdict: FAIL

### Pass 103 — 2026-11-05T13:29:22Z · commit `091b643`

Board: `hw/pdlvds_rx.exp63.kicad_pcb` · Commit: `091b6432f85da5d318abe174920279d8bf00918a`

Escapes 18 (exp62 -> exp63): surviving D4 staircase segment ripped (tight tolerance), D5 stub placed; RST stub refused again by the NXT diagonal (batch 19 rips it). Heal round 2 runs on this board.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 81 · Unconnected nets: 62 · Audit verdict: FAIL

### Pass 104 — 2026-11-05T13:40:49Z · commit `b7db9f1`

Board: `hw/pdlvds_rx.exp64.kicad_pcb` · Commit: `b7db9f141c32da836e17e14bd3aef564fd99d44f`

ULPI fanout heal round 2 (exp63 -> exp64): D5, DIR, CK CONNECTED; D7 and NXT re-connected after their fence rips. Residue moved to the U6 side (U6.47/U6.69/U6.26 bare pads) + D4 pad re-entry + RST. Post-fanout audit: 54 nets / 82 violations (from 65/71 at adoption).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 81 · Unconnected nets: 57 · Audit verdict: FAIL

### Pass 105 — 2026-11-05T13:57:16Z · commit `21f47f4`

Board: `hw/pdlvds_rx.exp65.kicad_pcb` · Commit: `21f47f49a306431708701ba4698dfad78198b482`

Escapes 19-20 (exp64 -> exp65): U6-side ULPI stubs placed for D2 (south, shortened clear of D0 track), D3 (west), STP (west); NXT diagonal ripped for RST. Heal round 3 then connected nothing (U7 stub groups walled in heal model) -- hand routes follow.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 81 · Unconnected nets: 58 · Audit verdict: FAIL

### Pass 106 — 2026-11-05T13:59:22Z · commit `b87c4ee`

Board: `hw/pdlvds_rx.exp68.kicad_pcb` · Commit: `b87c4eecd254424a252052898bc8011dba4094e1`

Escapes 21 (exp67 -> exp68): D5 F stubs ripped for the D4/D5 order fix; D4 and D2 hand routes refused on named blockers (CDR_DATP via, U7.23 pad) -- re-aimed in batches 22-24. exp66/exp67 were engine-attempt states with no connectivity change, folded here.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 81 · Unconnected nets: 59 · Audit verdict: FAIL

### Pass 107 — 2026-11-05T15:03:19Z · commit `5dcacab`

Board: `hw/pdlvds_rx.exp79.kicad_pcb` · Commit: `5dcacab9b39eb885ab792c3c206931bf777d2bf8`

Campaign + ULPI knot work (exp68 -> exp79, cumulative): general heal campaign landed 68 groups over the severance debt (post-campaign audit exp73 = 36 nets / 87 violations, down from 65/71 at respread adoption and 59/81 at pass 104); ULPI heal round rejoin (NXT); knot batches 26-30 -- ULPI_D4 COMPLETE (tail into its via after the D5 vertex rip), ULPI_DIR rejoined (F seg + via placed batch 27, B legs into its staircase batch 29), USB_RST stub placed, D5/D6 fanout fences ripped for the order fix, D2 spur + D1 diagonal + CDR_DATP via ripped, D3 F approach seg placed. exp69-exp78 intra-campaign/batch states folded into this pass. ULPI residue (D1 pad group, D2, D3, D5, D6, STP) is a named knot: hand batches 22-30 + thread_far all refused on the U7 row channel shared with campaign-routed CDR_DATP/D1/D0 copper -- carried as named residual, rest of board proceeds.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 87 · Unconnected nets: 38 · Audit verdict: FAIL

### Pass 108 — 2026-11-05T16:54:46Z · commit `036be9c`

Board: `hw/pdlvds_rx.exp81.kicad_pcb` · Commit: `036be9c586201a1e4cfab0ab553eee5b776cf093`

Heal campaign exp79->exp81 over 30 non-knot nets (heal_nets, results/heal-exp81.log). DELTAS: nets 38->33, violations 87->120. Joins: HV_R31A, HV_FBX, CDR_DATP, ULPI_DIR connected outright; APD_K 6->5 groups (C33/C4/R30 cluster merged). Violation delta +33 concentrated in ONE join: 32 lines from heal's HV_RAW B.Cu surface diagonal vs the GND pours at the 1.0 mm HV class, +1 XI vs a new CDR_DATP via at (87.125,16.625). HV_RAW's join exceeds the acceptance bound; it is ripped and re-approached (In2 bridge + D9 pour notch) in the next pass. All other joins landed clean (0 new violations). Still isolated after heal (residue for hand work): SLICEN U4.7, SET_P U13.7, +3V3D_CDR U4.12 group, +5V U11/U7.4 groups, PHY_1V8 U7.15/U7.26, PHY_1V8A C23.1, APD_K R31.1/D1.5/R47.2/RJ2.2, CC2 J1.B5 group, +3V3A U7.6/16/25, U6/U7 single pads (CAP_CLK, CDR_LOL, CDR_SQUELCH, HV_EN, HV_SHDN, SWDIO, USB_RST, VCAP1), CDR_PIN U4.5 group, CF2 C15.2 group, DM_PHY/DP_PHY U7 pads, RBIAS U7.32, XI/XO X1-site groups.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 120 · Unconnected nets: 33 · Audit verdict: FAIL

### Pass 109 — 2026-11-05T16:59:39Z · commit `d408fc5`

Board: `hw/pdlvds_rx.exp82.kicad_pcb` · Commit: `d408fc552430493917d875229dcb91165091bebd`

HV_RAW re-approach (hw/fix_hvraw.py): heal's B.Cu surface diagonal ripped (63 items) and the D9.1 haul re-bridged on In2 -- F neck to via (5.38,-24.88), In2 southern run y=-24.88 to x=22.2, corridor north at x=22.2, northern approach into via W (34.12,-11.88), F necks into the D5.1 web; D9 pour notch (notch.py species, rule areas 1.25,-27.5..7.03,-22.5 on F+B) added so the pours hold >=1.0 mm from the D9 pocket. Every placed shape was tested against the audit's own item model including zone fills. DELTAS vs pass 108: nets 33->33 (join retained, mechanism changed), violations 120->87 (-33: -32 HV_RAW diagonal-vs-pour lines removed by the rip, -1 pre-existing 'HV_RAW D9.1 vs GND zone' line cured by the notch, +0 new lines from the In2 bridge). Acceptance test PASSED (full audit results/audit-exp82.txt: 33/87; the single exp82-vs-exp79 newcomer, XI vs the CDR_DATP via, belongs to pass 108's CDR_DATP join).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 87 · Unconnected nets: 33 · Audit verdict: FAIL

### Pass 110 — 2026-11-05T17:23:51Z · commit `197acbd`

Board: `hw/pdlvds_rx.exp83.kicad_pcb` · Commit: `197acbdbb06c3e2b1c964356fbc209e43e28a8fe`

SLICEN connected (hw/fix_slicen.py): pure-F northern jog from U4.7 -- hand_stub and hand_via both refused (SLICEP's escape via at (51.5,-17.5) fences the west lane: 0.6 mm exclusion vs 0.25 mm row offset); pair re-lay grid-searched and refused on evidence (+3V3D In2 trunk fences SLICEP's via to its original row, CDR_NIN diagonal fences its neck). Jog: west on-row to (52.08,-17.25), steep rise to (51.72,-16.82), west into the group track end (51.38,-16.88); one GND stitch via relocated (52.125,-16.625)->(52.45,-15.85) out of the rise corridor. DELTAS vs pass 109: nets 33->32 (SLICEN joined), violations 87->87 (census byte-identical, +0 new). GND groups unchanged.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 87 · Unconnected nets: 32 · Audit verdict: FAIL

### Pass 111 — 2026-11-05T17:52:47Z · commit `4331784`

Board: `hw/pdlvds_rx.exp89.kicad_pcb` · Commit: `433178454c7120888ef1d984eaafdf4de9f3b421`

SET_P connected: U13 relocated + re-heal of its 6 nets (hw/move_u13.py, heal_nets, hw/fix_u13_6.py). The decided (-4,0) west move is REFUTED on the current field (exact pad check): destination lands in the routed NEG_RAW staircase web (EP vs 18 tracks, ILIM_P/+5V pins vs more, need 0.25). Full-ring placement search (dx -8..+2, dy -7..+7) found one clean cluster SW; executed (-6.75,-7.00) -> U13 at (41.25,55.00), pin 7 0.47 mm from the SET_P web. One SET_P web vertex (via 43.875,61.375 + 2 segments) ripped pre-move; heal re-bridged it. heal joined SET_P/+VA/ILIM_P and +5V pins 1/2/3; U13.6 (+5V) refused twice more (stubbed and unstubbed) and the pure-F west bridge was refused on the GND/DM_PHY/ILIM_P braid -- landed as a one-via B.Cu hop: via (42.68,56.28) overlapping the pad, B run NW into the +5V B staircase at (41.75,53.25). DELTAS vs pass 110: nets 32->31 (SET_P joined, +5V back to its 4 pre-existing groups), violations 87->87 (census byte-identical, +0 new).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 87 · Unconnected nets: 31 · Audit verdict: FAIL

### Pass 112 — 2026-11-05T18:48:09Z · commit `6df00a1`

Board: `hw/pdlvds_rx.exp94.kicad_pcb` · Commit: `6df00a118777ace8727ace42f44bf9bd1b630a9c`

U4 north gate re-woven; +3V3D_CDR haul REFUSED in all topologies (named residual, full record in hw/fix_gate.py + hw/fix_gate2.py docstrings). Ripped the clock pair's woven escapes + REFCLK's two junction vias; heal then connected +3V3D_CDR through the gate (via 54.38,-14.38 + B west run) but that route re-sealed both clock stubs (via-disc tiling, verified site-by-site). Reversed the order: ripped heal's +3V3D_CDR gate route (7 items), hand-laid REFCLKN (F north + flat into its tail (55.5,-14.5)) and REFCLK (F north at x=53.75, swerve over THRADJ's via, B bridge over CDR_LOL, In2 drop onto its own tail at (57.35,-13.65)) -- both clocks CONNECTED on the audit. heal +3V3D_CDR then refused on the clock-placed field (its optimum is the ripped route), and ~15 hand channel forms were shape-refused: the gate's F/In2/B capacity fits only 2 of the 3 nets in every topology tried (In1 is an unused plane layer board-wide -- 0 tracks -- and stays unused). DELTAS vs pass 111: nets 31->31, violations 87->87, unconnected list and clearance census BYTE-IDENTICAL -- topology change only: heal's blocking route is off the board and the clocks hold the new routes, which is the prerequisite field for the next +3V3D_CDR mechanism (east-column re-lay of CF1's B staircase + CDR_LOL's escape). +3V3D_CDR stays split: stub (54.75,-15.45) vs main group.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 87 · Unconnected nets: 31 · Audit verdict: FAIL

### Pass 113 — 2026-11-05T19:51:10Z · commit `258c23d`

Board: `hw/pdlvds_rx.exp101.kicad_pcb` · Commit: `258c23d8cf8d97b89413338b96d384f25ddd3509`

U7 west-column escapes + residue stubs harvested. Ripped the CAP_CLK/ULPI_NXT F palisade (x=71.88/72.62 verticals + 2 NXT diagonal steps -- via-proof pair, 0.74 apart vs 0.625 needed each side; pad row equally sealed at 0.25 gaps) and laid the four row lanes west on F: +3V3A U7.6 CONNECTED via its lane + heal to the (74.12,10.38) staircase; +5V U7.4, DP_PHY U7.7, DM_PHY U7.8 lanes placed as open-field anchors (heals refused the 55-65mm D3 hauls and the +5V main-group haul -- Class B long-haul residue, anchors in place). Palisade repaid: heal rejoined ULPI_NXT (13 items, 0 vias) and CAP_CLK's split (44 items). bridge (exp99, pre-pass) had connected +3V3A U7.16 (gap 1.99) but ripped 2 victims: ULPI_D7 (rejoined by heal) and ULPI_CK's F->In2 junction via at (77.62,17.88) (restored by hw/fix_ckvia.py, site shape-tested clean). Also in the chain: hand_stub escapes on exp95 for HV_EN/HV_SHDN/VCAP2/PHY_1V8A/RBIAS/XI and hand_via vias for CDR_SQUELCH/SWDIO (anchors for the heal campaign); fix_escape placed a +3V3A U7.16 via (redundant with bridge's join). XO U7.27 named sealed: DATP via (76.88,10.62) + XI stub + PHY_1V8 pad fence every exit -- north-row rework residue. heal/heal_big/thread_far went 0-for on the stubbed singles (grid anchor wall + 15mm pair gate) -- the lane/via hand escapes are the working vehicle for this family.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 87 · Unconnected nets: 31 · Audit verdict: FAIL

### Pass 114 — 2026-11-05T20:29:34Z · commit `2250037`

Board: `hw/pdlvds_rx.exp106.kicad_pcb` · Commit: `22500376c306fc100b4669497a6822c73f1cac1c`

Drainable queue harvest (parent queue-order directive). LANDED: CAP_CLK fully connected (thread_far from the U6.34 west lane, gap 2.55); CC2 connected (bridge, gap 1.20); APD_K R31.1 joined the main group (bridge gap 2.72 then 0.02 after its first seg landed short); GND stitch clusters merged 5->4 groups (bridge gap 0.25). VICTIMS NAMED AND MOSTLY REPAID: CAP_CLK thread ripped BOOT0 (re-threaded, gap 7.75); CC2 bridge ripped VBUS_RAW (re-bridged, gap 0.85); APD_K bridge ripped HV_FBX x2 in the (31,-2.5) field -- HV_FBX STILL SPLIT (bridge gap 1.33 unplaced; repay is next); BOOT0 thread ripped ULPI_STP's U6.26 neck track (71.34,-2.25) -- STP's U6 group is a bare pad again, repay queued with the knot work (priced mechanisms still parked per directive). thread_far went 0/8 on VCAP2/PHY_1V8A/XI/+3V3A/PHY_1V8/USB_RST/XO/CF2 (anchor wall / pair gate) and heal_big 0/2 on CAP_CLK/CDR_LOL pad groups (fanout model: starts are pad cells only). CDR_LOL lane anchor in place at (69.9,2.75) for the east-column re-lay.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 83 · Unconnected nets: 31 · Audit verdict: FAIL

### Pass 115 — 2026-11-05T20:44:51Z · commit `cac7c75`

Board: `hw/pdlvds_rx.exp107.kicad_pcb` · Commit: `cac7c75ba6182a55ca0e537bcabcbae3ea3f7dee`

HV_FBX repaid (owed from pass 114). Ripped group 1's 9-track F.Cu spur west of (33.25,-4.5) -- the dead-end branch whose north end stopped 1.33 mm short of group 0's In2 run with the only via site inside R31.1's APD_K 1.0 mm disc (pass 114's refused repay). Bridge landed on B.Cu via-to-via: (26.125,-4.625) group-0 via -> (30,-5.0) -> (33.875,-5.375) group-1 via, w=0.3. Refused on evidence first: F corridors y=-4.80/-5.05 (GND tail track x=30.38, y -4.975..-3.025), F y=-5.50 (R50.1 HV_R31B 1.0 mm disc), In2 via-to-via (HV_R31A run fills the In2 corridor). DELTAS vs pass 114: nets 31->30 (HV_FBX joined), violations 83->75 (-8: every APD_K-vs-HV_FBX spur line removed; census diff shows 0 new lines). No victims.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 75 · Unconnected nets: 30 · Audit verdict: FAIL

### Pass 116 — 2026-11-05T21:26:20Z · commit `bbf0942`

Board: `hw/pdlvds_rx.exp108.kicad_pcb` · Commit: `bbf0942f28383423d8262e4d4fb7f254f7616bc4`

APD_K R47.2 group connected (queue item 1, leg 1 of 3). Diagnosis: TMP_ALERT's B.Cu vertical at x=49.12 was the pocket's last wall -- APD_K (HV) needs 1.0 mm from it on every layer a via spans (hand_via 0/3, heal 1 s refusal, thread_far no-thread all on record). Fix (hw/fix_r47.py): TMP_ALERT repaid in-pass (B vertical ripped south of y=1.20, re-laid on In2 from its own via, via back at (49.12,1.20), B north re-placed); pour notch F+B x[46.20,51.45] y[-3.10,-0.10]; APD_K via (50.05,-1.60) + In1 west run onto the main web's via (41.12,0.62). DELTAS vs pass 115: nets 30->30 (APD_K groups 4->3), violations 75->72 (-3 cured: R47.2 pad, old stub track, R47.1 -- all vs GND zone; +0 new. First notch cut with east edge 51.15 left the new via 0.8 mm from the fill and cost +3 zone lines; widened to 51.45, re-audited clean). No victims: TMP_ALERT connected after repay, GND still 4 groups.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 72 · Unconnected nets: 30 · Audit verdict: FAIL

### Pass 117 — 2026-11-05T21:35:24Z · commit `9a17ea0`

Board: `hw/pdlvds_rx.exp109.kicad_pcb` · Commit: `9a17ea002447bfff744c41df914933e09b2f317e`

APD_K D1.5 leg connected (queue item 1, leg 2 of 3). D1.5 is ringed by its own footprint's APD_A pads at 0.40-0.50 mm gaps, so any surface exit starts inside the 1.0 mm surface class -- the geometry behind the 2 standing APD_K-vs-APD_A lines. Fix (hw/fix_d15.py): ONE diagonal F neck (9.20,40.00)->(11.00,38.50) whose exact-test blockers are D1.4 and D1.6 only (script asserts all blockers are APD_A and aborts otherwise), via at (11.00,38.50) (nearest clear site in a 0.25-grid disc scan), In1 south+east runs onto the main web's via (13.62,30.62). DELTAS vs pass 116: nets 30->30 (APD_K groups 3->2; only the RJ2.2 leg remains), violations 72->74 (+2, exactly the two predicted sibling-pad lines APD_A (D1.4)/(D1.6) vs the neck track -- same standing D1-footprint species as the 2 gated lines, geometrically forced: no via site reachable from D1.5 clears 1.0 mm from both pads). No victims.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 74 · Unconnected nets: 30 · Audit verdict: FAIL

### Pass 118 — 2026-11-05T21:55:19Z · commit `1c4fe11`

Board: `hw/pdlvds_rx.exp110.kicad_pcb` · Commit: `1c4fe11964d26d9a6aa11a52f18d8371670b2edb`

GND islands closed (queue item 2): all 4 groups merged to 1. Stitch vias to the In1 GND plane (stitch_track.py): cluster track@(83.375,0.125), C34.2 tail track@(29.775,-2.25); hand_via via stub for the lone R32.2 pad (via (30.77,-3.80)). DELTAS vs pass 117: nets 30->29 (GND connected), violations 74->74 -- census byte-identical (the R32.2-vs-R31.1 1.0 mm line is pad-placement geometry, carried to the violation campaign). No victims. Also this session: APD_K RJ2.2 leg (item 1, leg 3) stands as a named residual -- hand_stub/hand_via/heal x2/thread_far gate/exact via-scan all refused and the APD_A_ALT crossing-swap dive site was refused on +3V3D/FB_3V3/GND blockers; untried mechanisms are a full connector-corner re-fanout or an RJ1/RJ2 move. Tooling: heal crash on In1 copper fixed with regression test in commit 8ffdef7.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 74 · Unconnected nets: 29 · Audit verdict: FAIL

### Pass 119 — 2026-11-05T22:32:25Z · commit `7ddc20b`

Board: `hw/pdlvds_rx.exp111.kicad_pcb` · Commit: `7ddc20bdc9cde5ecf3a6e41300897ea028327b80`

CC2 rejoined (queue item 3): F hop (30.50,72.55)->(31.30,72.34)->(31.90,72.30) w=0.20 threaded through the 0.125 mm window at x=31.10 between J1.B4's pad (0.25 class) and J1.A9's escape start. VBUS_RAW's F jumper (31.15,72.83)->(31.00,71.98) -- A9's sole link -- ripped and repaid in the same pass: escape extended (31.85,70.88)->(32.05,70.68), via (32.05,70.68), B run south then diagonal west onto VBUS_RAW's own B diagonal chain at (28.00,72.25); VBUS_RAW still 1 group. First hop cut cost +3 (74->77: B4 pad + A9 escape x2) and was re-approached, not kept. DELTAS vs pass 118: nets 29->28 (CC2 connected), violations 74->74, census byte-identical. No victims (VBUS_RAW repaid in-pass).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 74 · Unconnected nets: 28 · Audit verdict: FAIL

### Pass 120 — 2026-11-05T22:53:27Z · commit `3a26a18`

Board: `hw/pdlvds_rx.exp112.kicad_pcb` · Commit: `3a26a18d62750578a8534d19a53b70ab9822f1d8`

ZOMBIE PRUNE (owner-directed cleanup): new standing tool hw/prune_dead.py leaf-trims dead branches on a geometric copper graph (pads and pour contacts are terminals; through-paths stay) and proves the invariant in-process before saving: the per-net pad-group partition under the audit's own connectivity model (pads+tracks+vias+zone fills, Collide-0) is IDENTICAL before/after -- no net moved, no net reverted. REMOVED: 392 segments (0 vias), 126 overshoot tracks shortened, 385.9 mm of dead copper. Worst offenders: GND -101 segs (75.7 mm), SWDIO -18 segs (60.9 mm -- an entire superseded route), CDR_DATP -46 (24.2 mm), ULPI_D0 -22 (20.2 mm), HV_EN -6 (19.1 mm), TMP_ALERT -14 (18.5 mm), CAP_CLK -25 (10.9 mm), I2C_SDA -27 (10.6 mm); the old U6-site fanout field around (69-78,33-41) accounts for the NRST/CAP_CLK/TMP_ALERT share. DELTAS vs pass 119: nets 28->28 (identical partitions), violations 74->71 -- 3 lines cured, all zombie GND tracks in the HV field (HV_R31A R49.1 vs GND track@(30.375,-12.625); TP_HV track@(44.375,18.125) vs GND tracks x2), zero new lines. Tool stays in hw/: run after any placement move as a matter of course.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 28 · Audit verdict: FAIL

### Pass 121 — 2026-11-05T23:03:34Z · commit `ed32afa`

Board: `hw/pdlvds_rx.exp113.kicad_pcb` · Commit: `ed32afaa472c114246b42c4c590841e9aefe96f4`

+3V3A U7.25 connected (queue item 4): via d=0.45 at (77.98,11.65) in the north-east corner -- overlaps U7.25's own pad edge, clears U7.24 (ULPI_D0) by 0.25 shape distance, and touches the In2 mesh segment (77.88,11.62)->(77.62,11.88); F stub (77.80,11.75)->(77.98,11.65). Refused on record: via on the pad or onto the mesh NE (QFN pitch + ULPI_CK's F staircase at 0.25 class on every site) and the F west channel run in 4 variants (ULPI_CK wall + CDR_DATP via (76.88,10.62) + XI/PHY_1V8A escape nubs tile the channel). DELTAS vs pass 120: nets 28->27 (+3V3A connected), violations 71->71, census byte-identical. No victims.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 27 · Audit verdict: FAIL

### Pass 122 — 2026-11-05T23:23:24Z · commit `eadd3bc`

Board: `hw/pdlvds_rx.exp114.kicad_pcb` · Commit: `eadd3bcfdf4c36ea14547ffdc3e5d4e6156d677d`

XI/XO (queue item 5) stand as NAMED RESIDUALS; XI fanout ray placed as the heal-enabler attempt. XO: U7.27 SEALED -- hand_stub refuses all 16 directions; every via site tiled by the CDR_DATP via (76.88,10.62) at 0.03-0.155mm, ULPI_CK's wall and U7.26 PHY_1V8's pad; the only mechanisms are the coordinated CDR-pair relay or a U7 move (both parked with the ULPI knot). XI: heal refused before AND after this ray (pad-cell seal in the grid model), thread_far refused (gap 8.45, no thread); remaining mechanisms are the west-corridor hand-route (crosses +3V3A's 0.60 west trunk + the GND field at y19-22, multi-via marginal windows) or the pair relay. This pass places ONLY the XI ray: nub extended (76.25,11.03)->(76.25,10.55) + west bend ->(75.85,10.55), exact-tested clean; no via fits at the ray (CDR_DATP buried staircases). DELTAS vs pass 121: nets 27->27, violations 71->71 expected (audit verifies), XI groups unchanged 2. No victims. NEXT: queue item 6 (east-column +3V3D_CDR + CDR_LOL), then the residue family.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 27 · Audit verdict: FAIL

### Pass 123 — 2026-11-06T00:01:14Z · commit `29ad408`

Board: `hw/pdlvds_rx.exp116.kicad_pcb` · Commit: `29ad40873e999f6f1cb2a73941a3270ef74ac310`

Batch heal over all 24 remaining nets (heal starts from each net's SMALL group; several small groups sit in open grid even when the far end is sealed): ULPI_D1, ULPI_D3 (3 vias, 75s search) and ULPI_D6 CONNECTED -- the ULPI knot loses three members; +5V closed two of its four groups (7-item group via 1 via; 2-item group direct), leaving [U7.4 group] vs main. All other nets refused by heal (pad-cell seals at the QFP/QFN rows; CF2/DP_PHY/HV_SS/PHY_1V8A/ULPI_D2 searches exhausted the 1.5M cap against enclosed target pockets). DELTAS vs pass 122: nets 27->24 (D1, D3, D6), violations 71->71, census byte-identical -- heal's grid routes audited clean. No victims. LEFT: 24 nets; knot remainder D2/D5/STP + USB_RST; named residuals XI, XO, +3V3D_CDR, CDR_LOL unchanged.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 24 · Audit verdict: FAIL

### Pass 124 — 2026-11-06T00:12:25Z · commit `146a6ef`

Board: `hw/pdlvds_rx.exp117.kicad_pcb` · Commit: `146a6ef734b761fdcfb9463198b220a9559cb834`

Standing prune (owner's instruction: after any route change) over pass 123's heal copper: 6 dead 0.2mm segments removed (CAP_DATA, CDR_SQUELCH, I2C_SCL, HV_SHDN, VCAP2, PHY_1V8A), 6 tracks shortened (I2C_SDA, SET_P x2, ULPI_CK, VCAP1, HV_VC); partition proof passed for all nets (none moved, none reverted). DELTAS vs pass 123: nets 24->24, violations 71->71, census byte-identical. No victims.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 24 · Audit verdict: FAIL

### Pass 125 — 2026-11-06T00:52:47Z · commit `3b0f4fd`

Board: `hw/pdlvds_rx.exp118.kicad_pcb` · Commit: `3b0f4fd52ba21bd2804e7f19e9ce4a93aa138f82`

COURTYARD CAMPAIGN item 0 (audit blindness): courtyards drawn for the five drawable blind footprints D1, D2, C4, U9, T1 — board instances + hw/pdlvds.pretty library (text insertion of fp_line rectangles: KiCad 7.0.11's writer zeroes FP_SHAPE points set through the Python API, verified in-session; hw/draw_courtyards.py is the instrument). Blind list 6 -> 1: SH1 remains (shield can enclosing the frontend it covers by design; closure is the pending clip-pattern conversion, parts audit; the audit's bbox-fallback line reports it every pass). Drawing the courtyards REVEALED 8 new gated pairs, now counted and queued: L1xD2, L2xD2, D2xC36, D2xR35, D2xU11, D2xRJ2, C32xT1, D11xT1. BOARD STATE: courtyard pairs 26 -> 34, nets 24 -> 24, violations 71 -> 71 (courtyard shapes carry no copper; no parts moved, no victims). Next: D2 cluster (move D2, the DNP alternate APD site), T1 pair (move C32, D11), then the original 26.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 24 · Courtyard collisions: 34 · Audit verdict: FAIL

### Pass 126 — 2026-11-06T01:09:05Z · commit `9a9a517`

Board: `hw/pdlvds_rx.exp120.kicad_pcb` · Commit: `9a9a5178144c2813f05a84d2e2e09b4cc94b6a6e`

COURTYARD CAMPAIGN item 1 (U6 cluster): C49 (89,-9)->(97.5,-12), R15 (89,1)->(97.5,-15.5), R16 (89.5,-2)->(97.5,-18), C19 (95,1)->(97.5,-9.5), C18 (94,-4)->(95.5,-4), U5 (68,-18.5)->(66,-20.5). Pairs closed (7): U6xC49, U6xR15, U6xR16, U6xC19, MH2xC19, U6xC18, U6xU5. New instrument hw/move_part.py: courtyard-clear offset + straight re-lay on the anchor's own layer + via-relay fallback, group-count guard per pad net. R15 (both pads) and C19 (NRST) reconnected by relay, counts unchanged; prune_dead run after the moves. VICTIMS NAMED AS OWED: +3V3A C49 leg (pad detached, relay refused at both tried sites; net was 1 group, now 2), BOOT0 R16 leg (1->2), and the U5 nudge split +3V3D, CDR_CLKN, CAP_CLK, CAP_DATA (each 1->2 in the repair model; DATP/DATN/CLKP held by relay) -- all repay in the resumed routing queue. VCAP2 unchanged (2 groups before and after; already a residue net). GND repair-model groups 52->56 (audit is zone-inclusive; its count governs). U6xMH2 still open: neither part may move (U6 load-bearing, MH2 a mounting hole) -- escalated to parent with the polygon data.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 112 · Unconnected nets: 30 · Courtyard collisions: 27 · Audit verdict: FAIL

### Pass 127 — 2026-11-06T01:14:00Z · commit `1a5ecb6`

Board: `hw/pdlvds_rx.exp121.kicad_pcb` · Commit: `1a5ecb63172159b0824785c7cda42821b5b75325`

COURTYARD CAMPAIGN item 2 (D2 + T1 clusters): D2 (18,60)->(28,60) closing all six pairs its newly drawn courtyard revealed (L1, L2, C36, R35, U11, RJ2); C32 (40.5,-17)->(40.5,-16.4) and D11 (21,-25)->(17,-29.5) closing C32xT1 and D11xT1 (D11 boxed by D9/D10 west, T1 east/south, Q1 north; nearest pocket SW, 10 segments re-laid clean). APD_K_ALT held by relay; C32 and D11 nets unchanged. VICTIM NAMED AS OWED: APD_A_ALT D2 leg (1->2 groups) -- repays in the resumed routing queue. prune_dead run after the moves. Remaining courtyard pairs: 19, of which U6xMH2 is the neither-may-move case escalated to the parent.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 118 · Unconnected nets: 31 · Courtyard collisions: 19 · Audit verdict: FAIL

### Pass 128 — 2026-11-06T01:20:55Z · commit `47140f1`

Board: `hw/pdlvds_rx.exp122.kicad_pcb` · Commit: `47140f12a33e38bae40befca7fcb38045b110a7e`

COURTYARD CAMPAIGN item 3 (U6xMH2, parent ruling: MH2 moves, U6 stays, no courtyard shrunk): landing zone probed first (x93-100, y6-14) -- occupants: R44 (courtyard reaching (94.48,7.73), inside MH2's new keep-out circle), D6/D7 clear (courtyards end x=91.48). R44 moved first, same item: (93,7)->(91.5,9.5), the pocket between D6, D7, X1 and MH2's new circle (its first target (97.5,5) sat inside MH2's CURRENT circle; the pocket was probe-verified clear of both MH2 positions). MH2 then moved north at constant x: (96.5,3.5)->(96.5,10.0) (corner column with MH4 kept); new courtyard (93.04,6.54)-(99.95,13.46), bottom clearing U6's courtyard top (5.65) by 0.89 mm. U6xMH2 CLOSED. Pair census: 19 -> 18. VICTIM NAMED AS OWED: LED_PWR_K R44 leg (1->2 groups) -- the pocket is sealed: straight F segments to all web targets blocked, heal refused (sealed pad), wide-grid via relay found zero legal via sites within 5 mm (hw/fix_r44.py is the refusal record); repays when D6/D7 move in the next item or in the routing queue. MH2 has no pads/nets; nothing else ripped. prune_dead run after the moves.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 122 · Unconnected nets: 32 · Courtyard collisions: 18 · Audit verdict: FAIL

### Pass 129 — 2026-11-06T01:27:31Z · commit `100debd`

Board: `hw/pdlvds_rx.exp123.kicad_pcb` · Commit: `100debd4a17f24967c61e7fe49285a5359caa0b3`

COURTYARD CAMPAIGN item 4 (X1 diodes, MH5, J3, F1, J5 clusters): D6 (90,7)->(92.5,6.5) and D7 (90,12)->(91.5,12), tight to X1 and clear of MH2's new circle; C33 (11.33,28)->(9.83,30) west-south out of MH5 (east was blocked); R11 (44.5,40)->(40,40) west out of J3; F1 (20,70)->(20.5,70) after C38's nudge (20.93,67.27)->(20.93,66.77) freed its east exit; R25 (8,-18.5)->(10,-18.5) east out of J5. Pairs closed (7): X1xD6, X1xD7, MH5xC33, R11xJ3, F1xD4, F1xC38, J5xR25. C38 and F1 nets unchanged. VICTIMS NAMED AS OWED: LED_PWR_K D6 leg (2->3 groups; the R44 leg from item 3 still owed), LED_STAT and LED_STAT_A D7 legs (1->2 each), TEST_IN R11 leg (1->2), HV_SHDN and +5V R25 legs (2->3 each; both already residue nets), C33 GND pad (repair model 56->57; audit is pour-inclusive and governs). prune_dead run after the moves. Remaining courtyard pairs: 11.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 156 · Unconnected nets: 36 · Courtyard collisions: 11 · Audit verdict: FAIL

### Pass 130 — 2026-11-06T01:45:03Z · commit `c528060`

Board: `hw/pdlvds_rx.exp141.kicad_pcb` · Commit: `c52806048ec4c98d5352e748c0565f21c2d94dcd`

COURTYARD CAMPAIGN COMPLETE: 0 courtyard collisions. Consolidated placement session (parent, single pair of hands, audit->render->look->move loop) from pass 127's board (exp121, 19 pairs): 20 moves over 19 parts closing every remaining pair -- R11 (44.5,40)->(42.25,40) out of J3; C41 ->(41.25,59.75) closing C41xFB2 + C41xR40; C5 ->(21.95,42.87) closing C1xC5; C17 ->(71.95,9.5) closing C16xC17; D8 ->(12.5,44) closing D8xU1; C38 ->(20.93,67.02) + D4 ->(13.27,72.25) closing F1xC38 + F1xD4; R25 ->(8,-19.25) closing J5xR25; C33 ->(12.58,28.5) closing MH5xC33 (polygon; bbox still touches the round hole courtyard, shapes do not intersect); R32 ->(30.5,-4.05) closing R32xR31; C37 ->(8.25,60) closing R36xC37; R42 ->(55.46,58.5) closing R41xR42; R50 ->(32.84,-7.15) closing R49xR50; R1 ->(19.5,35.75) closing U1xR1 (nudge only, stays tight to the TIA); D6 ->(91.25,8.5), D7 ->(91.25,12), R44 ->(91.25,14.5) as one column east of X1 closing X1xD6 + X1xD7 and clearing MH2's landing zone; R5 ->(16.25,50.5) closing U12xR5; MH2 ->(96.5,10.0) per the parent ruling closing U6xMH2. LINEAGE: this endpoint branches from pass 127 and SUPERSEDES the sibling item-3/4 positions in passes 128/129 for the shared clusters (MH2's endpoint is identical; R44/D6/D7/R11/C33/R25 differ); passes 128/129 remain the record of that line. VICTIMS OWED on this board, repay first in the resumed routing queue: TEST_IN (R11 leg), GND (C41 leg), +5V (R25 leg), LED_PWR_K (D6 leg and R44 leg), LED_STAT + LED_STAT_A (D7 legs). SH1 still has no drawn courtyard -- the one blind footprint, named until closed. Routing resumes from this board.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 156 · Unconnected nets: 36 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 131 — 2026-11-06T04:25:59Z · commit `8066156`

Board: `hw/pdlvds_rx.exp154.kicad_pcb` · Commit: `8066156fbf6e994f7ba41723232e9bbccb7c0ae7`

Post-courtyard routing resumes + dead-copper prune. From pass 130's board (exp141): prune pass, heal reconnected TEST_IN and LED_STAT (exp144); two placement attempts on the sealed LED pads (R44/D7 slid south, exp145/146) did NOT open them -- position alone is not the seal; heal still refuses R44.1/D7.1/D7.2. KiCad 8 DRC adopted as the standing checker (exp147 baseline: 706 violations / 50 unconnected items). Dead-copper campaign: the user's screenshots showed barbs that prune_dead's own redrawn-graph model had absorbed (raw census: 363 one-ended + 71 floating segments). Three deleter designs failed verification and were rejected uncommitted (centreline-tolerance model severed live joints, DRC unconnected 50->115; copper-overlap model 50->51; raw DRC-dangling deletion split pad groups 50->52, restored). Shipped instrument scratch/drc_graph_prune.py: KiCad proposes dangling items, a copper-contact graph vetoes segments that bridge two pad groups, KiCad referees after every round with abort-and-restore. Result (exp154): 150 dead segments removed over 31 rounds; track_dangling 84->25, via_dangling 7->0, violations 706->627, unconnected items 50 UNCHANGED throughout. Residue: 25 flagged dangling = 5 graph-vetoed bridges (live overshoot tracks, kept deliberately) + 19 matcher-skipped (matcher fix owed) + ~1. Failed boards exp148/149/151/152 remain in the working tree as evidence, uncommitted. Instruments saved in scratch/: dead_end_census.py, delete_dead.py, drc_prune.py, graph_prune.py, drc_graph_prune.py.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 144 · Unconnected nets: 35 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 132 — 2026-11-06T05:23:24Z · commit `97e9a1e`

Board: `hw/pdlvds_rx.exp157.kicad_pcb` · Commit: `97e9a1ecdfaf0afe4703d800208bac20bb747ab4`

Dead-copper residue prune with the matcher fixed. The pass-131 residue (25 DRC-dangling) is now attacked with the joint-disambiguation matcher in scratch/drc_graph_prune.py (far-end-free test + stacked-duplicate handling). Its first full batch removed 33 but KiCad unconnected rose 50 -> 51; a per-net bisect (scratch/bisect_prune.py) isolated the load-bearing deletion to ONE net: SWCLK, In2.Cu at (94.12,34.38) -- two different lattice segments share the flagged joint, both far ends anchor in the contact graph (one onto the long northbound SWCLK segment passing 0.11 mm away, one onto the next lattice segment), yet jointly they carry the net. Root cause: the matcher's fall-through treated any unresolved multi-candidate match as stacked duplicates and deleted ALL candidates. Fix: delete-all only for geometrically identical stacked copies; any other ambiguous joint is skipped, never guessed (regression: this run). Also added same-net zone-bbox anchoring to the far-end test. Result (exp157): 120 further dead segments removed over 31 rounds, KiCad DRC violations 627 -> 619, track_dangling 25 -> 17, via_dangling 0, unconnected items 50 UNCHANGED in every round. Residue 17 = graph-vetoed bridges (live overshoot tracks, incl. a 14 mm GND and the 4.375 mm HV_DAC run) + ambiguous hairline joints the matcher now refuses to guess (SWCLK (94.125,34.375) named; heals in the routing phase). Instruments updated: scratch/drc_graph_prune.py, scratch/bisect_prune.py.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 144 · Unconnected nets: 35 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 133 — 2026-11-06T05:29:17Z · commit `a81f8f0`

Board: `hw/pdlvds_rx.exp158.kicad_pcb` · Commit: `a81f8f0ec4563c9a34351e70baa5946cc45dc52d`

Keepout class closed by mechanism fix: 199 items_not_allowed -> 0. Provenance: all 28 rule areas on the board were created by hw/notch.py, hw/notch_strip.py, hw/fix_hvraw.py and hw/fix_r47.py, each setting only SetIsRuleArea(True) + SetDoNotAllowCopperPour(True) -- documented intent "copper-pour keepout only, tracks/vias/pads unaffected". A fresh ZONE in the KiCad 7-era pcbnew defaulted DoNotAllowTracks/Vias/Pads to True, the tools never cleared them, and the stored board banned tracks in every rule area (162 of the 199 were APD_K/APD_A tracks crossing the big front-end pour notch; the home-grown routers never modelled keepouts, so the copper accumulated silently). Fix (scratch/fix_keepout_flags.py): every rule area now allows tracks/vias/pads and keeps the pour ban -- the pour still stays out of the HV pocket exactly as designed; track-level HV isolation remains governed by clearance/net classes, untouched. KiCad DRC: violations 619 -> 420, items_not_allowed 199 -> 0, unconnected items 50 UNCHANGED, all other classes byte-identical counts. Regression test hw/tests/test_keepout_flags.py added in this pass: FAILS on exp157 (28 of 28 rule areas ban tracks), PASSES on exp158 (28 pour-only keepouts).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 144 · Unconnected nets: 35 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 134 — 2026-11-06T05:40:29Z · commit `dfe4ee1`

Board: `hw/pdlvds_rx.exp159.kicad_pcb` · Commit: `dfe4ee170b19b5d51920f049ed8275a089125bcb`

Shorts class attacked; verdict: it is live routes over foreign pads, not debris. A DRC-refereed deletion pass (scratch/drc_shorts_prune.py: KiCad proposes the track items of shorting_items, the contact graph vetoes own-net bridges, deletions applied per-net with DRC after each net and wholesale restore on any split) removed exactly 2 segments board-wide (CDR_DATP 1 + 1): KiCad DRC violations 420 -> 416, shorting_items 59 -> 57, unconnected 50 UNCHANGED. Everything else was vetoed as an own-net bridge or split on deletion (+3V3D batch splits +2, ULPI_NXT +1 -- both restored and hand-listed): the shorting tracks are overwhelmingly fanout-lattice escapes that cross foreign pads while carrying their own net, concentrated at U5 (29 of 59: +3V3D stubs over U5 GND/CDR_CLKP/CDR_CLKN pads, CDR_DATP over U5.+3V3D pad, I2C tracks/vias over CDR pads) and the ULPI_D4/D6 x XO lattice (9). Deletion is the wrong tool for the rest; the fix is a coordinated rip-and-relay of the U5 fanout field (same locality as the CAP_CLK/CAP_DATA/CDR unconnected groups), then the ULPI/XO lattice. Via shorts (5) were not auto-deleted by design (a via on a foreign pad can be its net's layer bridge) and are on the same hand list.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 142 · Unconnected nets: 35 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 135 — 2026-11-06T05:46:50Z · commit `617e1ea`

Board: `hw/pdlvds_rx.exp161.kicad_pcb` · Commit: `617e1ea713ffc8de6c0124114affa94c8202860c`

U5 fanout rip-and-relay, first locality proven: CDR_DATP. Ripped the 6 CDR_DATP segments intersecting the U5 west pad-field box (x 61.5..66, y -24.5..-20) -- the escape zigzag that crossed U5.+3V3D pad 4 three times and CAP_DATA -- then re-laid with heal_nets (KiCad 8 compat copies in scratch/heal8/: wx preambles stripped, run under xvfb; hw/ originals untouched). Heal reported 2 groups connected. KiCad DRC referee: violations 416 -> 411, shorting_items 57 -> 54 (zero CDR_DATP shorts remain), clearance 66 -> 65, unconnected items 50 UNCHANGED, no class regressed. The mechanism (rip the net's copper in the pad-field box, heal, DRC-verify) is now proven for the U5 locality; +3V3D's U5 distribution (16 GND-pad shorts + CLKP/CLKN) is the next and largest application.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 138 · Unconnected nets: 35 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 136 — 2026-11-06T05:52:35Z · commit `4590d4b`

Board: `hw/pdlvds_rx.exp163.kicad_pcb` · Commit: `4590d4bb3baae2c86c1a822387921ce41f6d940f`

U5 rip-and-relay, the big one: +3V3D. Ripped all 72 +3V3D segments intersecting the U5 pad-field box (x 61..71, y -26..-14) -- the heal-era distribution whose stubs lay across U5's GND/CDR_CLKP/CDR_CLKN pads -- and re-laid with heal_nets (scratch/heal8 KiCad 8 copies): 10 groups connected in 121 s. KiCad DRC referee, exp161 -> exp163: violations 411 -> 347, shorting_items 54 -> 34 (every U5 +3V3D short gone; the 6 remaining +3V3D shorts are the separate east-edge LED-column locality at D6/D7/R44), unconnected items 50 -> 48 (the rip forced the rail's genuinely split groups to re-merge), clearance 65 -> 45, solder_mask_bridge 72 -> 38. Cost: track_dangling 17 -> 22 (fresh heal stubs; the DRC/graph prune eats those next). No class but dangling regressed, and total violations fell by 64.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 112 · Unconnected nets: 34 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 137 — 2026-11-06T05:58:33Z · commit `25ee047`

Board: `hw/pdlvds_rx.exp164.kicad_pcb` · Commit: `25ee0470a85dcf0a3fd1d2231f40cd23fd1a5860`

Heal-stub prune after the U5 rip-and-relays. The +3V3D/CDR_DATP re-lays (passes 135-136) left fresh dangling stubs (track_dangling had risen 17 -> 22). Ran the DRC/graph prune (scratch/drc_graph_prune.py) on exp163: 23 dead segments removed over 9 rounds, every round refereed. KiCad DRC: violations 347 -> 338, track_dangling 22 -> 20, clearance 45 -> 44, shorting_items 34 UNCHANGED, unconnected items 48 UNCHANGED throughout. The 20 remaining dangling are the standing residue: graph-vetoed bridges (live overshoot tracks) + ambiguous hairline joints the matcher refuses to guess (SWCLK at (94.125,34.375) among them).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 112 · Unconnected nets: 34 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 138 — 2026-11-06T06:10:10Z · commit `0a9e214`

Board: `hw/pdlvds_rx.exp165.kicad_pcb` · Commit: `0a9e214298170b578f1715b359a6e39265b91378`

Shorts locality C: HV_EN x C4 GND (7 items). Ripped 14 HV_EN segments intersecting the C4 pad box (x 24..27.5, y 13.8..17.5) -- the B.Cu diagonal grazed the C4.2 PTH ring at its corner -- and re-laid with heal_nets (scratch/heal8): main 68-item group reconnected around the pad in 11 s. HV_EN's U6.97 pad group remains STILL isolated (pre-existing, residue-family queue; the rip box is nowhere near U6). KiCad DRC referee, exp164 -> exp165: violations 338 -> 320, shorting_items 34 -> 27 (zero HV_EN shorts remain), solder_mask_bridge 38 -> 31, unconnected items 48 UNCHANGED, clearance 44 unchanged, track_dangling 20 -> 21 (one fresh heal stub, prune food).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 105 · Unconnected nets: 34 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 139 — 2026-11-06T06:16:28Z · commit `1ba94ed`

Board: `hw/pdlvds_rx.exp166.kicad_pcb` · Commit: `1ba94ed1fcde11e82c2b33389d1eba50c34daed8`

Shorts locality A: east strip (X1/LED column/ULPI fanout), 16 items + LED victim repaid. Ripped in box (84.5,5)-(94.5,19): +3V3D 20 segs, ULPI_D4 17, ULPI_D6 25, LED_STAT 19 (LED_PWR_K/LED_STAT_A had zero segments -- never routed); deleted 2 stray vias in the LED field (LED_PWR_K at (89.875,8.125), LED_STAT at (89.125,13.625)). Heal (116 s): +3V3D reconnected both groups, re-laid on In2.Cu EAST of the D7/R44 column (was: F.Cu trunk through D7.2 and R44.2 pads); ULPI_D4/D6 reconnected around X1.2; LED_PWR_K CONNECTED D6.1->R44.1 down the west side of the column (victim repaid). LED_STAT D7.1 and LED_STAT_A D7.2 STILL isolated -- pads open but the strip is crossed by the CDR_CLKP/CLKN diagonals; next mechanism is a local rip of the pair + heal LEDs first. KiCad DRC referee, exp165 -> exp166: violations 320 -> 297, shorting_items 27 -> 11 (east strip zero), solder_mask_bridge 31 -> 17, clearance 44 -> 42, unconnected items 48 -> 47. Regressions noted: copper_edge_clearance 80 -> 85 (re-laid strip routes run nearer the east edge; that class is next in queue), track_dangling 21 -> 25 (fresh heal stubs).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 87 · Unconnected nets: 32 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 140 — 2026-11-06T06:27:46Z · commit `3d45a4e`

Board: `hw/pdlvds_rx.exp170.kicad_pcb` · Commit: `3d45a4e24eada7bf0dc5c2c13199e991a0da8baa`

CDR pair rip-and-relay through the east strip (sets up the D7 field), then heal-stub prune. Ripped CDR_CLKP 52 + CDR_CLKN 34 segments in box (88.5,10)-(94.5,19) from exp166 and re-laid with heal_nets: both nets fully reconnected (52 / 55+1 items), zero new shorts. Prune (scratch/drc_graph_prune.py) then removed 62 dead segments. KiCad DRC referee, exp166 -> exp170: violations 297 -> 294, unconnected items 47 -> 46, track_dangling 25 -> 20, shorting_items 11 unchanged, clearance 42 unchanged, solder_mask_bridge 17 unchanged. Carried regression: copper_edge_clearance 85 -> 88 (the pair's re-lay runs nearer the east edge; that class is next in queue). NOTE on the branch not taken: exp167/exp168 (uncommitted evidence) added LED_STAT's connection via the same field but its escape vias/stubs landed on X1.2 (XO) three times running (+4 shorts) and LED_STAT_A refused heal in 1 s even with a hand-laid fanout ray -- that whole branch cost more than it gained and was re-approached as this pair-only relay. LED_STAT_A's other endpoint is R45.2 at (86.33,22.0), not U6 (diagnosed from its item list); the LED nets go to the routing queue with that fact.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 87 · Unconnected nets: 31 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 141 — 2026-11-06T06:33:19Z · commit `3808685`

Board: `hw/pdlvds_rx.exp171.kicad_pcb` · Commit: `3808685177ecb2b992c03e7e2f5e28155a5c3d60`

Shorts locality B: U5 west pad field (5 items). Ripped in box (61.5,-24)-(66,-14.5): I2C_SCL 4 segs, I2C_SDA 13, CDR_CLKP 25, CDR_DATN 6; deleted 4 vias in the field (CDR_CLKP at (63.12,-18.88), (62.62,-18.12), (64.62,-16.12) -- the last was the one on U5.8 GND -- and CDR_DATN at (65.53,-22.95)). Heal (74 s): all four nets fully reconnected, 7 groups. The I2C vias DRC had paired with U5.6/U5.5 were resolved by the re-lay (their positions in the report were the pads'; the re-laid fanout now clears the column). KiCad DRC referee, exp170 -> exp171: violations 294 -> 283, shorting_items 11 -> 6 (U5 zero; remaining are five single localities), unconnected items 46 -> 45, clearance 42 -> 37, solder_mask_bridge 17 -> 12, copper_edge_clearance 88 unchanged, track_dangling 20 -> 23 (fresh heal stubs).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 77 · Unconnected nets: 31 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 142 — 2026-11-06T07:07:47Z · commit `1dad870`

Board: `hw/pdlvds_rx.exp172.kicad_pcb` · Commit: `1dad870609ad65574b0d373f52fd2519f01508c1`

Shorts singles cleared: shorting_items 6 -> 0 (class closed). Five micro-localities, each rip+heal with DRC checks between: ULPI_NXT x C17.1/VCAP1 (ripped 13 segs in (69.8,4)-(71.8,12.5); heal reconnected 4 groups -- NXT was more fragmented than it looked); CMP_IN x R11.1/TEST_IN (ripped 4 in (36.5,39.5)-(41.5,44.5); reconnected); HV_SHDN x R25.1/+5V (ripped 8 in (3.5,-22.5)-(10,-16.5); 3 groups reconnected; U6.42 group STILL isolated, pre-existing residue); +VA x D2.2/APD_K_ALT (ripped 10 in (22,58.5)-(27,64); reconnected 59+1 items); ILIM_P x C41.2/GND (cleared ILIM_P's 14 items in (41,58)-(44.5,61.5) including the via on C41.2; heal re-laid the 19-item group). KiCad DRC referee, exp171 -> exp172: violations 283 -> 278, shorting_items 6 -> 0, clearance 37 -> 34, solder_mask_bridge 12 -> 7, unconnected items 45 UNCHANGED, copper_edge_clearance 88 unchanged, track_dangling 23 -> 27 (fresh heal stubs, prune next).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 68 · Unconnected nets: 31 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 143 — 2026-11-06T07:15:38Z · commit `d28f43d`

Board: `hw/pdlvds_rx.exp173.kicad_pcb` · Commit: `d28f43d7c9c28c70990cf18ba54bd3f93e999eb8`

Heal-stub prune after the shorts campaign. Ran scratch/drc_graph_prune.py on exp172 (DRC proposes, contact graph vetoes bridges, DRC referees every round, unconnected invariant held at 45 in all 10 rounds run); stopped at the converged plateau (22 flagged residue = vetoed bridges + ambiguous hairline joints, the standing residue) and banked the last refereed state. KiCad DRC, exp172 -> exp173: violations 278 -> 268, track_dangling 27 -> 22, shorting_items 0, clearance 34, solder_mask_bridge 7, copper_edge_clearance 88 -- all unchanged; unconnected items 45 UNCHANGED.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 68 · Unconnected nets: 31 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 144 — 2026-11-06T07:20:58Z · commit `17f6d2f`

Board: `hw/pdlvds_rx.exp174.kicad_pcb` · Commit: `17f6d2fd3826b9955748566cdc0d1001cd5358b9`

Copper-edge campaign, part 1: the creepage slot (x12..46 / y23.6..25.1, docs/02 HV-island creepage feature). Diagnosis: the class was not tracks hugging edges -- several routes CROSS the slot outright (the heal-era router does respect the slot; the crossings were older copper) plus a fanout field inside its east tip. Ripped 5 nets in corridor (10,21)-(48,28) -- HV_EN 29, DAC_VREF 12, +5V 12, HV_DAC 17, APD_K 1 -- deleted 1 GND via inside the slot, healed all 5 (7 groups reconnected; APD_K test case first proved the re-lay keeps 0 segments within 0.5 mm of the slot). GND's 8 segments inside/near the slot deleted surgically (pour carries the net; referee confirms no split). Pre-existing victims untouched by the corridor remain: RJ2.2, U7.4 (+5V leg), U6.97. KiCad DRC referee, exp173 -> exp174: violations 268 -> 253, copper_edge_clearance 88 -> 68, unconnected items 45 UNCHANGED, shorting 0, clearance 34, mask 7 unchanged, track_dangling 22 -> 25 (fresh heal stubs). Edge residue: J1 NPTH field at the south edge (18), slot east-tip fanout (10), east-edge x=100 runs (8+), south GND runs (6).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 68 · Unconnected nets: 32 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 145 — 2026-11-06T08:22:38Z · commit `9c622fc`

Board: `hw/pdlvds_rx.exp175.kicad_pcb` · Commit: `9c622fca66b3e9fddbaa78990135f0f29e550274`

Heal-stub prune on exp174 with a bisection-proven exclusion. First prune attempt BROKE the invariant (round 0 removed 8, unconnected 45 -> 46, board restored uncommitted). Per-net bisection (scratch/bisect_prune.py) isolated the split to the GND batch; per-item bisection (scratch/bisect_items.py) proved the single culprit: Track [GND] on F.Cu, 1.75 mm at (44.375, 10.125) -- removing it alone splits a group (the contact graph cannot see its pour-side join). It is now on the tool's exclusion list (scratch/dgp-exclusions.json) and stays. Clean run: 31 stub segments removed over 10 rounds, unconnected items 45 UNCHANGED in every round. KiCad DRC referee, exp174 -> exp175: violations 253 -> 249, track+via dangling items 27 -> 23, copper_edge_clearance 68, clearance 34, shorting 0. Dangling residue: 4 graph-vetoed bridges + 18 matcher-ambiguous joints (skipped, never guessed) + the excluded GND track.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 68 · Unconnected nets: 32 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 146 — 2026-11-06T09:19:00Z · commit `a3a5b7a`

Board: `hw/pdlvds_rx.exp176.kicad_pcb` · Commit: `a3a5b7a31d32444611a9b015fa9f9606324d6546`

Copper-edge campaign, part 2: the creepage slot is now CLEAR of copper, and C26 was living in it. Diagnosis chain: DRC slot items read 'actual 0.0000 mm' -- tracks CROSS the slot (docs/02 HV-island creepage slot, x12..46 / y23.6..25.1), they do not hug it. The heal router ignores Edge.Cuts and re-lays crossings (proven on +5V: delete the 19 mm In2 crossing, heal, crossing census unchanged). New mechanism, proven on a +5V probe first: a sacrificial SLOTFENCE net fenced across the band on all 4 layers (scratch/fence_slot.py) forces heal detours around the slot ends; fence removed before the referee runs. Production: deleted 23 crossing segments (HV_EN 11, DAC_VREF 6, HV_DAC 3, +5V 1, CMP_QN 1, GND 1; scratch/delete_slot_crossings.py), fenced, healed all 5 nets (4 connected immediately; +5V U7.4 and HV_EN U6.97 remain the standing isolated pads). DAC_VREF's residue exposed the real defect: C26 was PLACED INSIDE THE SLOT (centre (43.5,24.0), pads over the cutout) with its fanout via also in the slot (43.125,24.125, deleted). C26 is U8's VREF bypass (DAC_VREF has exactly two pads: U8.10 and C26.1). First move target (46.8,30.8) landed in U8's +3V3D fanout (4 shorts, heal NO_EXIT -- rejected by DRC); second move to (49.5,23.5), east of the slot end and north of U8, courtyard-clean, healed in 1 s. A VM replacement ate the first heal run mid-flight; the stage was rebuilt from exp175 after a census showed the dead run's checkpoint had contaminated the work file. KiCad DRC referee, exp175 -> exp176: violations 249 -> 229, unconnected items 45 -> 44 (DAC_VREF whole again), copper_edge_clearance 68 -> 40 (slot band 35 -> 0 by the crossing census), shorting 0, clearance 34 -> 35 (one new item: CMP_QN detour vs THR_DAC via south of the slot -- named for the clearance campaign), dangling 23 -> 30 (fresh heal stubs, next prune). Edge residue: J1 NPTH field 18 (incl. footprint-intrinsic pad items), east-edge trunks 15.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 68 · Unconnected nets: 31 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 147 — 2026-11-06T09:30:47Z · commit `c12c810`

Board: `hw/pdlvds_rx.exp177.kicad_pcb` · Commit: `c12c810d0598c41c254e8324e14742d76b1d499d`

Heal-stub prune on exp176. 75 stub segments removed over 33 referee-clean rounds (unconnected items 44 in every round); round 33's single removal split a group (44 -> 45 at the next DRC) and the tool restored the last good board itself -- that segment, the last link of a long stub chain, is live copper the contact graph under-models, same family as the excluded GND track; it stays. KiCad DRC referee against the committed exp176 (229/44): violations 229 -> 217, dangling items 30 -> 25, copper_edge_clearance 40 -> 33 (several pruned stubs were also edge violators), clearance 35, shorting 0, unconnected 44 UNCHANGED. Residue unchanged in kind: 4 graph-vetoed bridges + 19 matcher-ambiguous fanout joints (skipped, never guessed) + the excluded GND track + the rolled-back chain link.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 68 · Unconnected nets: 31 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 148 — 2026-11-06T09:46:30Z · commit `bbb5dd6`

Board: `hw/pdlvds_rx.exp178.kicad_pcb` · Commit: `bbb5dd6f7feb79646a227933fdb7ac9fb2345904`

East edge cleared: the J2 CDR pair escape reworked. Diagnosis chain: the pair (J2.5/6 pads at x=98.08) escaped east into a shared channel at x=99.375 whose fanout topology forced the heal to re-lay it identically after every rip (three attempts); the sacrificial-fence mechanism proved lossy on this stack -- a no-op heal run drops fence tracks layer-specifically (In2 loses the out-of-outline column at save, F.Cu loses tracks through save_checkpoint) and routed runs rename survivors to GND (three 123 mm GND-named fence columns found by geometry census and deleted by exact geometry; committed exp177 verified phantom-free by the same census). Working recipe: DENSE fence (0.3 mm pitch, 28 tracks, x 98.9..100.7 full height), wide rip of both pair nets east of x=96.5 (46+28 segments), heal (CLKP took a real interior route: 28 s, 3 vias), fence removal by name AND geometry, then a zone refill (the heal checkpoint refills with the fence still on; without a post-removal refill the F.Cu GND pour keeps fence-shaped slots and reads +1 unconnected island). KiCad DRC referee against committed exp177 (217/44): violations 217 -> 209, copper_edge_clearance 33 -> 20 with ZERO items east of x=98 remaining (the +3V3D east trunk and the whole CDR_CLKP/CLKN east run are gone), clearance 35, shorting 0, unconnected 44 UNCHANGED after the refill. Remaining edge items are exactly the J1 south field (20, placement-decision class). New CLKN path passes close to SWCLK on In2 (one clearance item, named for the clearance campaign).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 68 · Unconnected nets: 31 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 149 — 2026-11-06T09:59:03Z · commit `fa5c56b`

Board: `hw/pdlvds_rx.exp179.kicad_pcb` · Commit: `fa5c56be261e09d3ecf641b78a1b2379b8a72cd1`

WHOLE-BOARD RE-PLACEMENT (user order 2026-11-06: placement itself was the defect). Force-directed placement over all 139 movable parts: connection springs (per-net pad star) + hard courtyard separation + simulated annealing with same-padcount swaps; anchored: mounting holes, edge connectors J1/J2, shield can SH1 with the APD/TIA under it, alt-APD D2, test header J3; HV creepage slot and board bounds hard constraints throughout. Clusters now sit on their connections: ADN2813 U4 and capture U5 beside J2 on the y=43 latitude; DAC U8 beside the processor; +3V3D regulator U11 moved from the NW corner to its east-side loads; SWD header J4 beside U6 (and U6's east-edge satellite column -- VCAP1/2, LEDs -- placed against its pads at x=95.75); interlock J5 in the processor-to-converter corridor at (48,-20). Locality census (scratch/locality.py, same method both boards), exp177 -> exp179: TOTAL pad star 6142 -> 3680 mm (-40%); +3V3D 1367 -> 615 (span 122.0 -> 58.4), +5V 818 -> 585, +3V3A 291 -> 162, APD_K 195 -> 105, +VA 141 -> 82, PG_3V3 141 -> 57, CDR_CLKP/DATP ~110 -> ~43 each; worst parts by mean partner distance: J2 53.2 -> 19.1, J5 46.7 -> 20.3, C9 41.1 -> 15.3, J4 38.6 -> below 13, U8 26.4 -> 14.9, U6 22.9 -> 13.9. Remaining far parts are geometric floors, named: D3 (USB PHY pair to U7, USB cluster kept), T1 (transformer pad spread), J5 (series midpoint between processor and converter), D8 (emitter at the detector). Courtyard: 0 gated pairs (full check_pcb audit); SH1 fallback pairs 21 (the standing blind spot; SH1 did not move). One FD casualty found by DRC and fixed before commit: C41 had drifted onto SH1's GND pad (SH1 has no drawn courtyard, so the placer could not see it) -- moved clear to (31,50.5). Copper: STRIPPED (0 tracks, 0 vias verified on the saved file) -- the re-placement orphaned effectively all routing; the board is re-routed from here as the main job. KiCad DRC on the bare board: 154 violations, all non-copper except 4 (J1 footprint-intrinsic edge items: NPTH vs own A12 pad, shield pads vs south edge) + 1 solder-mask bridge (C41 -VA pad vs GND pour); silk_overlap/silk_over_copper 148 (designator text collisions from the moves, tail class); shorting 0; unconnected 303 (every net, by construction). The exp177/178 line remains in git history; this board is the board now.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 15 · Unconnected nets: 120 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 150 — 2026-11-06T11:33:43Z · commit `04b5078`

Board: `hw/pdlvds_rx.exp180.kicad_pcb` · Commit: `04b507822882d7c63c65482672b053b5d1c78e60`

First re-route of the re-placed board (exp179, pass 149): three heal campaigns over the bare board (residue/stuck set first while the field was empty, then two full sweeps resumed across a VM restart from the 60-group checkpoint). 234 groups connected in total. KiCad DRC referee against the bare exp179 (154 violations / 303 unconnected): violations 167 (silk_overlap/silk_over_copper 148 -- the designator-text class the re-placement created, tail work; copper_edge_clearance 7; shorting_items 6, named below; CLEARANCE 0 and DANGLING 0 -- the heal lays are clean), unconnected 303 -> 82. Residue by net (DRC items): GND 56 (never healed -- the pour alone strands pads/islands; gets its own heal next), +VA 18 (the one total failure: every group exhausted the search cap; two clusters 12 mm apart around U13/front-end, mechanism to be diagnosed with the board rendered), TIA_OUT 8 (front-end enclosure: U1.6 and C5.1 each failed after ~146 s searches), +3V3A 4 (U7.6/U7.25 sealed pads), APD_A 4 (D1.2/4/6 sealed under the shield can), DP_CON 4 (J1.B6), I2C_SDA 4, +3V3D 2 (U11.14), +3V3D_CDR 2 (U4.12), APD_K 2 (D1.5), CAP_CLK 2 + CAP_DATA 2 (U5-U6 corridor), plus the sealed-pad set (U7 ULPI ring, U4.4/22/28, SWCLK, C23.1 PHY_1V8A). Next: hand-stub fanout for the sealed pads (hw/hand_stub.py exists for exactly this), GND heal, shorts prune, then the residue diagnoses. Placement dividend already visible: +5V, the ULPI bus's U6 side, both CDR pairs and the HV chain connected in seconds-to-minutes where the old placement ground for hours.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 76 · Unconnected nets: 40 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 151 — 2026-11-06T12:08:41Z · commit `3030246`

Board: `hw/pdlvds_rx.exp181.kicad_pcb` · Commit: `30302465aea7f7706223e922ee6139ef4d95fe78`

CDR_SQUELCH/X1.2 shorts closed by an obstacle-model fix. Root cause: the heal/router item model registered every pad with footprint rotation ADDED to the pad orientation, but KiCad 8 pad.GetOrientationDegrees() is already board-absolute -- non-square pads on 90/270-degree footprints were modelled with axes swapped (X1.2 modelled y[8.75,10.75], real y[7.5,12.0]), so heal laid the squelch web through the real pad corner and re-healing reproduced the short exactly. Model fixed in all four registration copies + regression test (tools commit 32c44dc, fail-old/pass-new). Board: ripped the 11 web segments clipping X1.2, re-healed CDR_SQUELCH with the corrected model; it detoured around the pad. KiCad DRC exp180 -> exp181: violations 167 -> 156, shorting_items 6 -> 0, solder_mask_bridge 5 -> 0, unconnected items 82 UNCHANGED, clearance 0, dangling 0. Remaining classes: silk 148, copper_edge 7, holes_co_located 1 (two co-located NEG_RAW vias).

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 70 · Unconnected nets: 40 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 152 — 2026-11-06T13:06:51Z · commit `668c325`

Board: `hw/pdlvds_rx.exp182.kicad_pcb` · Commit: `668c325961dcface297a30fe90df1b55276112a2`

pass 152: GND campaign on the re-placed board - pour stitching (vias tying 16 stranded pads + F islands to the inner GND plane), U10 pocket cluster track-tied south to T1.9, U8 island tied. KiCad DRC vs exp181: violations 156 -> 156, unconnected items 82 -> 59 (GND items 28 -> 5: C29.2 pad and 4 F islands remain)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 70 · Unconnected nets: 40 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 153 — 2026-11-06T13:30:42Z · commit `b9b75ce`

Board: `hw/pdlvds_rx.exp183.kicad_pcb` · Commit: `b9b75ceec71d2f0f2d3ac69df125306a73643ef8`

pass 153: +VA first links - grid-routed tree C44.1/C2.1/C7.1/U2.5 on F, U13.9-U13.10 same-net pin link (0.6 segment ending at 49.55 for exactly class clearance to U13.8 GND). KiCad DRC vs exp182: violations 156 -> 156, unconnected items 59 -> 55 (+VA items 9 -> 5; remaining +VA groups: U3.5, C10.1, U1.7, R5.1, U13 pair join)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 70 · Unconnected nets: 40 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 154 — 2026-11-06T13:42:46Z · commit `d0ec1b1`

Board: `hw/pdlvds_rx.exp184.kicad_pcb` · Commit: `d0ec1b1139cb17656ce46add3a9534842dcf2c40`

GND C29.2 unsealed: relayed the HV_R29M via 1.5 mm north (22.375,0.375 -> 22.375,1.875; F and B chain segments re-laid on the same vertical, DRC-neutral) to open the east corridor its 1.0 mm HV clearance shadow had closed by 0.01 mm, then grid-routed GND C29.2 -> R24.2 on F with pad-anchored ends. KiCad DRC vs exp183: violations 156 -> 156, unconnected items 55 -> 54 (GND items 5 -> 4; remaining GND is the four F-zone islands X2.2/C16.2/U6.51/U6.38). No clearance/shorting/dangling items.

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 70 · Unconnected nets: 39 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 155 — 2026-11-06T13:59:22Z · commit `8ea38d7`

Board: `hw/pdlvds_rx.exp185.kicad_pcb` · Commit: `8ea38d785db7ec1828b232bb671dc1794bc065c9`

pass 155: GND island X2.2 tied - 0.5/0.3 via at (72.55,25.6) in the fragment north lobe drops to the In1 GND zone (In2 +3V3D track at y=24.375 blocks the pad row; F exits sealed by the CDR_SQUELCH staircase and the +3V3D via at (74.625,24.375)). DRC: violations 156 -> 156 (class table unchanged), unconnected 54 -> 53, GND items 4 -> 3

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 70 · Unconnected nets: 39 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 156 — 2026-11-06T14:03:21Z · commit `dddffe4`

Board: `hw/pdlvds_rx.exp186.kicad_pcb` · Commit: `dddffe4822214208b19d5feccab56c8d5771fa41`

pass 156: GND island C16.2 tied - 0.5/0.3 via at (76.487,9.139) inside the fragment drops to the In1 GND zone (exhaustive 0.125-grid scan at the board-minimum via size found exactly one legal spot in the fragment). DRC: violations 156 -> 156 (class table unchanged), unconnected 53 -> 52, GND items 3 -> 2

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 70 · Unconnected nets: 39 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 157 — 2026-11-06T14:06:44Z · commit `f8430f8`

Board: `hw/pdlvds_rx.exp187.kicad_pcb` · Commit: `f8430f856d89e113d83aace0c2d48734c71174e6`

pass 157: GND island U6.51 tied - 0.5/0.3 via at (79.817,6.078) inside the fragment drops to the In1 GND zone (single legal spot in an exhaustive 0.125-grid scan at board-minimum via size). DRC: violations 156 -> 156 (class table unchanged), unconnected 52 -> 51, GND items 2 -> 1 (only the U6.38 sliver remains)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 70 · Unconnected nets: 39 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 158 — 2026-11-06T14:15:24Z · commit `d3711ff`

Board: `hw/pdlvds_rx.exp188.kicad_pcb` · Commit: `d3711ff00208ef659f2ac11f589a990ea2081b92`

pass 158: +VA U3.5-C10.1 joined by an In1 hop - 0.5/0.3 vias in the U3.5 pad (37.725,39.975) and C10.1 pad (37.375,35.75), In1 track routed east around the CMP_IN via pair (In2 is blocked by the CMP_IN vertical and the THR_FILT staircase; In1 carries no tracks in this district). DRC: violations 156 -> 156 (class table unchanged), unconnected 51 -> 50, +VA items 5 -> 4

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 39 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 159 — 2026-11-06T14:19:35Z · commit `6f6877c`

Board: `hw/pdlvds_rx.exp189.kicad_pcb` · Commit: `6f6877cf4bd30d7bbad2495326596a88772a1053`

pass 159: +VA hop group joined to the main tree - 0.5/0.3 via in C44.1 pad (30.825,40.05), In1 track west at y=40 from the U3.5 hop via (37.725,39.975), passing 0.425 clear of the CMP_IN and THR_FILT vias. DRC: violations 156 -> 156 (class table unchanged), unconnected 50 -> 49, +VA items 4 -> 3 (U13 pair, U1.7, R5.1 remain)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 39 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 160 — 2026-11-06T14:22:59Z · commit `3dab785`

Board: `hw/pdlvds_rx.exp190.kicad_pcb` · Commit: `3dab7852c4e6d0817fb3b8b6755a58cd1b13b34a`

pass 160: +VA U1.7 joined to the tree - 0.5/0.3 vias in U1.7 pad (18.5,39.365) and U2.5 pad (25.95,39.05), straight In1 track between (In1/In2 carry no tracks in the front-end district). DRC: violations 156 -> 156 (class table unchanged), unconnected 49 -> 48, +VA items 3 -> 2 (U13 pair and R5.1 remain)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 39 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 161 — 2026-11-06T14:25:47Z · commit `8990c3d`

Board: `hw/pdlvds_rx.exp191.kicad_pcb` · Commit: `8990c3d439ed5e31b6e46034f5f9a34da57ab493`

pass 161: +VA R5.1 joined - 0.5/0.3 via on R5.1 pad west edge (15.025,50.5) (APD_A 1.0 mm class pushes the legal spot to the pad edge), In1 track south to the U1.7 via (18.5,39.365). DRC: violations 156 -> 156 (class table unchanged), unconnected 48 -> 47, +VA items 2 -> 1 (only the U13 output pair remains)

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 39 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 162 — 2026-11-06T14:48:02Z · commit `6f32002`

Board: `hw/pdlvds_rx.exp192.kicad_pcb` · Commit: `6f32002e9e2dd7d4d18337345eee6b3cc85f0e74`

pass 162: +VA COMPLETE - U13 output pair joined: 0.5/0.3 via at (41.1,49.35) on the U13.10 pad/stub, In1 track south at x=41.1 then west at y=41.6 (clearing the GND/TEST_IN via pair) to the hop via (37.725,39.975). DRC: violations 156 -> 156 (class table unchanged), unconnected 47 -> 46, +VA items 1 -> 0

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 38 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 163 — 2026-11-06T14:51:15Z · commit `10b615f`

Board: `hw/pdlvds_rx.exp193.kicad_pcb` · Commit: `10b615f7ff63e95a40c47f77ea3ae0c52733f7d0`

pass 163: TIA_OUT U1.6-R1.1 routed on F (grid route, DRC-verified). DRC: violations 156 -> 156 (class table unchanged), unconnected 46 -> 45, TIA_OUT items 4 -> 3

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 38 · Courtyard collisions: 0 · Audit verdict: FAIL

### Pass 164 — 2026-11-06T14:54:45Z · commit `pending`

Board: `hw/pdlvds_rx.exp194.kicad_pcb` · Commit: `pending`

pass 164: TIA_OUT C1.1 joined - via-in-pad at C1.1 (18.52,43.25) and U1.6 (18.9,40.635), In1 track between; F is sealed by U1.5 pad and the APD_A/-VA weave, and KiCad DRC accepts the via (APD_A is not in the board's 1.0 mm netclass). DRC: violations 156 -> 156 (class table unchanged), unconnected 45 -> 44, TIA_OUT items 3 -> 2

Nets fully routed: not recorded · Pins failed: not recorded · Clearance violations: 71 · Unconnected nets: 38 · Courtyard collisions: 0 · Audit verdict: FAIL

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

