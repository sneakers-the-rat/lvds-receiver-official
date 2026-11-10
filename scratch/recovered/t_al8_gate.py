"""Joint gate: DAC_SYNC west-dive re-lay + SWCLK route (exp225 field).
Rips: DAC F stub/diag/via(90.125,-17.875) + B tail to (89.625,-15.625).
DAC adds: F stub+diag+west run, via(87.3,-17.9), B rejoin seg.
SWCLK adds: F stub+diag+south run, via(89.75,-20.05), B path to J4.4."""
import sys, wx
_app = wx.App(False)
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/work/ai')
import pcbnew
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp225.kicad_pcb')
items = load_items(b)
RIPSEG = [(90.25, -16.663, 90.25, -17.163), (90.25, -17.163, 90.125, -17.875),
          (90.125, -17.875, 90.125, -16.125), (90.125, -16.125, 89.875, -15.875),
          (89.875, -15.875, 89.625, -15.625)]
def is_rip(it):
    if it[1] != 'DAC_SYNC':
        return False
    if it[0] == 'via':
        d = it[2]
        return abs(d[0] - 90.125) < 0.01 and abs(d[1] + 17.875) < 0.01
    if it[0] != 'seg':
        return False
    d = it[2]
    return any(abs(d[0]-s[0]) < 0.01 and abs(d[1]-s[1]) < 0.01 and
               abs(d[2]-s[2]) < 0.01 and abs(d[3]-s[3]) < 0.01 for s in RIPSEG)
items2 = {li: [it for it in items[li] if not is_rip(it)] for li in range(3)}
nrip = sum(1 for li in range(3) for it in items[li] if is_rip(it))
print(f'ripped {nrip} item-instances (5 segs x1 layer + via x3 layers = 8)')
box = (85.0, 95.0, -26.0, -13.0)
pool = in_box_pool(items2, box, pad=1.2)

DAC_ADD = [('seg', 0, (90.25, -16.663), (90.25, -17.55), 0.10),
           ('seg', 0, (90.25, -17.55), (89.3, -17.9), 0.10),
           ('seg', 0, (89.3, -17.9), (87.3, -17.9), 0.10),
           ('via', None, (87.3, -17.9), 0.25),
           ('seg', 2, (87.3, -17.9), (89.625, -15.625), 0.125)]
SW_ADD = [('seg', 0, (90.75, -16.663), (90.75, -17.75), 0.10),
          ('seg', 0, (90.75, -17.75), (89.75, -18.35), 0.10),
          ('seg', 0, (89.75, -18.35), (89.75, -20.05), 0.10),
          ('via', None, (89.75, -20.05), 0.25),
          ('seg', 2, (89.75, -20.05), (89.9, -23.0), 0.10),
          ('seg', 2, (89.9, -23.0), (90.3, -24.55), 0.10),
          ('seg', 2, (90.3, -24.55), (92.52, -24.55), 0.10),
          ('seg', 2, (92.52, -24.55), (92.52, -23.52), 0.10)]

def pseudo(adds):
    out = {0: [], 1: [], 2: []}
    for a in adds:
        if a[0] == 'seg':
            _, li, p, q, hw_ = a
            out[li].append(('seg', CUR[0], (p[0], p[1], q[0], q[1], hw_), 0.2))
        else:
            _, _, p, r = a
            for li in range(3):
                out[li].append(('via', CUR[0], (p[0], p[1], r), 0.2))
    return out

ok = True
for CUR, adds in [(('DAC_SYNC',), DAC_ADD), (('SWCLK',), SW_ADD)]:
    other = SW_ADD if CUR[0] == 'DAC_SYNC' else DAC_ADD
    CUR2 = ('SWCLK',) if CUR[0] == 'DAC_SYNC' else ('DAC_SYNC',)
    save = CUR
    CUR = CUR2
    opool = pseudo(other)
    CUR = save
    full = {li: pool[li] + opool[li] for li in range(3)}
    for a in adds:
        if a[0] == 'seg':
            _, li, p, q, hw_ = a
            m, w = seg_margin(li, p, q, CUR[0], hw_, full[li])
            print(f'{CUR[0]} seg L{li} {p}->{q}: {m:+.3f} worst {fmt_it(w)}')
        else:
            _, _, p, r = a
            for li in range(3):
                m, w = pt_margin(li, p[0], p[1], CUR[0], r, full[li])
                print(f'{CUR[0]} via {p} L{li}: {m:+.3f} worst {fmt_it(w)}')
        ok &= m >= 0
print('ALL GATES PASS' if ok else 'SOME GATES FAIL')
