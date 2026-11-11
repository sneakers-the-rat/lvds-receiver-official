#!/usr/bin/env python3
"""SH1 surgery stage A on exp275: relocate R8/C7/C44/C2, swap the
can to the 20x15 S02-20150300 at (21.05,37.25), add six S1001-46R
clips, re-lay the affected webs, refill, save.
Geometry lock: scratch/work/finish/sh1_plan.md (FINAL LOCK)."""
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


nets = {n.GetNetname(): n.GetNetCode()
        for n in [board.FindNet(z) for z in
                  ('+VA', 'POST_OUT', 'CMP_IN', 'GND')]}
print('netcodes:', nets)

# ---------- rip ----------
RIP = [('+VA', (28.38, 40.38), (30.75, 40.38), F),
       ('+VA', (31.00, 40.50), (31.00, 41.50), F),
       ('+VA', (30.62, 43.00), (30.88, 41.75), F),
       ('+VA', (30.82, 40.05), (37.73, 39.98), IN1),
       ('POST_OUT', (28.18, 37.75), (29.43, 37.75), F),
       ('CMP_IN', (31.07, 38.50), (31.07, 37.75), F),
       ('CMP_IN', (31.07, 37.75), (32.58, 37.75), F)]
to_rip = []
for net, a, b, lay in RIP:
    hits = find_track(net, a, b, lay)
    assert len(hits) == 1, (net, a, b, len(hits))
    to_rip += hits
via = find_via('+VA', (30.82, 40.05))
assert via is not None
to_rip.append(via)
for t in to_rip:
    board.Remove(t)
print('ripped', len(to_rip), 'items')

# ---------- move parts ----------
MOVES = {'R8': (29.32, 35.90), 'C7': (37.9, 42.8),
         'C44': (38.4, 44.3), 'C2': (38.3, 45.9)}
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
for ref, (x, y) in MOVES.items():
    fp = fps[ref]
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    print('moved', ref, '->', (x, y))

# ---------- SH1 swap ----------
old = fps['SH1']
fields = {}
for f in old.GetFields():
    fields[f.GetName()] = (f.GetText(), f.GetPosition(), f.IsVisible())
board.Remove(old)
new = pcbnew.FootprintLoad('hw/pdlvds.pretty', 'SHIELD_CAN_S02_20150300')
assert new is not None
new.SetReference('SH1')
new.SetValue('Harwin S02-20150300 20x15x3 can (S1001-46R clips)')
new.SetPosition(pcbnew.VECTOR2I(mm(21.05), mm(37.25)))
board.Add(new)
for name, (text, pos, vis) in fields.items():
    for f in new.GetFields():
        if f.GetName() == name:
            f.SetText(text)
            f.SetPosition(pos)
print('SH1 swapped -> S02-20150300 at (21.05, 37.25)')

# ---------- clips ----------
CLIPS = {'CL1': (23.9, 29.75, 0), 'CL2': (28.8, 29.75, 0),
         'CL3': (14.65, 44.75, 0), 'CL4': (28.8, 44.75, 0),
         'CL5': (11.05, 33.75, 90), 'CL6': (31.05, 33.75, 90)}
for ref, (x, y, rot) in CLIPS.items():
    fp = pcbnew.FootprintLoad('hw/pdlvds.pretty', 'HARWIN_S1001')
    assert fp is not None
    fp.SetReference(ref)
    fp.SetValue('Harwin S1001-46R shield clip')
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    fp.SetOrientationDegrees(rot)
    board.Add(fp)
    for p in fp.Pads():
        p.SetNetCode(nets['GND'])
    print('clip', ref, 'at', (x, y), 'r', rot)

# ---------- re-lay webs ----------
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


# POST_OUT into R8.1 (28.49, 35.90)
add_track('POST_OUT', (28.18, 37.75), (28.18, 35.90), F, 0.2)
add_track('POST_OUT', (28.18, 35.90), (28.49, 35.90), F, 0.2)
# CMP_IN from R8.2 (30.15, 35.90) to the surviving chain
add_track('CMP_IN', (30.15, 35.90), (31.07, 35.90), F, 0.2)
add_track('CMP_IN', (31.07, 35.90), (31.07, 38.50), F, 0.2)
add_track('CMP_IN', (31.07, 37.75), (32.58, 37.75), F, 0.2)
# +VA east cluster: via on the In1 spine, F feed, spine south
add_via('+VA', (38.30, 41.05))
add_track('+VA', (38.30, 41.05), (38.30, 41.90), F, 0.3)
add_track('+VA', (38.30, 41.90), (37.07, 41.90), F, 0.3)
add_track('+VA', (37.07, 41.90), (37.07, 42.80), F, 0.3)
add_track('+VA', (37.40, 42.80), (37.40, 45.90), F, 0.3)
print('webs re-laid')

# ---------- refill + save ----------
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(SRC)
print('saved', SRC)
