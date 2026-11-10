# Recovered scripts — provenance archive (REDO, corrected scope)

## Phase A — the session set (this file is the Phase A deliverable)

The user's scope, binding: **just the scripts for this PCB project, written by the
subagents spawned to work on the PCB project.** Not the main chat agent, not this
chat's root agent, not cron/watchdog job sessions, not any other workstream's agents.

### Method

- Source: spawn records (`subagent.spawn` calls and their results) in the local session
  JSONL transcripts under `/home/hatch/agents/` — no muse.db (user order). Tooling:
  `scripts/scratch-recovery/enumerate_spawns.py` + `build_manifest.py`.
- A session is in the set iff its spawning brief tasks it with this project
  (photodiode LVDS receiver / lvds-receiver-official). The brief's first line is quoted
  for every session below as the evidence.
- Spawn calls are attributed to their true owner by call id (earliest record wins): child session files carry
  fork copies of ancestor transcripts (re-stamped at fork time), so a naive per-file
  scan finds 244 apparent 'grandchild' spawns that are really the root's own calls.
  Ownership-resolved, the only genuine second-generation spawns are the 3 workers the
  first build coordinator spawned on 2026-11-03. No third generation exists.
- The main-chat session (`ea3d13c7-e549-4198-bf09-87d40b70d51f`) was checked the same way: of its 421 spawns, **zero**
  task a child with this project (its Nov 1–9 spawns are cell/binary-exploration work).
  Every project spawn lives in this chat's root session lineage.
- Deliberately excluded: the root agent itself; the 4 recovery-lineage sessions
  (batch-1 miner and its successors, and this Phase A session) — listed in the
  exclusions note under the table; cron/watchdog job sessions (not in this lineage).

### Hard-stop checks

- Total sessions in set: **94** (limit 100 — OK).
- Earliest spawn: 2026-11-03T18:34:18.675769947+00:00 — nothing before 2026-11-03 (OK).
- Every session's spawn brief is on record in its parent transcript (OK).
- Sessions with no transcript file on disk: 0; with !=1 session file: 0.

### The set

