#!/usr/bin/env python3
"""SH1 surgery stage B on exp275: fix the stage-A DRC defects.
- restore the +VA spine (In1 leg + via moved west to (30.10,40.06),
  clear of the can's east wall) so U3.5/U2.5 stay fed;
- cluster +VA feed via a via in U3.5's pad (same net) + W/N/E route;
- CMP_IN re-routed west around R8 instead of east into CL6;
- CL6 (east clip) moved south to (31.05,32.50), CL4 (SE south clip)
  deleted - the south wall east of C3 has no lawful clip window;
  clips renumber to CL1-CL5 (2N/1S/1W/1E);
- C7/C44/C2 nudged west to clear C37/C43/C25 courtyards and pads;
- orphan GND stubs at the old SH1 pad centres ripped;
- GND stitch via+track for every clip."""
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

# ---------- rip stage-A mistakes ----------
to_rip = []
for net, a, b, lay in [
        ('+VA', (38.30, 41.05), (38.30, 41.90), F),
        ('+VA', (38.30, 41.90), (37.07, 41.90), F),
        ('+VA', (37.07, 41.90), (37.07, 42.80), F),
        ('+VA', (37.40, 42.80), (37.40, 45.90), F),
        ('CMP_IN', (30.15, 35.90), (31.07, 35.90), F),
        ('CMP_IN', (31.07, 35.90), (31.07, 38.50), F),
        ('CMP_IN', (31.07, 37.75), (32.58, 37.75), F)]:
    hits = find_track(net, a, b, lay)
    assert len(hits) == 1, (net, a, b, len(hits))
    to_rip += hits
v = find_via('+VA', (38.30, 41.05))
assert v is not None
to_rip.append(v)
# orphan GND stubs at the old SH1 pad centres (4.0,31.0) and (28.0,31.0)
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != 'GND':
        continue
    s, e = t.GetStart(), t.GetEnd()
    pts = {(round(s.x / 1e6, 2), round(s.y / 1e6, 2)),
           (round(e.x / 1e6, 2), round(e.y / 1e6, 2))}
    if pts & {(4.0, 31.0), (28.0, 31.0)} and t.GetLength() / 1e6 < 0.8:
        to_rip.append(t)
for t in to_rip:
    board.Remove(t)
print('ripped', len(to_rip))

# ---------- moves / clip renumber ----------
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
for ref, (x, y) in {'C7': (37.5, 42.8), 'C44': (37.9, 44.3),
                    'C2': (37.9, 46.1), 'CL6': (31.05, 32.50)}.items():
    fps[ref].SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    print('moved', ref, '->', (x, y))
board.Remove(fps['CL4'])
fps['CL5'].SetReference('CL4')
fps['CL6'].SetReference('CL5')
print('clips renumbered: CL4 = W (11.05,33.75), CL5 = E (31.05,32.50); '
      'SE south clip deleted')


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


# ---------- +VA spine restore ----------
add_track('+VA', (30.82, 40.05), (37.73, 39.98), IN1, 0.3)
add_via('+VA', (30.10, 40.06))
add_track('+VA', (28.38, 40.38), (30.10, 40.38), F, 0.6)
add_track('+VA', (30.10, 40.38), (30.10, 40.06), F, 0.6)
# ---------- cluster feed: via in U3.5 pad + W/N/E ----------
add_via('+VA', (36.90, 40.02))
add_track('+VA', (36.90, 40.02), (35.90, 40.02), F, 0.3)
add_track('+VA', (35.90, 40.02), (35.90, 41.90), F, 0.3)
add_track('+VA', (35.90, 41.90), (36.90, 41.90), F, 0.3)
add_track('+VA', (36.90, 41.90), (36.90, 42.80), F, 0.3)
add_track('+VA', (37.00, 42.80), (37.00, 46.10), F, 0.3)
# ---------- CMP_IN west route ----------
add_track('CMP_IN', (29.20, 35.90), (30.15, 35.90), F, 0.2)
add_track('CMP_IN', (29.20, 35.90), (29.20, 38.40), F, 0.2)
add_track('CMP_IN', (29.20, 38.40), (31.07, 38.40), F, 0.2)
add_track('CMP_IN', (31.07, 38.40), (31.07, 38.50), F, 0.2)
# ---------- clip GND stitches ----------
add_track('GND', (23.90, 29.75), (23.90, 31.60), F, 0.3)
add_via('GND', (23.90, 31.60))
add_track('GND', (28.80, 29.75), (28.80, 31.60), F, 0.3)
add_via('GND', (28.80, 31.60))
add_track('GND', (14.65, 44.75), (14.65, 46.60), F, 0.3)
add_via('GND', (14.65, 46.60))
add_track('GND', (11.05, 33.75), (11.05, 31.90), F, 0.3)
add_via('GND', (11.05, 31.90))
add_track('GND', (31.05, 32.50), (32.30, 32.50), F, 0.3)
add_via('GND', (32.30, 32.50))
print('stage B additions done')

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(SRC)
print('saved', SRC)
