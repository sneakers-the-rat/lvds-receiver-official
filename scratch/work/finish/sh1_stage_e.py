#!/usr/bin/env python3
"""SH1 stage E: widen the +VA cluster feed past C7.2's GND pad.
The F vertical leg moves from x=38.35 to x=38.47 (channel centre
between C7.2 east edge 38.12 and C37.1 west edge 38.80), with a
short jog on the via top at (38.35,41.60)."""
import wx
wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp275.kicad_pcb'
board = pcbnew.LoadBoard(SRC)

def mm(v): return int(round(v * 1e6))

def seg_key(s):
    a, e = s.GetStart(), s.GetEnd()
    return (s.GetNetname(), s.GetLayer(),
            tuple(sorted(((a.x, a.y), (e.x, e.y)))))

targets = {
    ('+VA', pcbnew.F_Cu, ((mm(38.35), mm(41.60)), (mm(38.35), mm(42.55)))),
    ('+VA', pcbnew.F_Cu, ((mm(38.35), mm(42.55)), (mm(39.19), mm(42.55)))),
}
found = []
rest = []
for t in board.GetTracks():
    if t.Type() != pcbnew.PCB_VIA_T and seg_key(t) in targets:
        found.append(t)
    else:
        rest.append(t)
assert len(found) == 2, 'found %d of 2 legs' % len(found)
for t in found:
    board.Remove(t)
print('ripped', len(found), 'legs')

nc = board.GetNetcodeFromNetname('+VA')

def add_seg(x1, y1, x2, y2, w=0.20):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetWidth(mm(w))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNetCode(nc)
    board.Add(t)
    print('seg (%.2f,%.2f)-(%.2f,%.2f) w%.2f' % (x1, y1, x2, y2, w))

add_seg(38.35, 41.60, 38.47, 41.60)
add_seg(38.47, 41.60, 38.47, 42.55)
add_seg(38.47, 42.55, 39.19, 42.55)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(SRC)
print('saved', SRC)
