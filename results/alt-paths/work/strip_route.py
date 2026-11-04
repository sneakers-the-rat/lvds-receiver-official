#!/usr/bin/env python3
"""Strip all tracks/vias from a board copy (placement-only). One
process, one board — KiCad 7.0.11 SWIG corrupts repeated LoadBoard."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
nt = b.GetNumTracks() if hasattr(b, 'GetNumTracks') else None
tracks = b.Tracks()
n_all = 0; n_trk = 0; n_via = 0
for t in list(tracks):
    n_all += 1
    if isinstance(t, pcbnew.PCB_VIA): n_via += 1
    else: n_trk += 1
print(f"tracks={n_trk} vias={n_via} zones={b.GetNumZones() if hasattr(b,'GetNumZones') else len(b.Zones())} footprints={len(b.GetFootprints())}")
for t in list(b.Tracks()):
    b.Delete(t)
b.BuildListOfNets()
print(f"after delete: tracks iterable={len(list(b.Tracks()))}")
b.Save(dst)
print("saved", dst)
