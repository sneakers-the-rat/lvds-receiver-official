#!/usr/bin/env python3
"""SH1 stage C2: move the cluster +VA tap north to (41.10,42.90)."""
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
for net, a, b in [('+VA',(41.10,45.60),(39.60,45.60)),
                  ('+VA',(39.60,45.60),(39.60,45.30)),
                  ('+VA',(39.60,45.30),(36.80,45.30))]:
    hits = find_track(net, a, b, F)
    assert len(hits) == 1, (a, b, len(hits))
    to_rip += hits
v = find_via('+VA', (41.10, 45.60)); assert v is not None; to_rip.append(v)
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

add_via('+VA', (41.10, 42.90))
add_track('+VA', (41.10, 42.90), (39.19, 42.90), F, 0.2)
add_track('+VA', (39.19, 42.90), (39.19, 45.30), F, 0.2)
add_track('+VA', (39.19, 45.30), (36.80, 45.30), F, 0.2)
print('tap moved to (41.10,42.90)')
filler = pcbnew.ZONE_FILLER(board); filler.Fill(board.Zones())
board.Save(SRC); print('saved', SRC)
