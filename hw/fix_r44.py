#!/usr/bin/env python3
"""R44.1 LED_PWR_K reconnection after the MH2-item move
(pass 128): the pad sits in the pocket between X1, D6, D7 and
MH2's new position; every straight F segment to the web is
blocked and heal refuses (sealed pad). One wide-grid via relay:
F stub -> via -> buried run -> the web's existing vias at
(89.12,7.12) / (92.62,7.12). Exact-tested piece by piece
(fix_*.py pattern); first fully clean chain wins.
Run: xvfb-run -a python3 hw/fix_r44.py IN OUT
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import hand_stub
import hand_via
import repair
import repair6

MM = pcbnew.FromMM
ALL_LAYERS = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
              pcbnew.B_Cu}
NET = 'LED_PWR_K'

src, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
items = hand_stub.build_items(board)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
pad = {p.GetNumber(): p for p in fps['R44'].Pads()}['1']
centre = pad.GetPosition()
w = MM(0.2)

targets = []
for t in board.GetTracks():
    if t.GetNetname() == NET and t.Type() == pcbnew.PCB_VIA_T:
        targets.append(t.GetPosition())
print('web via targets:', [(round(pcbnew.ToMM(t.x), 2),
                             round(pcbnew.ToMM(t.y), 2))
                            for t in targets])

# via candidates around the pad, 0.25 grid to radius 5, near first
grid = []
n = int(5.0 / 0.25)
for ix in range(-n, n + 1):
    for iy in range(-n, n + 1):
        dx, dy = ix * 0.25, iy * 0.25
        d2 = dx * dx + dy * dy
        if d2 < 0.64 or d2 > 25.0:
            continue
        grid.append((d2, centre.x + MM(dx), centre.y + MM(dy)))
grid.sort()
done = False
tried_relays = 0
for _d2, vx, vy in grid:
    v1 = pcbnew.VECTOR2I(int(vx), int(vy))
    sh = pcbnew.SHAPE_SEGMENT(centre, v1, w)
    if not hand_stub.stub_ok(items, NET, sh, {pcbnew.F_Cu}, 0.0):
        continue
    disc = pcbnew.SHAPE_SEGMENT(v1, v1, MM(0.6))
    if not hand_via.ok(items, NET, disc, ALL_LAYERS, 0.0):
        continue
    for v2 in targets:
        for lr in (pcbnew.In2_Cu, pcbnew.In1_Cu, pcbnew.B_Cu):
            sh2 = pcbnew.SHAPE_SEGMENT(v1, v2, w)
            tried_relays += 1
            if not hand_stub.stub_ok(items, NET, sh2, {lr}, 0.0):
                continue
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(centre)
            t.SetEnd(v1)
            t.SetWidth(w)
            t.SetLayer(pcbnew.F_Cu)
            t.SetNet(board.FindNet(NET))
            board.Add(t)
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(v1)
            v.SetWidth(MM(0.6))
            v.SetDrill(MM(0.3))
            v.SetNet(board.FindNet(NET))
            board.Add(v)
            t2 = pcbnew.PCB_TRACK(board)
            t2.SetStart(v1)
            t2.SetEnd(v2)
            t2.SetWidth(w)
            t2.SetLayer(lr)
            t2.SetNet(board.FindNet(NET))
            board.Add(t2)
            print(f"relay placed: via at ({pcbnew.ToMM(v1.x):.2f},"
                  f"{pcbnew.ToMM(v1.y):.2f}), run on layer {lr} "
                  f"to web via ({pcbnew.ToMM(v2.x):.2f},"
                  f"{pcbnew.ToMM(v2.y):.2f})")
            done = True
            break
        if done:
            break
    if done:
        break
print('relays tried:', tried_relays)
groups = repair.compute_groups(board)
print(NET, 'groups after:', len(groups.get(NET, [])))
if done:
    repair6.save_checkpoint(board, out)
    print('saved', out)
else:
    print('NO RELAY FOUND — net stays owed')
    sys.exit(2)