| # | agent id | spawned (UTC) | parent | role | brief — first line |
|---|---|---|---|---|---|
| 1 | `211e6068-5645-443d-821c-d965a1288a6c` | 2026-11-03T18:34:18 | `4925d244…` | coordinator | You are the build coordinator for a PCB design project. Work in the existing git repo at ~/workspace/photodiode-lvds-rx (already initialized, first commit 073664b contains READM… |
| 2 | `6b643e67-3b72-4a34-a4e4-cb88906fc170` | 2026-11-03T18:35:40 | `211e6068…` | design worker (write-only slice) | Work in ~/workspace/photodiode-lvds-rx (git repo, do NOT git commit — the coordinator commits; do NOT rm anything). Write ONLY these files: sim/link_budget.py, results/link_budg… |
| 3 | `6ff926cd-6c17-4a41-8909-98b586b5f440` | 2026-11-03T18:35:40 | `211e6068…` | design worker (write-only slice) | Work in ~/workspace/photodiode-lvds-rx (git repo, do NOT git commit — coordinator commits; do NOT rm anything). Write ONLY: host/codec.py, host/test_codec.py, sim/digital_sim.py… |
| 4 | `04d878b8-e46d-47c3-a3e8-19842ed9ea6c` | 2026-11-03T18:35:40 | `211e6068…` | design worker (write-only slice) | Work in ~/workspace/photodiode-lvds-rx (git repo, do NOT git commit — coordinator commits; do NOT rm anything). Write ONLY under firmware/: firmware/codec/ (portable C codec lib… |
| 5 | `3c689d8e-9bcc-47b0-a096-4767120a160c` | 2026-11-03T21:58:48 | `4925d244…` | CI lane | You are the CI-fix worker for the photodiode LVDS receiver project. The user has explicitly ordered: fix the CI tests and the website deploy NOW so CI gives useful information. … |
| 6 | `263d02bd-2694-4be4-a34b-d020557c1979` | 2026-11-03T22:27:12 | `4925d244…` | CI lane | You are the CI-fix worker, round 3, for the photodiode LVDS receiver project. Work ONLY in ~/workspace/pdlvds-cifix on branch `ci-fix` (pull the latest ci-fix first — it now inc… |
| 7 | `00079813-c48a-433e-bd73-476dd6ede479` | 2026-11-03T22:39:09 | `4925d244…` | site/gallery rendering | You are the routing-history gallery worker for the photodiode LVDS receiver project. Work ONLY in ~/workspace/pdlvds-cifix on branch `routing-history` (already checked out, base… |
| 8 | `fbee6d75-6e0b-4c8a-a720-6ef52d21c0d2` | 2026-11-03T22:40:42 | `4925d244…` | CI lane | You are the CI-fix worker, round 4 (final ERC round), photodiode LVDS receiver project. Work ONLY in ~/workspace/pdlvds-cifix on branch `ci-fix` (rounds 1-3 are merged to main; … |
| 9 | `ff0c75ad-4e6c-4321-bfa3-a2ca61b971bc` | 2026-11-03T22:51:03 | `4925d244…` | site/gallery rendering | You are the routing-gallery rendering worker, round 2, photodiode LVDS receiver project. Work ONLY in ~/workspace/pdlvds-cifix on branch `routing-history`. Commit frequently. Do… |
| 10 | `7f6dd3c0-90bf-4b74-9767-641daf60ab88` | 2026-11-03T23:08:19 | `4925d244…` | CI lane | You are the CI performance worker for the photodiode LVDS receiver project. Work ONLY in ~/workspace/pdlvds-cifix; create a fresh branch `ci-speed` from the `ci-fix` tip (df0c69… |
| 11 | `e3e498fa-2d0f-4ea0-896f-06f51051aa22` | 2026-11-03T23:18:33 | `4925d244…` | site/gallery rendering | You are the routing-gallery rendering worker, round 3 (colour visibility), photodiode LVDS receiver project. Work ONLY in ~/workspace/pdlvds-cifix on branch `routing-history`. C… |
| 12 | `110e2372-a411-4917-9496-e2188176d9f6` | 2026-11-04T00:18:56 | `4925d244…` | coordinator | You are the successor build coordinator for the photodiode LVDS receiver PCB, taking over the routing lane in ~/workspace/photodiode-lvds-rx (branch main, local clone). Your pre… |
| 13 | `b3484ddd-409f-4eb0-bc21-c912679c6b5d` | 2026-11-04T00:52:32 | `4925d244…` | CI lane | You are the CI-signal worker for the photodiode LVDS receiver project. Work in ~/workspace/pdlvds-cifix on a FRESH branch `ci-signal` created from current origin/main (fetch fro… |
| 14 | `13c2bc99-3cf3-4499-a01f-dda273939356` | 2026-11-04T01:03:27 | `4925d244…` | CI lane | You are the CI-signal worker, round 2, photodiode LVDS receiver project. Work in ~/workspace/pdlvds-cifix on branch `ci-signal` (your round-1 branch; it has been merged to main,… |
| 15 | `b785e77a-5ae4-47b7-a4a9-61508885fa25` | 2026-11-04T01:12:23 | `4925d244…` | CI lane | You are the CI-signal worker, round 3 (small, surgical), photodiode LVDS receiver project. Work in ~/workspace/pdlvds-cifix on branch `ci-signal`. Commit; do NOT push; no token.… |
| 16 | `60e10a13-9832-4f5a-b861-c8112a74866b` | 2026-11-04T08:03:17 | `4925d244…` | CI lane | You are the token-metrics worker for the photodiode LVDS receiver project. Work in ~/workspace/pdlvds-cifix on a FRESH branch `token-metrics` from current origin/main. Commit fr… |
| 17 | `0088c73b-1d16-42f6-9f1a-5ba99e7c4865` | 2026-11-04T08:28:32 | `4925d244…` | metrics lane | You are the token-graph worker for the photodiode LVDS receiver project. Work in ~/workspace/pdlvds-cifix on a FRESH branch `token-graph` from current origin/main (63490c0, whic… |
| 18 | `333218be-904b-4e57-a6bd-d45857886107` | 2026-11-04T10:11:44 | `4925d244…` | site/pass-system | You are the pass-structure worker for the photodiode LVDS receiver project. Work in ~/workspace/pdlvds-cifix on a FRESH branch `pass-structure` from current origin/main (7abadef… |
| 19 | `11120dd2-6afc-4c3b-9c7f-7cf4627a92c4` | 2026-11-04T10:17:33 | `4925d244…` | metrics lane | You are the token-chart-v2 worker for the photodiode LVDS receiver project. The repo's main clone and cifix clone are busy with other agents — work in your OWN fresh clone: `git… |
| 20 | `d5bb5f18-a489-4487-afd5-2bce236e766e` | 2026-11-04T10:23:33 | `4925d244…` | site/schematic | You are the site-migration worker for the photodiode LVDS receiver project. Work in ~/workspace/pdlvds-cifix on a FRESH branch `site-jekyll` from current origin/main (26c569a or… |
| 21 | `ab55d171-69f0-459c-92c1-6ffebf77daf1` | 2026-11-04T10:26:09 | `4925d244…` | metrics lane | You are the input-split metrics worker for the photodiode LVDS receiver project. Work in your OWN fresh clone: `git clone https://github.com/sneakers-the-rat/lvds-receiver-offic… |
| 22 | `8369f89c-5558-4309-9a69-47a9e50ed1d4` | 2026-11-04T10:27:47 | `4925d244…` | metrics lane | You are the cost-summary worker for the photodiode LVDS receiver project. Work in your OWN fresh clone: `git clone https://github.com/sneakers-the-rat/lvds-receiver-official.git… |
| 23 | `5f78a807-40c8-493c-a22f-6725e6fb1773` | 2026-11-04T10:36:23 | `4925d244…` | metrics lane | You are the codename-pricing worker for the photodiode LVDS receiver metrics. Work in ~/workspace/pdlvds-cost (existing clone) on a FRESH branch `cost-codename` from current ori… |
| 24 | `ce118fef-acba-4105-aabf-c1338429fb5d` | 2026-11-04T10:41:20 | `4925d244…` | CI lane | You are the CI apt-cache worker (round 2) for the photodiode LVDS receiver project. Work in ~/workspace/pdlvds-cifix on a FRESH branch `ci-apt-cache` from current origin/main (f… |
| 25 | `1fe81d0d-1d0a-4955-8b0d-10edd7bed231` | 2026-11-04T10:50:39 | `4925d244…` | metrics lane | TASK: Correct the compaction rule in the input-split estimator of the photodiode LVDS receiver project and republish all dependent numbers. Repo: https://github.com/sneakers-the… |
| 26 | `b728b450-ad5f-4415-873c-4db2a154a76c` | 2026-11-04T10:57:17 | `4925d244…` | site/pass-system | TASK: Turn the board ("Routes") page renders of the photodiode LVDS receiver project site into a selectable gallery, and make the render SVGs carry their own dark background. Re… |
| 27 | `fa23dfda-f128-4850-be69-fd6d5e19076d` | 2026-11-04T11:01:55 | `4925d244…` | site/pass-system | TASK: Backfill the missing renders for layout passes 5, 8 and 9 of the photodiode LVDS receiver project, rendering from the board files AS OF each pass's own commit. Repo: https… |
| 28 | `e49a319b-6f75-432b-a279-f17e9917db5e` | 2026-11-04T11:06:26 | `4925d244…` | metrics lane | TASK: Rebuild the cost presentation (metrics README + site token page) of the photodiode LVDS receiver project into sane tables. Repo: https://github.com/sneakers-the-rat/lvds-r… |
| 29 | `9a93416b-f726-4fe6-9fa6-e55d045aea0e` | 2026-11-04T11:22:04 | `4925d244…` | site/pass-system | TASK: Fix the pass-page board views of the photodiode LVDS receiver project site (fake CSS-stack composite + every image 404ing) and make every composite on the site a real sing… |
| 30 | `cdfdba38-9acb-43bf-8460-cfbce6d542bc` | 2026-11-04T11:54:27 | `4925d244…` | firmware | TASK: Implement the USB device transport for the photodiode LVDS receiver's STM32H723 firmware — replace the stub with real, compile-verified code. Repo: https://github.com/snea… |
| 31 | `74a92a7e-43e9-45ad-a559-91d42365a624` | 2026-11-04T11:57:22 | `4925d244…` | project worker | TASK: Scrub the word "legacy" as a label for the Manchester mode across the photodiode LVDS receiver project, and restate the two link modes plainly. Repo: https://github.com/sn… |
| 32 | `361c335b-1d7f-4949-9828-b0d6157fda66` | 2026-11-04T11:57:22 | `4925d244…` | routing experiment (Freerouting) | TASK: Open two independent parallel paths at the routing blocker of the photodiode LVDS receiver project and deliver adoption-ready candidates. Repo: https://github.com/sneakers… |
| 33 | `d1f0d05a-a887-4772-989b-05b56480fb1d` | 2026-11-04T12:17:44 | `4925d244…` | coordinator | MISSION — PCB COMPLETION COORDINATOR: drive the photodiode LVDS receiver board to DONE tonight. You own the routing main line now. Deadline: the owner wakes in the morning (work… |
| 34 | `b86d6da7-368f-4d4c-bd21-a7b6566ae3ae` | 2026-11-04T12:21:45 | `4925d244…` | firmware | TASK — firmware fix: reconcile the DAC8562 threshold driver with the schematic (PA4 conflict). Small, bounded job; the USB transport worker surfaced this conflict and parked it;… |
| 35 | `9f0eb1e7-05b3-4048-82ea-76655f210c18` | 2026-11-04T12:29:26 | `4925d244…` | hardware-simulation attempts (refused) | MISSION — FULL DEVICE HARDWARE SIMULATION FROM THE ACTUAL DESIGN. The owner has specified this exactly and rejected the alternative in advance: NOT a script that re-implements w… |
| 36 | `5d363ec0-4316-4ce0-aeb9-37365a5af7c7` | 2026-11-04T12:30:50 | `4925d244…` | hardware-simulation attempts (refused) | MISSION — FULL DEVICE HARDWARE SIMULATION FROM THE ACTUAL DESIGN. The owner has specified this exactly and rejected the alternative in advance: NOT a script that re-implements w… |
| 37 | `4a3ec8f1-8ae5-4e9d-bf4a-5bffc9418201` | 2026-11-04T12:32:33 | `4925d244…` | hardware-simulation attempts (refused) | MISSION — FULL DEVICE HARDWARE SIMULATION FROM THE ACTUAL DESIGN. This is a benign scientific-research project (a photodiode optical-link receiver replacing an FPGA-based lab in… |
| 38 | `1602d923-1c3b-4f0b-8cb0-2553b7d099c7` | 2026-11-04T12:37:42 | `4925d244…` | firmware | TASK — firmware reconciliation #2: the HV-control and CDR-status pins. The DAC fix (just merged to main as d7e430f) surfaced that more of board.h was invented. You are reconcili… |
| 39 | `66b5a0e1-0ab1-4ef6-a817-92bce09b4d03` | 2026-11-04T21:58:05 | `4925d244…` | routing | SINGLE TASK: produce pass 65 — the board EXPANSION — for the photodiode LVDS receiver project. Nothing else. Read ~/workspace/custom-skills/local-verify-claims/SKILL.md first; e… |
| 40 | `2edb9d7e-5b3a-4fec-9eb7-377437572a1a` | 2026-11-04T22:46:55 | `4925d244…` | coordinator | You are the completion coordinator for the photodiode LVDS receiver PCB — routing phase on the EXPANDED board. Read ~/workspace/custom-skills/local-verify-claims/SKILL.md first;… |
| 41 | `98e426b0-540c-4eca-a7dd-67f646ed9bb7` | 2026-11-05T01:43:45 | `4925d244…` | coordinator | You are the successor completion coordinator for the photodiode LVDS receiver PCB, picking up mid-flight. Read ~/workspace/custom-skills/local-verify-claims/SKILL.md first; ever… |
| 42 | `b559fea1-e235-466a-a53e-69d4317cdde2` | 2026-11-05T03:43:08 | `4925d244…` | routing experiment (Freerouting) | SINGLE TASK: one whole-board Freerouting completion attempt on the EXPANDED photodiode-LVDS board, judged only by the project's audit. Read ~/workspace/custom-skills/local-verif… |
| 43 | `33778cb7-fbcd-4b8b-a090-0b43bb54f8c8` | 2026-11-05T04:51:46 | `4925d244…` | design audit/fix | SINGLE TASK: a parts lock-in audit for the photodiode LVDS receiver — every fitted part on the board verified and locked BEFORE further routing is trusted. Read ~/workspace/cust… |
| 44 | `b8f9dc88-c0ab-4ab4-b924-b731a676afee` | 2026-11-05T04:52:46 | `4925d244…` | coordinator | You are the completion coordinator for the photodiode LVDS receiver PCB, taking over a live lane. Read ~/workspace/custom-skills/local-verify-claims/SKILL.md first; every claim … |
| 45 | `d03706d0-0923-437b-b493-bfbe6552b535` | 2026-11-05T04:53:38 | `4925d244…` | design audit/fix | SINGLE TASK: fix the high-voltage self-fry defect in the photodiode LVDS receiver — bound the HV rail in HARDWARE so the fitted Excelitas C30737 (VBR max 260 V, docs/07) can nev… |
| 46 | `e5ec69fd-70b5-49cf-baf9-a85b819611d0` | 2026-11-05T05:14:00 | `4925d244…` | design audit/fix | SINGLE TASK: execute the parts fixes from the completed lock-in audit (docs/08-parts-lock.md, findings F-01…F-13) on the photodiode LVDS receiver. Read ~/workspace/custom-skills… |
| 47 | `4393dc69-a319-496f-987c-4c2d3f9d4c83` | 2026-11-05T06:07:42 | `4925d244…` | coordinator | You are the completion coordinator for the photodiode LVDS receiver PCB, taking over a live lane whose previous coordinator ended after pass 79. Read ~/workspace/custom-skills/l… |
| 48 | `ecabc602-1ab4-479b-8b34-3c2d2e4b4be5` | 2026-11-05T08:19:41 | `4925d244…` | board routing lane | You are the successor layout/routing worker for the photodiode LVDS receiver PCB. Your predecessor died mid-run (~23:36 PST) on a crashed routing run; the board work has been id… |
| 49 | `a7ed933a-108d-4f65-b0e0-b1265dd1e013` | 2026-11-05T10:46:47 | `4925d244…` | project worker | You are a parallel placement-prototype worker for the photodiode LVDS receiver PCB. Read ~/workspace/custom-skills/local-verify-claims/SKILL.md first and follow it — claims only… |
| 50 | `cbdad9c2-ec71-4781-b4b3-2a938630fd21` | 2026-11-05T15:25:39 | `4925d244…` | board routing lane | You are the successor layout/routing worker for the photodiode LVDS receiver PCB. Your predecessor ended after committing pass 107; the board is unfinished and the queue below i… |
| 51 | `0c197c75-0f58-423a-bb6a-63609b2472d5` | 2026-11-05T17:04:01 | `4925d244…` | board routing lane | You are the successor layout/routing worker for the photodiode LVDS receiver PCB. Your predecessor ended after committing pass 109; the board is unfinished and the queue below i… |
| 52 | `14c07024-a1a2-45e5-9528-06b5a68a623d` | 2026-11-05T20:33:14 | `4925d244…` | board routing lane | You are the successor layout/routing worker for the photodiode LVDS receiver PCB. One continuous task: keep working layout and routing until the audit reads 0 unconnected (viola… |
| 53 | `826fd10c-2967-4ec0-af33-8c054d8c4ef5` | 2026-11-05T20:49:14 | `4925d244…` | board routing lane | You are the successor layout/routing worker for the photodiode LVDS receiver PCB. One continuous task: keep working layout and routing until the audit reads 0 unconnected (viola… |
| 54 | `e563195a-672c-4190-afa6-b32eca2a9f4a` | 2026-11-05T21:32:00 | `4925d244…` | site/schematic | You are the site worker for the photodiode LVDS receiver project. The user finds the docs site unusable for following the board's evolution: the left menu lists ~115 pass pages … |
| 55 | `33b416d8-a46e-4355-8695-7030ad2883e2` | 2026-11-05T21:50:31 | `4925d244…` | project support | Make exactly ONE video: a slideshow of every pass's full-board TOP view render from the photodiode LVDS receiver repo, 1 second per board, low fps. Keep it simple — this is a fi… |
| 56 | `843addc6-05f8-43fb-876a-0305148a999f` | 2026-11-06T05:11:10 | `4925d244…` | project worker | WORK THE PCB BOARD — one continuous job, in ~/workspace/pdlvds-route (branch mwork9), repo https://github.com/sneakers-the-rat/lvds-receiver-official. |
| 57 | `ff1fdc7d-81cc-480f-82b4-fe819a8c9b35` | 2026-11-06T06:03:49 | `4925d244…` | board routing lane | CONTINUE THE PCB BOARD JOB — one continuous job, in ~/workspace/pdlvds-route (branch mwork9), repo https://github.com/sneakers-the-rat/lvds-receiver-official. You are picking up… |
| 58 | `11a7a32f-8259-47d1-b430-5deb54b7667d` | 2026-11-06T07:34:42 | `4925d244…` | board routing lane | CONTINUE THE PCB BOARD JOB — one continuous job, in ~/workspace/pdlvds-route (branch mwork9), repo https://github.com/sneakers-the-rat/lvds-receiver-official. You are picking up… |
| 59 | `8e23251f-636a-48aa-9ee3-72368d67abe0` | 2026-11-06T12:04:22 | `4925d244…` | board routing lane | CONTINUE THE PCB BOARD JOB — one continuous job, in ~/workspace/pdlvds-route (branch mwork9), repo https://github.com/sneakers-the-rat/lvds-receiver-official. You inherit a comp… |
| 60 | `b5451089-f5e9-4c9c-b889-4fd19d7fb870` | 2026-11-06T13:35:18 | `4925d244…` | board routing lane | CONTINUE THE PCB BOARD JOB — one continuous job, in ~/workspace/pdlvds-route (branch mwork9), repo https://github.com/sneakers-the-rat/lvds-receiver-official. You inherit the re… |
| 61 | `51d8882f-718d-4053-9278-f447bdadc103` | 2026-11-06T15:43:45 | `4925d244…` | board routing lane | CONTINUE THE PCB BOARD JOB — one continuous job, in ~/workspace/pdlvds-route (branch mwork9), repo https://github.com/sneakers-the-rat/lvds-receiver-official. You inherit the re… |
| 62 | `df91ac80-1261-4894-8404-5c0cbd177542` | 2026-11-06T18:46:43 | `4925d244…` | board routing lane | CONTINUE THE PCB BOARD JOB — one continuous job, in ~/workspace/pdlvds-route (branch mwork9), repo https://github.com/sneakers-the-rat/lvds-receiver-official. |
| 63 | `0c2b9721-8189-4962-b187-259bd980dcb9` | 2026-11-06T19:32:57 | `4925d244…` | board routing lane | CONTINUE THE PCB BOARD JOB — one continuous job, in ~/workspace/pdlvds-route (branch mwork9), repo https://github.com/sneakers-the-rat/lvds-receiver-official. |
| 64 | `1c6c250c-feaa-471f-b965-1afba833fc82` | 2026-11-06T20:14:53 | `4925d244…` | board routing lane | CONTINUE THE PCB BOARD JOB — one continuous job, in ~/workspace/pdlvds-route (branch mwork9), repo https://github.com/sneakers-the-rat/lvds-receiver-official. |
| 65 | `dc1a84f4-c133-4354-b90e-8f3b1e076da9` | 2026-11-06T22:48:30 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 66 | `fad5d62b-4b95-4dde-abe6-540270c80f5a` | 2026-11-07T00:09:41 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 67 | `c7337aba-6bd8-49c2-8e71-7a9f65978108` | 2026-11-07T02:06:51 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 68 | `bf963864-0546-437d-be90-a3a4209149d8` | 2026-11-07T04:10:17 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 69 | `0aefa113-7cea-49a8-abc3-d4a3c33d136f` | 2026-11-07T06:15:48 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 70 | `a38ebf44-2db7-4994-aa64-fa795ebfd70f` | 2026-11-07T08:15:47 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 71 | `433c61f0-924e-4394-8d19-0dc374edf7f7` | 2026-11-07T12:14:25 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 72 | `6d629b50-5801-4e11-bc8e-5f3ae7b3d3fd` | 2026-11-07T23:22:49 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 73 | `20867681-db2a-497e-a850-4f9b621cc53f` | 2026-11-08T01:22:50 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 74 | `0ba936c0-535c-4ce0-b7af-c35ea829bf3e` | 2026-11-08T03:30:34 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 75 | `48c8fb90-d2c7-4e52-b0f3-75688404e410` | 2026-11-08T05:28:56 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 76 | `9057a69f-713b-4e1b-adce-33cf932ce3b4` | 2026-11-08T07:29:17 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 77 | `2428f6c1-e756-464d-bbe4-99829283ed07` | 2026-11-08T09:19:10 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 78 | `7da12727-8bdc-4527-89e9-e197d2af5c33` | 2026-11-08T09:55:55 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 79 | `c89ee133-e946-4997-94d5-0a0c733a37d0` | 2026-11-08T13:06:40 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 80 | `04d7c2a1-57e1-4084-acc4-ec4d10b3b8b7` | 2026-11-08T18:11:36 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 81 | `5bf19a85-98b1-4b0a-a6ff-7a9dea0cf43b` | 2026-11-08T18:43:39 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 82 | `093c11ed-829d-4490-b4f7-c8b2bcdee5e4` | 2026-11-08T21:02:12 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 83 | `ae719c55-5551-4cd1-9902-f1e0fb01ca79` | 2026-11-08T22:30:29 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 84 | `0b552a13-666c-4e8f-a630-e19975f39cf7` | 2026-11-08T22:50:57 | `4925d244…` | site/schematic | TASK: Fix the project website build so the current-information pages always render the CURRENT board and sources automatically at site-build time. Repo: lvds-receiver-official. … |
| 85 | `57853226-0f3b-4f6a-8160-2c7aa03ccb2d` | 2026-11-08T22:50:57 | `4925d244…` | site/schematic | TASK: Make the generated KiCad schematic human-readable — subsystem layout with drawn wires — WITHOUT changing its logical structure by a single pin. Repo: lvds-receiver-officia… |
| 86 | `9e085623-5279-434f-b654-cb54adecd12b` | 2026-11-09T04:24:39 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 87 | `ad8257c0-736d-4b1c-89f1-65f5afcb5d79` | 2026-11-09T06:45:35 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 88 | `99fd7bda-c81e-46f8-9b70-9dfc260f5a79` | 2026-11-09T11:09:19 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 89 | `87b04502-827e-4c83-a62e-a28bbc933270` | 2026-11-09T21:47:22 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 90 | `74b6af9e-3749-4904-b700-dd7195ad394b` | 2026-11-09T23:50:50 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 91 | `bf0b8727-d72c-4188-ba24-e29fc094d2f7` | 2026-11-10T02:03:35 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 92 | `7fab2300-5df8-4b5f-97fa-ab7cd9d0072d` | 2026-11-10T04:41:32 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 93 | `473f9bbe-a334-4aff-9125-432a058e60e6` | 2026-11-10T05:59:29 | `4925d244…` | board routing lane | Continue the PCB board job — ONE continuous whole-board routing job on the lvds-receiver-official repo. You inherit the full conversation context including the compaction summar… |
| 94 | `5a4dfda8-244e-41b4-b816-43ece9e2596f` | 2026-11-10T06:41:35 | `4925d244…` | project worker | CONTINUATION of the LVDS receiver PCB routing job (repo https://github.com/sneakers-the-rat/lvds-receiver-official, work clone ~/workspace/pdlvds-route on branch mwork9, merge v… |

Excluded recovery-lineage sessions (spawned from the same root, briefs on record,
out of scope by the user's rule — the recovery is not board work):

- `bb32a622-8412-44aa-a9b2-a9965c712632` — recovery job, batch 1 (the purged sweep)
- `f2d79bf0-408a-43ad-8f8a-bb5db6ada733` — recovery job, successor 1 (died with no output)
- `a0ed68c3-adae-4ce8-a0c1-9fc51369d482` — recovery job, successor 2 (closed at purge)
- `93f6273c-a2bd-4261-8556-e544983cd8f5` — recovery redo, Phase A (this enumeration)

### Coverage notes and discrepancies

- metrics/agents.csv cross-check: 84 of 94 set sessions appear in the
  repo's project-scope metrics list; the absentees are named here because the metrics
  export is a stale snapshot (its refresh has been skipped repeatedly; newest usage row
  2026-11-09T14:55Z) — the spawn records, not the metrics export, are the census:
  - `ff1fdc7d-81cc-480f-82b4-fe819a8c9b35`
  - `2428f6c1-e756-464d-bbe4-99829283ed07`
  - `04d7c2a1-57e1-4084-acc4-ec4d10b3b8b7`
  - `99fd7bda-c81e-46f8-9b70-9dfc260f5a79`
  - `87b04502-827e-4c83-a62e-a28bbc933270`
  - `74b6af9e-3749-4904-b700-dd7195ad394b`
  - `bf0b8727-d72c-4188-ba24-e29fc094d2f7`
  - `7fab2300-5df8-4b5f-97fa-ab7cd9d0072d`
  - `473f9bbe-a334-4aff-9125-432a058e60e6`
  - `5a4dfda8-244e-41b4-b816-43ece9e2596f`
- Lane directories in the repo at scratch/work/: ae, ah, ai, aj, ak, al, am, an, ao, ap, aq, ar, as, at, au, av, aw, ax, ay, az, ba, bb, bc (23 lanes). All sit
  inside the era of the board-routing sessions in this set; per-lane session attribution
  is a Phase B extraction check. (Lane `bd` has no directory yet — its session is in the
  set; its work is still landing. `parent-shots` is the root agent's own directory and is
  correctly out of scope.)
- Phase B (extraction of these sessions' scripts into this directory) starts only after
  the parent approves this set.

