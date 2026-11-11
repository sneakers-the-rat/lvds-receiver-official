#!/usr/bin/env python3
"""SH1 stage D: reload the can + clip footprints (silk rects
removed), reposition the silk texts DRC flagged, refill, save."""
import wx
wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp275.kicad_pcb'
board = pcbnew.LoadBoard(SRC)

def mm(v): return int(round(v * 1e6))

fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
gnd = board.FindNet('GND').GetNetCode()

def fields_of(fp):
    out = {}
    for f in fp.GetFields():
        out[f.GetCanonicalName()] = (f.GetText(), f.GetPosition())
    return out

def reload_fp(ref, libname):
    old = fps[ref]
    pos, rot = old.GetPosition(), old.GetOrientationDegrees()
    saved = fields_of(old)
    board.Remove(old)
    new = pcbnew.FootprintLoad('hw/pdlvds.pretty', libname)
    assert new is not None, libname
    new.SetPosition(pos)
    new.SetOrientationDegrees(rot)
    board.Add(new)
    for f in new.GetFields():
        name = f.GetCanonicalName()
        if name in saved:
            f.SetText(saved[name][0])
    new.SetReference(ref)
    return new

sh1 = reload_fp('SH1', 'SHIELD_CAN_S02_20150300')
sh1.SetValue('Harwin S02-20150300 20x15x3 can (S1001-46R clips)')
clips = {}
for ref in ('CL1', 'CL2', 'CL3', 'CL4', 'CL5'):
    fp = reload_fp(ref, 'HARWIN_S1001')
    fp.SetValue('Harwin S1001-46R shield clip')
    for p in fp.Pads():
        p.SetNetCode(gnd)
    clips[ref] = fp
print('footprints reloaded')

# text placement: {ref: (x, y)} for the Reference field
TEXTPOS = {
    'SH1': (21.05, 37.25),
    'CL1': (22.20, 28.20), 'CL2': (29.90, 28.30),
    'CL3': (13.30, 43.30), 'CL5': (32.70, 30.80),
    'CL4': (9.30, 36.60),
    'R8': (27.50, 34.60), 'C7': (35.50, 44.40),
    'C44': (35.80, 45.90), 'C2': (36.10, 47.40),
    'C37': (41.40, 40.10), 'C43': (42.40, 43.30),
}
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
for ref, (x, y) in TEXTPOS.items():
    fp = fps[ref]
    t = fp.Reference()
    t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    t.SetVisible(True)
    print('text', ref, '->', (x, y))

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(SRC)
print('saved', SRC)
