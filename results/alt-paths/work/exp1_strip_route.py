#!/usr/bin/env python3
"""Experiment 1: strip ALL tracks/vias (+ zone fills stay) from the
pass-10 board, leaving pure placement. Reports item counts only."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
nt = len(b.GetTracks())
nz = len(b.Zones())
nf = len(b.GetFootprints())
print(f"before: tracks+vias={nt} zones={nz} footprints={nf}")
b.BuildListOfNets()
# remove tracks/vias
for t in list(b.GetTracks()):
    b.Remove(t)
b.BuildListOfNets()
print(f"after: tracks+vias={len(b.GetTracks())} zones={len(b.Zones())} footprints={len(b.GetFootprints())}")
b.Save(dst)
print("saved", dst)
