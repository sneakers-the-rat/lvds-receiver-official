"""t_ak13: APD_K slot detour. Gates the design in the exact item
model first; if green, builds exp222: rip the 3 slot-crossing segs
+ the north vertical, lay the west-end detour (all F w0.4), refill
zones, save, and print the reload per-net census for APD_K.
Usage: t_ak13_apdk.py in out"""
import sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import load_items, seg_margin, in_box_pool, fmt_it

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = load_items(board)

RIP = [((17.788, 26.5), (17.788, 25.0)),
       ((17.788, 25.0), (18.125, 24.375)),
       ((18.125, 24.375), (18.125, 18.625))]
ADD = [((12.875, 26.375), (11.25, 26.375)),
       ((11.25, 26.375), (11.25, 22.85)),
       ((11.25, 22.85), (18.125, 22.85)),
       ((18.125, 22.85), (18.125, 18.625))]


def is_rip(it):
    if it[0] != 'seg' or it[1] != 'APD_K':
        return False
    d = it[2]
    a, b = (d[0], d[1]), (d[2], d[3])
    return any((abs(a[0] - r[0][0]) < 0.01 and abs(a[1] - r[0][1]) < 0.01
                and abs(b[0] - r[1][0]) < 0.01 and
                abs(b[1] - r[1][1]) < 0.01) or
               (abs(b[0] - r[0][0]) < 0.01 and abs(b[1] - r[0][1]) < 0.01
                and abs(a[0] - r[1][0]) < 0.01 and
                abs(a[1] - r[1][1]) < 0.01) for r in RIP)


statics = [it for it in items[0] if not is_rip(it)]
pool = in_box_pool({0: statics, 1: items[1], 2: items[2]},
                   (8.0, 22.0, 16.0, 30.0), pad=1.2)[0]
adds = [('seg', 'APD_K', (a[0], a[1], b[0], b[1], 0.2), 1.0)
        for a, b in ADD]
ok = True
for a, b in ADD:
    m, w = seg_margin(0, a, b, 'APD_K', 0.2, pool + adds)
    print(f'  gate {a}->{b}: {m:+.3f} worst {fmt_it(w)}')
    if m < 0:
        ok = False
if not ok:
    print('GATES FAIL -- no build')
    sys.exit(1)

# capture netcodes before any Remove (net-name map dies after)
nc = {}
for t in board.GetTracks():
    nc[t.GetNetname()] = t.GetNetCode()
for fp in board.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname():
            nc[p.GetNetname()] = p.GetNetCode()
nrip = 0
for t in list(board.GetTracks()):
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != 'APD_K':
        continue
    a = (round(pcbnew.ToMM(t.GetStart())[0], 3),
         round(pcbnew.ToMM(t.GetStart())[1], 3))
    b = (round(pcbnew.ToMM(t.GetEnd())[0], 3),
         round(pcbnew.ToMM(t.GetEnd())[1], 3))
    if any((a == r[0] and b == r[1]) or (a == r[1] and b == r[0])
           for r in RIP):
        board.Remove(t)
        nrip += 1
print(f'ripped {nrip}')
for a, b in ADD:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
    t.SetWidth(pcbnew.FromMM(0.4))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNetCode(nc['APD_K'])
    board.Add(t)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
b2 = pcbnew.LoadBoard(OUT)
from collections import Counter
c = Counter(t.GetNetname() for t in b2.GetTracks())
print('reload APD_K items:', c['APD_K'])
