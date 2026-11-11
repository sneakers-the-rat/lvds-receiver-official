#!/usr/bin/env python3
"""SH1 stage C4: cluster +VA tap onto the In1 diagonal at
(38.30,41.03) - the one point clearing C37.1's pad by 0.25 -
exiting south in the empty x=38.3 channel."""
import wx
wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp275.kicad_pcb'
board = pcbnew.LoadBoard(SRC)
F = pcbnew.F_Cu

def mm(v): return int(round(v * 1e6))

def find_track(net, a, b, layer=None):
    hits = []
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != net: continue
        if layer is not None and t.GetLayer() != layer: continue
        s, e = t.GetStart(), t.GetEnd()
        sp, ep = (s.x/1e6, s.y/1e6), (e.x/1e6, e.y/1e6)
        if (abs(sp[0]-a[0])<0.01 and abs(sp[1]-a[1])<0.01 and abs(ep[0]-b[0])<0.01 and abs(ep[1]-b[1])<0.01) or \
           (abs(sp[0]-b[0])<0.01 and abs(sp[1]-b[1])<0.01 and abs(ep[0]-a[0])<0.01 and abs(ep[1]-a[1])<0.01):
            hits.append(t)
    return hits

def find_via(net, at):
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() != net: continue
        p = t.GetPosition()
        if abs(p.x/1e6-at[0])<0.01 and abs(p.y/1e6-at[1])<0.01: return t
    return None

nets = {z: board.FindNet(z).GetNetCode() for z in ('+VA',)}
to_rip = []
for net, a, b in [('+VA',(40.25,41.60),(40.25,42.55)),
                  ('+VA',(40.25,42.55),(39.19,42.55))]:
    hits = find_track(net, a, b, F)
    assert len(hits) == 1, (a, b, len(hits))
    to_rip += hits
v = find_via('+VA', (40.25, 41.60)); assert v is not None; to_rip.append(v)
for t in to_rip: board.Remove(t)
print('ripped', len(to_rip))

def add_track(net, a, b, layer, w):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
    t.SetLayer(layer); t.SetWidth(mm(w)); t.SetNetCode(nets[net]); board.Add(t)

def add_via(net, at, dia=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(at[0]), mm(at[1]))); v.SetWidth(mm(dia)); v.SetDrill(mm(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNetCode(nets[net]); board.Add(v)

add_via('+VA', (38.30, 41.03))
add_track('+VA', (38.30, 41.03), (38.30, 42.55), F, 0.2)
add_track('+VA', (38.30, 42.55), (39.19, 42.55), F, 0.2)
print('tap at (38.30,41.03)')
filler = pcbnew.ZONE_FILLER(board); filler.Fill(board.Zones())
board.Save(SRC); print('saved', SRC)
