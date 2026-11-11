#!/usr/bin/env python3
"""SH1 surgery stage C on exp275: fix the stage-B residue.
- +VA via off the In1 leg's end -> (30.55,40.045) with the leg
  extended to meet it (clears R7.2 hole clearance and the wall);
- cluster +VA feed rerouted from the SOUTHERN In1 spine
  (via at (41.10,45.60)) - no via-in-pad, no U3.4 corridor;
- CMP_IN east link restored; R8 west to (28.80,35.90) so its
  courtyard clears the east clip; C7/C44/C2 final positions from
  measured courtyard rects; CL5 (east clip) to (31.05,33.00);
- clip pad spines so all three pads of each clip are one copper;
- orphan GND via at (4.75,31.0) ripped."""
import wx
wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp275.kicad_pcb'
board = pcbnew.LoadBoard(SRC)
F = pcbnew.F_Cu
IN1 = pcbnew.In1_Cu


def mm(v):
    return int(round(v * 1e6))


def find_track(net, a, b, layer=None):
    hits = []
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != net:
            continue
        if layer is not None and t.GetLayer() != layer:
            continue
        s, e = t.GetStart(), t.GetEnd()
        sp = (s.x / 1e6, s.y / 1e6)
        ep = (e.x / 1e6, e.y / 1e6)
        if (abs(sp[0] - a[0]) < 0.01 and abs(sp[1] - a[1]) < 0.01
                and abs(ep[0] - b[0]) < 0.01 and abs(ep[1] - b[1]) < 0.01) or \
           (abs(sp[0] - b[0]) < 0.01 and abs(sp[1] - b[1]) < 0.01
                and abs(ep[0] - a[0]) < 0.01 and abs(ep[1] - a[1]) < 0.01):
            hits.append(t)
    return hits


def find_via(net, at):
    for t in board.GetTracks():
        if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() != net:
            continue
        p = t.GetPosition()
        if abs(p.x / 1e6 - at[0]) < 0.01 and abs(p.y / 1e6 - at[1]) < 0.01:
            return t
    return None


nets = {z: board.FindNet(z).GetNetCode()
        for z in ('+VA', 'POST_OUT', 'CMP_IN', 'GND')}

to_rip = []
for net, a, b, lay in [
        ('+VA', (30.82, 40.05), (37.73, 39.98), IN1),
        ('+VA', (28.38, 40.38), (30.10, 40.38), F),
        ('+VA', (30.10, 40.38), (30.10, 40.06), F),
        ('+VA', (36.90, 40.02), (35.90, 40.02), F),
        ('+VA', (35.90, 40.02), (35.90, 41.90), F),
        ('+VA', (35.90, 41.90), (36.90, 41.90), F),
        ('+VA', (36.90, 41.90), (36.90, 42.80), F),
        ('+VA', (37.00, 42.80), (37.00, 46.10), F),
        ('POST_OUT', (28.18, 37.75), (28.18, 35.90), F),
        ('POST_OUT', (28.18, 35.90), (28.49, 35.90), F),
        ('CMP_IN', (29.20, 35.90), (30.15, 35.90), F),
        ('GND', (31.05, 32.50), (32.30, 32.50), F)]:
    hits = find_track(net, a, b, lay)
    assert len(hits) == 1, (net, a, b, len(hits))
    to_rip += hits
for net, at in [('+VA', (30.10, 40.06)), ('+VA', (36.90, 40.02)),
                ('GND', (32.30, 32.50)), ('GND', (4.75, 31.00))]:
    v = find_via(net, at)
    assert v is not None, (net, at)
    to_rip.append(v)
for t in to_rip:
    board.Remove(t)
print('ripped', len(to_rip))

fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
for ref, (x, y) in {'R8': (28.80, 35.90), 'C7': (36.90, 42.80),
                    'C44': (37.60, 44.50), 'C2': (37.40, 46.20),
                    'CL5': (31.05, 33.00)}.items():
    fps[ref].SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    print('moved', ref, '->', (x, y))


def add_track(net, a, b, layer, w):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
    t.SetLayer(layer)
    t.SetWidth(mm(w))
    t.SetNetCode(nets[net])
    board.Add(t)


def add_via(net, at, dia=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(at[0]), mm(at[1])))
    v.SetWidth(mm(dia))
    v.SetDrill(mm(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNetCode(nets[net])
    board.Add(v)


# +VA spine tap, moved via
add_track('+VA', (30.55, 40.045), (37.73, 39.98), IN1, 0.3)
add_via('+VA', (30.55, 40.045))
add_track('+VA', (28.38, 40.38), (30.55, 40.38), F, 0.6)
add_track('+VA', (30.55, 40.38), (30.55, 40.045), F, 0.6)
# cluster feed from the southern spine
add_via('+VA', (41.10, 45.60))
add_track('+VA', (41.10, 45.60), (39.60, 45.60), F, 0.2)
add_track('+VA', (39.60, 45.60), (39.60, 45.30), F, 0.2)
add_track('+VA', (39.60, 45.30), (36.80, 45.30), F, 0.2)
add_track('+VA', (36.80, 42.80), (36.80, 46.20), F, 0.3)
add_track('+VA', (36.80, 42.80), (36.30, 42.80), F, 0.3)
# POST_OUT / CMP_IN for R8 at (28.80,35.90)
add_track('POST_OUT', (28.18, 37.75), (27.97, 37.75), F, 0.2)
add_track('POST_OUT', (27.97, 37.75), (27.97, 35.90), F, 0.2)
add_track('CMP_IN', (29.20, 35.90), (29.63, 35.90), F, 0.2)
add_track('CMP_IN', (31.07, 37.75), (31.07, 38.40), F, 0.2)
add_track('CMP_IN', (31.07, 37.75), (32.58, 37.75), F, 0.2)
# clip spines + CL5 stitch at its new position
add_track('GND', (22.30, 29.75), (25.50, 29.75), F, 0.3)
add_track('GND', (27.20, 29.75), (30.40, 29.75), F, 0.3)
add_track('GND', (13.05, 44.75), (16.25, 44.75), F, 0.3)
add_track('GND', (11.05, 32.15), (11.05, 35.35), F, 0.3)
add_track('GND', (31.05, 31.40), (31.05, 34.60), F, 0.3)
add_track('GND', (31.05, 33.00), (32.30, 33.00), F, 0.3)
add_via('GND', (32.30, 33.00))
print('stage C additions done')

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(SRC)
print('saved', SRC)
