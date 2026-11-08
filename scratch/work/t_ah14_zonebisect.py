#!/usr/bin/env python3
"""t_ah14_zonebisect.py -- for each candidate group of new F copper,
remove it from h8, refill, save a trial board. DRC then counts GND
zone pairs per trial to find which group severed a fill neck."""
import sys
import wx
_app = wx.App(False)
import pcbnew

F, B = pcbnew.F_Cu, pcbnew.B_Cu

def mm(v):
    return round(v / 1e6, 4)

def close(p, q):
    return abs(p[0] - q[0]) <= 0.002 and abs(p[1] - q[1]) <= 0.002

GROUPS = {
    'xoF': ('XO', [(F, (72.625, 12.25), (72.625, 10.375)),
                   (F, (72.625, 10.375), (72.375, 10.0)),
                   (F, (76.75, 11.125), (76.5, 10.75)),
                   (F, (76.5, 10.75), (76.0, 10.625))],
            [(72.625, 12.25), (76.0, 10.625)]),
    'p3F': ('+3V3A', [(F, (74.875, 11.125), (75.125, 11.125)),
                      (F, (75.125, 11.125), (74.25, 10.625)),
                      (F, (78.625, 16.75), (77.875, 16.75))],
            [(78.625, 16.75)]),
    'sclF': ('I2C_SCL', [(F, (67.5, 1.625), (67.375, 2.0)),
                         (F, (67.875, 1.625), (67.5, 1.625)),
                         (F, (69.375, 1.375), (67.875, 1.625))],
             []),
}

only = sys.argv[1] if len(sys.argv) > 1 else None
for gname, (net, segs, vias) in GROUPS.items():
    if only and gname != only:
        continue
    b = pcbnew.LoadBoard('scratch/work/ah/h8.kicad_pcb')
    n = 0
    for t in list(b.GetTracks()):
        if t.GetNetname() != net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = (mm(t.GetPosition().x), mm(t.GetPosition().y))
            if any(close(p, v) for v in vias):
                b.Remove(t); n += 1
        else:
            p = (mm(t.GetStart().x), mm(t.GetStart().y))
            q = (mm(t.GetEnd().x), mm(t.GetEnd().y))
            for lay, a, c in segs:
                if t.GetLayer() == lay and ((close(p, a) and close(q, c))
                                            or (close(p, c) and close(q, a))):
                    b.Remove(t); n += 1
                    break
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    out = f'scratch/work/ah/zb-{gname}.kicad_pcb'
    b.Save(out)
    print(gname, 'removed', n, '->', out)
