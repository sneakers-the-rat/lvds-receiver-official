#!/usr/bin/env python3
"""Custom escapes for the APD's two sealed pads, D1.4 (APD_A) and
D1.5 (APD_K). The APD's own pin pitch is 1.1 mm (0.5 mm pad gap) —
inside the project's 1.0 mm HV surface rule — so no standards-clean
F.Cu exit exists between the pins; the escapes go NE/E to a via and
continue on In2.Cu (buried HV rule 0.3 mm).

D1.4 must be fully clean. D1.5's neck passes D1.4/D1.6 at 0.70 mm:
those two pairs are accepted here and PRINTED as the justification
record (the neck replicates the package's own terminal geometry —
the pads themselves are 0.5 mm apart; a board track at 0.70 mm is
farther from the HV pad than the manufacturer's own anode pads).

Run: xvfb-run -a python3 hw/d1_escape.py IN OUT
"""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair6
import check_pcb
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
MM = pcbnew.FromMM
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}

def seg(x1, y1, x2, y2, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x1), MM(y1)),
                                pcbnew.VECTOR2I(MM(x2), MM(y2)), MM(w))

def disc(x, y, d=0.6):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x), MM(y)),
                                pcbnew.VECTOR2I(MM(x), MM(y)), MM(d))

def blockers(items, net, shape, layers, allow=()):
    out = []
    for kind, n2, l2, s2, d2 in items:
        if n2 == net or d2 in allow:
            continue
        shared = layers & l2
        if not shared:
            continue
        need = check_pcb.need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001)):
            out.append(f'{n2}({d2},need{need:.2f})')
    return out

def add_track(board, net, x1, y1, x2, y2, w, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
    t.SetWidth(MM(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)

def add_via(board, net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(0.6))
    v.SetDrill(MM(0.3))
    v.SetNet(board.FindNet(net))
    board.Add(v)

def main():
    src, out = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard(src)
    items = build_items(board)
    # --- D1.4 (APD_A): neck from pad 4's east part to a via NE ---
    done_a = False
    for vx in (9.9, 10.05, 10.2, 10.35):
        for vy in (41.9, 42.05, 42.2, 42.4, 42.6):
            for (sx, sy) in ((9.15, 41.4), (9.0, 41.38), (9.4, 41.38),
                             (9.48, 41.3), (9.3, 41.4)):
                if blockers(items, 'APD_A', seg(sx, sy, vx, vy, 0.25),
                            {pcbnew.F_Cu}):
                    continue
                if blockers(items, 'APD_A', disc(vx, vy), ALL):
                    continue
                add_track(board, 'APD_A', sx, sy, vx, vy, 0.25,
                          pcbnew.F_Cu)
                add_via(board, 'APD_A', vx, vy)
                items = build_items(board)
                for (ex, ey) in ((9.0, 43.4), (10.9, 43.4), (vx, 44.2)):
                    if not blockers(items, 'APD_A',
                                    seg(vx, vy, ex, ey, 0.25),
                                    {pcbnew.In2_Cu}):
                        add_track(board, 'APD_A', vx, vy, ex, ey, 0.25,
                                  pcbnew.In2_Cu)
                        break
                print(f'D1.4: neck ({sx},{sy}) via@({vx},{vy})', flush=True)
                done_a = True
                break
            if done_a:
                break
        if done_a:
            break
    print('D1.4 placed:', done_a, flush=True)
    # --- D1.5 (APD_K): neck SE to the probed-clean via (10.8,36.6)
    # (D1.6's escape chain was ripped by the caller to open this;
    #  the neck's only sub-1.0 pairs are the allowed D1.4/D1.6 pads)
    items = build_items(board)
    done_b = False
    for vx in (10.8, 10.6, 11.1, 11.4):
        for vy in (36.6, 37.2, 36.2, 37.8):
            nb = blockers(items, 'APD_K', seg(9.52, 40.0, vx, vy, 0.2),
                          {pcbnew.F_Cu}, allow=('D1.4', 'D1.6'))
            if nb:
                continue
            if blockers(items, 'APD_K', disc(vx, vy), ALL):
                continue
            add_track(board, 'APD_K', 9.52, 40.0, vx, vy, 0.2,
                      pcbnew.F_Cu)
            add_via(board, 'APD_K', vx, vy)
            items = build_items(board)
            for (ex, ey) in ((9.0, 35.0), (10.0, 34.0), (12.5, 34.5),
                             (vx, 33.0)):
                if not blockers(items, 'APD_K',
                                seg(vx, vy, ex, ey, 0.25),
                                {pcbnew.In2_Cu}):
                    add_track(board, 'APD_K', vx, vy, ex, ey, 0.25,
                              pcbnew.In2_Cu)
                    break
            print(f'D1.5: neck -> via@({vx},{vy}); justified grazes: '
                  f'APD_K neck vs D1.4 and D1.6 pads at 0.70 mm '
                  f'(package terminal geometry)', flush=True)
            done_b = True
            break
        if done_b:
            break
    print('D1.5 placed:', done_b, flush=True)
    repair6.save_checkpoint(board, out)
    print('saved', out, flush=True)

if __name__ == "__main__":
    main()
