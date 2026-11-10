#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
cd $R
export DISPLAY=:99
L=$R/results/commit-backlog.log
echo "=== backlog start $(date -u +%H:%M:%S) ===" >> $L
cp() {
  python3 scripts/commit_pass.py --board "$1" "$2" >> $L 2>&1
  grep -E 'committed [0-9a-f]+: pass' $L | tail -1
}
cp hw/pdlvds_rx.fr22.kicad_pcb "stub campaign 1 (hw/hand_stub.py): 13 of 31 singleton pads given audit-exact edge-anchored escape stubs, incl. D1.6 west, RJ2.2, CDR_DATP U4.29, CDR_NIN U4.4, CF1/CF2, GND R28.2, PHY_1V8A C23.1"
cp hw/pdlvds_rx.fr24.kicad_pcb "cluster clearing U4 disc (52,52) r4.2 on the stubbed board: 7/9 targets connected through the cleared field (CDR ring pads, +3V3D_CDR U4.24 among them)"
cp hw/pdlvds_rx.fr25.kicad_pcb "cluster clearing U7 disc (30,61) r4.5: 5/7 targets connected incl. +3V3A U7.16/U7.25; ULPI_NXT U7.11 and ULPI_STP U7.13 remain sealed by their own row geometry"
cp hw/pdlvds_rx.fr26.kicad_pcb "cluster clearing U10 disc (16,10) r3.6: 1/2 HV targets connected"
cp hw/pdlvds_rx.fr27.kicad_pcb "cluster clearing U6 west disc (83,44) r3.5: USB_RST U6.40 not connected by astar even in the cleared field (fanout-model seal)"
cp hw/pdlvds_rx.fr28.kicad_pcb "cluster clearing U13 disc (48,62) r3.6: ILIM_P U13.5 connected"
cp hw/pdlvds_rx.fr29.kicad_pcb "repairg healing after cluster chain 2: 68 groups connected (victims repaid in the cleared fields), sweep 2 connected 0; 37 unconnected nets, 85 groups, clearance 3"
cp hw/pdlvds_rx.fr30.kicad_pcb "stub campaign 2 on the healed field: +3V3A U7.30/U7.31 stubbed; CF1/CF2 re-stubbed (their campaign-1 stubs were ripped as cluster victims)"
cp hw/pdlvds_rx.fr31.kicad_pcb "small-disc clear (31.5,63.4) r2.4 with immediate audit-exact stubs: ULPI_STP, ULPI_DIR, ULPI_CK stubbed; ULPI_NXT U7.11 still sealed"
cp hw/pdlvds_rx.fr32.kicad_pcb "small-disc clear (30,58.5) r2.6 with immediate stubs: PHY_1V8A U7.29 stubbed; +3V3A U7.6 still sealed"
cp hw/pdlvds_rx.fr33.kicad_pcb "small-disc clear (84.5,43.5) r2.5 with immediate stubs: ULPI_D6 U6.74 stubbed; USB_RST U6.40 still sealed"
cp hw/pdlvds_rx.fr34.kicad_pcb "small-disc clear (16,10) r3.0: HV_INTVCC U10.8 / HV_SS U10.3 stubs still refused by the stub search's openness test"
cp hw/pdlvds_rx.fr35.kicad_pcb "small-disc clear (52.5,54) r2.6 with immediate stub: REFCLKN U4.11 stubbed; THRADJ U4.9 still sealed"
cp hw/pdlvds_rx.fr37.kicad_pcb "surgery2 (hw/surgery2.py — probe 16 directions, rip the cheapest rippable blockers, place a 0.2 mm neck): +3V3A U7.6 stubbed (1 DP_PHY via ripped), USB_RST U6.40, HV_INTVCC U10.8, HV_SS U10.3 stubbed (their necks were clean all along; the stub search's endpoint-openness test had been the blocker)"
cp hw/pdlvds_rx.fr38.kicad_pcb "surgery2 with pad-aware blocker pricing (pads cost 10, tracks/vias 1): ULPI_NXT U7.11 stubbed south (3 ULPI_STP items ripped), THRADJ U4.9 stubbed (2 GND tracks ripped) — every formerly singleton pad on the board now has copper"
cp hw/pdlvds_rx.fr39.kicad_pcb "repairg healing on the surgery board: 40 groups connected, sweep 2 connected 0; 39 unconnected nets, 87 groups, clearance 3"
cp hw/pdlvds_rx.fr40.kicad_pcb "ripup 'all' batch 1 on the healed board: 3 groups connected through ripped fences (victims queued for the next heal)"
cp hw/pdlvds_rx.fr41.kicad_pcb "ripup 'all' batch 2: 1 group connected"
cp hw/pdlvds_rx.fr42.kicad_pcb "repairg healing: 17 groups connected (ripup victims repaid; APD_K's three groups merged); 39 unconnected nets, 83 groups, clearance 3"
cp hw/pdlvds_rx.fr43.kicad_pcb "hand bridges (hw/bridge.py): VBUS_RAW, ULPI_D0 and +5V group pairs bridged across 1.0-1.45 mm gaps, one fence item ripped each"
cp hw/pdlvds_rx.fr44.kicad_pcb "hand segment joins the floating fanout chain west of D1 to APD_A's main group (the chain proved to be main-group copper; D1.6's pad itself still lone)"
cp hw/pdlvds_rx.fr45.kicad_pcb "D1.6 link segment from the pad's NW corner to its fanout chain: APD_A fully connected (36 unconnected nets). The segment passes D1.5 at ~0.96 mm — the 4th item of the justified D1 package-geometry graze family (the APD's own terminals are 0.5 mm apart; the 1.0 mm board rule cannot be met inside the footprint)"
echo "=== backlog done $(date -u +%H:%M:%S) ===" >> $L
