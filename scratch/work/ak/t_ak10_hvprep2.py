"""t_ak10: HV pocket full prep -- rip GND EP via+seg (redundant),
HV_GATE needle set, HV_SHDN F web + via + In2 run, HV_FBX In2
staircase segs inside the pocket box. Usage: t_ak10 in out"""
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
    ('HV_SHDN', 'F', (29.65, -3.5), (30.4, -3.5)),
    ('HV_SHDN', 'F', (30.4, -3.5), (30.625, -3.375)),
    ('HV_SHDN', 'F', (30.625, -3.375), (30.875, -3.125)),
    ('HV_SHDN', 'F', (30.875, -3.125), (30.875, -2.875)),
    ('HV_SHDN', 'In2', (30.875, -2.875), (43.375, -2.875)),
    ('HV_FBX', 'In2', (28.875, -3.875), (29.125, -3.625)),
    ('HV_FBX', 'In2', (29.125, -3.625), (29.375, -3.375)),
    ('HV_FBX', 'In2', (29.375, -3.375), (29.625, -3.125)),
    ('HV_FBX', 'In2', (29.625, -3.125), (29.875, -2.875)),
    ('HV_FBX', 'In2', (29.875, -2.875), (30.125, -2.625)),
    ('HV_FBX', 'In2', (30.125, -2.625), (30.375, -2.375)),
    ('HV_FBX', 'In2', (30.375, -2.375), (30.625, -2.125)),
    ('HV_FBX', 'In2', (30.625, -2.125), (32.375, -2.125)),
    ('HV_FBX', 'In2', (32.375, -2.125), (32.625, -1.875)),
]
RIP_VIAS = [('GND', (28.25, -3.0)), ('HV_GATE', (31.7, -1.5)),
            ('HV_SHDN', (30.875, -2.875))]
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
