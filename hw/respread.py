#!/usr/bin/env python3
"""HV string respread + stale-stub cleanup (drain after pass 81).

Diagnosis (audit-exp22 + heal results): the grid placer interleaved
the R31 string (R31 centre 35.5, partner 37.0 — pads interleave,
hop edges ~0 mm apart) and heal_nets cannot start a track in the
1.0 mm HV clearance shadow of the stale tracks that still run to
the strings' OLD positions. Fixes, one mechanism each:
1. Respread the string row at y=-1.8 with 3.8 mm centres
   (R31 33.5, R49 37.3, R50 41.1; R47 pulled in to 47.8) and move
   R32 0.9 mm south out of the row's pad shadow. All moves
   pads-clear asserted via hw/gridplace.py.
2. Delete torn stub islands: per-net copper groups in the HV
   cluster bbox (x 28..54, y -7..1) for APD_K/HV_FBX/TP_HV/GND/
   HV_RAW that touch NO pad and hold <6 items — they are the
   ripped remains of runs to dead pad positions, and they are
   what the moved strings' pads violate against.
3. Delete the GND stub ending exactly on R30.2's pad (R30.2 was
   GND before the re-sync; the pad is HV_R30M now and the stub
   buries it in foreign copper).
Zones refilled at the end.
Usage: xvfb-run -a python3 hw/respread.py <src> <out>
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import gridplace
from hand_stub import build_items

MMf = pcbnew.FromMM
MMt = pcbnew.ToMM
SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
_DEAD = []
LOG = []

def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s, flush=True)

def move(ref, region, home):
    fp = board.FindFootprintByReference(ref)
    got = gridplace.place(board, fp, region, home, log=log)
    assert got, f'{ref}: no feasible point'
    return got

move('R32', (29.5, -4.3, 31.5, -3.5), (30.5, -3.9))
move('R49', (36.2, -5.5, 36.8, -4.9), (36.5, -5.2))
move('R31', (33.2, -2.1, 33.8, -1.5), (33.5, -1.8))
move('R50', (39.2, -2.1, 39.8, -1.5), (39.5, -1.8))
move('R47', (48.0, -2.1, 48.6, -1.5), (48.3, -1.8))

# ---- stub-island cleanup ----
items = build_items(board)
# pad positions per net (for the touch test)
pad_pts = {}
for fp in board.GetFootprints():
    for p in fp.Pads():
        pad_pts.setdefault(p.GetNetname(), []).append(
            (MMt(p.GetPosition().x), MMt(p.GetPosition().y)))

tracks = list(board.GetTracks())
bynetc = {}
for t in tracks:
    bynetc.setdefault(t.GetNetname(), []).append(t)

def tendpoints(t):
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        return [(MMt(p.x), MMt(p.y))]
    return [(MMt(t.GetStart().x), MMt(t.GetStart().y)),
            (MMt(t.GetEnd().x), MMt(t.GetEnd().y))]

def tsh(t):
    e = tendpoints(t)
    if len(e) == 1:
        return pcbnew.SHAPE_SEGMENT(
            pcbnew.VECTOR2I(MMf(e[0][0]), MMf(e[0][1])),
            pcbnew.VECTOR2I(MMf(e[0][0]), MMf(e[0][1])),
            MMf(MMt(t.GetWidth())))
    return pcbnew.SHAPE_SEGMENT(
        pcbnew.VECTOR2I(MMf(e[0][0]), MMf(e[0][1])),
        pcbnew.VECTOR2I(MMf(e[1][0]), MMf(e[1][1])),
        MMf(MMt(t.GetWidth())))

KILL_NETS = {'APD_K', 'HV_FBX', 'TP_HV', 'GND', 'HV_RAW'}
killed = 0
for net in KILL_NETS:
    ts = bynetc.get(net, [])
    n = len(ts)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    shapes = [tsh(t) for t in ts]
    laysets = [set(t.GetLayerSet().Seq()) for t in ts]
    for i in range(n):
        for j in range(i + 1, n):
            if laysets[i] & laysets[j] and \
                    shapes[i].Collide(shapes[j], MMf(0.001)):
                a, b = find(i), find(j)
                if a != b:
                    parent[a] = b
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    pads = pad_pts.get(net, [])
    for root, idxs in groups.items():
        if len(idxs) >= 6:
            continue
        # bbox test + pad touch test
        pts = [p for i in idxs for p in tendpoints(ts[i])]
        if not all(28 <= x <= 54 and -7 <= y <= 1 for x, y in pts):
            continue
        touch = False
        for (x, y) in pts:
            for (px, py) in pads:
                if abs(x - px) < 0.01 and abs(y - py) < 0.01:
                    touch = True
        if touch:
            continue
        for i in idxs:
            _DEAD.append(ts[i])
            board.Remove(ts[i])
            killed += 1
        log(f'  deleted {net} stub island ({len(idxs)} items) at '
            f'{[(round(x,1), round(y,1)) for x, y in pts[:2]]}')
log(f'stub islands deleted: {killed} items')

# ---- R30.2 GND stub ----
r30 = board.FindFootprintByReference('R30')
target = None
for p in r30.Pads():
    if p.GetNumber() == '2':
        target = (MMt(p.GetPosition().x), MMt(p.GetPosition().y))
assert target
for t in list(board.GetTracks()):
    if t.GetNetname() == 'GND':
        for (x, y) in tendpoints(t):
            if abs(x - target[0]) < 0.01 and abs(y - target[1]) < 0.01:
                _DEAD.append(t)
                board.Remove(t)
                log(f'  deleted GND stub ending on R30.2 {target}')
                break

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
log(f'saved {OUT} (respread + cleanup, zones refilled)')
open('results/respread-log.txt', 'w').write('\n'.join(LOG) + '\n')
