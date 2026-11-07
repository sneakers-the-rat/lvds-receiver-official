"""t_ab17a: rip ULPI_CK's dive assembly from exp213, save base
board for the t_ab17 solver (fresh process - the board object
degrades after Remove())."""
import wx
_app = wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp213.kicad_pcb')
MM = pcbnew.ToMM
def key(a, bb):
    return frozenset(((round(a[0], 3), round(a[1], 3)),
                      (round(bb[0], 3), round(bb[1], 3))))
rip_segs = {key((76.75, 16.438), (76.62, 17.30)),
            key((76.62, 17.30), (76.62, 13.50))}
n = 0
for t in list(b.GetTracks()):
    if t.GetNetname() != 'ULPI_CK':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if abs(p[0] - 76.62) < 0.01 and abs(p[1] - 17.30) < 0.01:
            b.Remove(t); n += 1
        continue
    s, e = t.GetStart(), t.GetEnd()
    if key((MM(s.x), MM(s.y)), (MM(e.x), MM(e.y))) in rip_segs:
        b.Remove(t); n += 1
print(f'ripped {n} (expect 3)')
assert n == 3
b.Save('scratch/work/t_ab17_base.kicad_pcb')
print('saved scratch/work/t_ab17_base.kicad_pcb')
