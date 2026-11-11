#!/usr/bin/env python3
"""SH1 stage F: reload the can + clip footprints (Fab long-text fix:
moved to descr), refill, save."""
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


filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(SRC)
print('saved', SRC)
