#!/usr/bin/env python3
"""t_ah2b_rip2.py -- district rip v2 for the U7 south-west joint re-fanout.

From exp218: remove, by exact endpoint match,
  - ULPI_CK  In2 vertical (74.625,13.5)->(74.625,6.375)
  - +3V3A    In2 (75.625,11.375)->(75.625,10.125), (75.625,10.125)->(75.625,8.625)
  - +3V3A    F feed chain of U7.30/U7.31 down to (74.375,10.625)
             (keeps via (73.625,10.625) and seg (74.375,10.625)->(73.625,10.625))
  - I2C_SCL  B staircase stretch (72.875,11.625)->...->(76.875,9.625)
             (SCL's B web is a loop via (78.125,8.375); group census after
             the rip decides whether a rejoin job is needed at all)
Netcodes captured BEFORE any Remove (GetNetcodeFromNetname breaks after).
Output: scratch/work/ah/rip2.kicad_pcb. Asserts every listed item was found
exactly once.
"""
import wx
_app = wx.App(False)
import pcbnew

SRC = "hw/pdlvds_rx.exp218.kicad_pcb"
OUT = "scratch/work/ah/rip2.kicad_pcb"
F, IN2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu

RIP = [
    ("ULPI_CK", IN2, (74.625, 13.500), (74.625, 6.375)),
    ("+3V3A", IN2, (75.625, 11.375), (75.625, 10.125)),
    ("+3V3A", IN2, (75.625, 10.125), (75.625, 8.625)),
    ("+3V3A", F, (75.250, 11.562), (75.250, 11.312)),
    ("+3V3A", F, (75.250, 11.312), (74.875, 11.125)),
    ("+3V3A", F, (74.750, 11.562), (74.750, 11.312)),
    ("+3V3A", F, (74.750, 11.312), (74.875, 11.125)),
    ("+3V3A", F, (74.875, 11.125), (74.625, 10.875)),
    ("+3V3A", F, (74.625, 10.875), (74.375, 10.625)),
    ("I2C_SCL", B, (72.875, 11.625), (73.125, 11.875)),
    ("I2C_SCL", B, (73.125, 11.875), (73.375, 12.125)),
    ("I2C_SCL", B, (73.375, 12.125), (73.625, 12.375)),
    ("I2C_SCL", B, (73.625, 12.375), (74.125, 12.375)),
    ("I2C_SCL", B, (74.125, 12.375), (74.375, 12.125)),
    ("I2C_SCL", B, (74.375, 12.125), (74.625, 11.875)),
    ("I2C_SCL", B, (74.625, 11.875), (74.875, 11.625)),
    ("I2C_SCL", B, (74.875, 11.625), (75.125, 11.375)),
    ("I2C_SCL", B, (75.125, 11.375), (75.375, 11.125)),
    ("I2C_SCL", B, (75.375, 11.125), (75.625, 10.875)),
    ("I2C_SCL", B, (75.625, 10.875), (75.875, 10.625)),
    ("I2C_SCL", B, (75.875, 10.625), (76.125, 10.375)),
    ("I2C_SCL", B, (76.125, 10.375), (76.375, 10.125)),
    ("I2C_SCL", B, (76.375, 10.125), (76.625, 9.875)),
    ("I2C_SCL", B, (76.625, 9.875), (76.875, 9.625)),
]

b = pcbnew.LoadBoard(SRC)
codes = {}
for name in ("ULPI_CK", "+3V3A", "I2C_SCL"):
    codes[name] = b.GetNetcodeFromNetname(name)
    assert codes[name] >= 0, name
print("netcodes:", codes)

def mm(v):
    return round(v / 1e6, 4)

def close(p, q):
    return abs(p[0] - q[0]) <= 0.002 and abs(p[1] - q[1]) <= 0.002

found = {i: 0 for i in range(len(RIP))}
victims = []
for t in list(b.GetTracks()):
    if t.Type() != pcbnew.PCB_TRACE_T:
        continue
    nc = t.GetNetCode()
    lay = t.GetLayer()
    a = (mm(t.GetStart().x), mm(t.GetStart().y))
    c = (mm(t.GetEnd().x), mm(t.GetEnd().y))
    for i, (name, rl, ra, rc) in enumerate(RIP):
        if nc != codes[name] or lay != rl:
            continue
        if (close(a, ra) and close(c, rc)) or (close(a, rc) and close(c, ra)):
            found[i] += 1
            victims.append(t)

bad = [RIP[i] for i, n in found.items() if n != 1]
assert not bad, f"rip items not found exactly once: {bad}"
for t in victims:
    b.Remove(t)
print(f"removed {len(victims)} tracks")
b.Save(OUT)
print("saved", OUT)
