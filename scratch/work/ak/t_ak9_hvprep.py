"""t_ak9: HV pocket prep -- rip the redundant GND EP via + its F seg
(EP stays connected via the x28.125 vertical) and HV_GATE's needle
(F seg + via + B stub seg) from exp221. Usage: t_ak9 in out"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])


def mm(p):
    return (round(pcbnew.ToMM(p)[0], 3), round(pcbnew.ToMM(p)[1], 3))


RIP_SEGS = [
    ('GND', 'F', (27.5, -3.0), (28.25, -3.0)),
    ('HV_GATE', 'F', (30.375, -2.5), (31.6, -1.55)),
    ('HV_GATE', 'B', (31.6, -1.55), (30.375, -2.375)),
]
RIP_VIAS = [('GND', (28.25, -3.0)), ('HV_GATE', (31.7, -1.5))]
LAY = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
n = 0
for t in list(board.GetTracks()):
    net = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        p = mm(t.GetPosition())
        if any(net == rn and p == rp for rn, rp in RIP_VIAS):
            board.Remove(t)
            n += 1
    else:
        a, b = mm(t.GetStart()), mm(t.GetEnd())
        lay = LAY.get(t.GetLayer())
        for rn, rl, ra, rb in RIP_SEGS:
            if net == rn and lay == rl and \
                    ((a == ra and b == rb) or (a == rb and b == ra)):
                board.Remove(t)
                n += 1
print(f'ripped {n} tracks')
board.Save(sys.argv[2])
