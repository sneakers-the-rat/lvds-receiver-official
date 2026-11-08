"""t_ak11: tail survey -- NEG_RAW vias at (24.875,48.875); APD_K
tracks + Edge.Cuts geometry in the HV slot box."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])


def mm(p):
    return (round(pcbnew.ToMM(p)[0], 3), round(pcbnew.ToMM(p)[1], 3))


for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = mm(t.GetPosition())
        if abs(p[0] - 24.875) < 0.01 and abs(p[1] - 48.875) < 0.01:
            print(f'VIA {t.GetNetname()} at {p} d='
                  f'{pcbnew.ToMM(t.GetWidth()):.2f} drill='
                  f'{pcbnew.ToMM(t.GetDrill()):.2f} uuid={t.m_Uuid.AsString()}')
print('--- APD_K tracks in box x[8,32] y[16,34] ---')
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    if t.GetNetname() != 'APD_K':
        continue
    a, b = mm(t.GetStart()), mm(t.GetEnd())
    if 8 <= a[0] <= 32 and 16 <= a[1] <= 34:
        lay = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2',
               pcbnew.B_Cu: 'B'}.get(t.GetLayer(), '?')
        print(f'  SEG {lay} {a}->{b} w{pcbnew.ToMM(t.GetWidth()):.2f} '
              f'uuid={t.m_Uuid.AsString()}')
print('--- Edge.Cuts segments touching box x[0,50] y[15,35] ---')
for d in board.GetDrawings():
    if d.GetLayer() != pcbnew.Edge_Cuts:
        continue
    try:
        a, b = mm(d.GetStart()), mm(d.GetEnd())
    except Exception:
        print('  non-segment drawing:', d.GetShape())
        continue
    if (0 <= a[0] <= 50 and 15 <= a[1] <= 35) or \
            (0 <= b[0] <= 50 and 15 <= b[1] <= 35):
        print(f'  EDGE {a}->{b}')
