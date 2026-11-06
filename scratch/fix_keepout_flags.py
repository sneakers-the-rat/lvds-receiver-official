#!/usr/bin/env python3
"""Restore the rule areas' documented intent: copper-pour keepout ONLY.

Every rule area on this board was created by hw/notch.py,
hw/notch_strip.py, hw/fix_hvraw.py or hw/fix_r47.py, and every one of
those tools sets exactly two flags: SetIsRuleArea(True) and
SetDoNotAllowCopperPour(True) -- "copper-pour keepout only, tracks/
vias/pads unaffected" (hw/notch.py). But a freshly constructed ZONE
in the KiCad 7-era pcbnew defaulted DoNotAllowTracks/Vias/Pads to
True, the tools never cleared them, and the stored board therefore
bans tracks in all 28 rule areas. The home-grown routers never
modelled keepouts, so heal-era routing crossed them freely and
KiCad 8's DRC reports 199 items_not_allowed, 162 of them APD_K/APD_A
tracks inside the big front-end pour notch.

Fix: for every rule-area zone, allow tracks/vias/pads, keep the pour
ban. Track-level HV isolation is a clearance/net-class matter and is
untouched; the pour stays out of the HV pocket exactly as intended.

Usage: python3 scratch/fix_keepout_flags.py IN OUT
"""
import sys
import pcbnew

src, dst = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
n = 0
for z in board.Zones():
    if z.GetIsRuleArea():
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowCopperPour(True)
        n += 1
print(f'rule areas corrected: {n}')
board.Save(dst)
print(f'saved {dst}')
