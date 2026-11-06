#!/usr/bin/env python3
"""Probe: track/via counts on a board.
Usage: xvfb-run -a python3 hw/track_count.py <board>"""
import sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
tracks = list(b.GetTracks())
vias = sum(1 for t in tracks if isinstance(t, pcbnew.PCB_VIA))
print("%s: tracks+arcs=%d vias=%d total=%d footprints=%d"
      % (sys.argv[1], len(tracks) - vias, vias, len(tracks),
         len(list(b.GetFootprints()))))
