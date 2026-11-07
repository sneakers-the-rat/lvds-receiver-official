"""t_ag6: exact XO track diff exp217 vs t_ag4 trial."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
LAY = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
       pcbnew.B_Cu: 'B'}
def items(path):
    b = pcbnew.LoadBoard(path)
    out = []
    for t in b.GetTracks():
        if t.GetNetname() != 'XO':
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            p = MM(t.GetPosition())
            out.append(('via', round(p[0], 3), round(p[1], 3),
                        round(MM(t.GetWidth()), 2)))
        else:
            a, c = MM(t.GetStart()), MM(t.GetEnd())
            k = tuple(sorted([(round(a[0], 3), round(a[1], 3)),
                              (round(c[0], 3), round(c[1], 3))]))
            out.append(('seg', LAY[t.GetLayer()], k,
                        round(MM(t.GetWidth()), 2)))
    return sorted(map(str, out))
A = items('hw/pdlvds_rx.exp217.kicad_pcb')
B = items('scratch/work/t_ag4_trial.kicad_pcb')
print(f'exp217: {len(A)}  trial: {len(B)}')
print('--- only in exp217 (ripped) ---')
for x in A:
    if x not in B:
        print(' ', x)
print('--- only in trial (added) ---')
for x in B:
    if x not in A:
        print(' ', x)
