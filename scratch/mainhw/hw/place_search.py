#!/usr/bin/env python3
"""Find a clearance-clean home for a footprint near a target point.

Moves the footprint in-memory over a grid of candidate positions
(and both sides), testing its pads' exact shapes against every
other audit item with check_pcb.need_for (the audit's own test).
First clean candidate wins and is saved; the part's nets are left
disconnected for the healing repair to reconnect.

Run: xvfb-run -a python3 hw/place_search.py IN OUT REF CX CY [R]
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair6
import check_pcb
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
MM = pcbnew.FromMM

def pads_clean(fp, items):
    for pad in fp.Pads():
        net = pad.GetNetname()
        if not net:
            continue
        layers = {l for l in (pcbnew.F_Cu, pcbnew.In1_Cu,
                              pcbnew.In2_Cu, pcbnew.B_Cu)
                  if pad.IsOnLayer(l)}
        shape = pad.GetEffectiveShape()
        for kind, n2, l2, s2, d2 in items:
            if n2 == net:
                continue
            shared = layers & l2
            if not shared:
                continue
            need = check_pcb.need_for(net, n2, shared)
            if shape.Collide(s2, MM(need - 0.001)):
                return False
    return True

def main():
    src, out, ref = sys.argv[1], sys.argv[2], sys.argv[3]
    cx, cy = float(sys.argv[4]), float(sys.argv[5])
    rad = float(sys.argv[6]) if len(sys.argv) > 6 else 6.0
    board = pcbnew.LoadBoard(src)
    fp = [f for f in board.GetFootprints()
          if f.GetReference() == ref][0]
    orig_pos = fp.GetPosition()
    orig_flip = fp.IsFlipped()
    items = [it for it in build_items(board)
             if not it[4].startswith(ref + '.')]
    cands = []
    steps = [i * 0.5 for i in range(int(rad * 2) + 1)]
    for dx in steps:
        for dy in steps:
            for sx in (1, -1) if dx else (1,):
                for sy in (1, -1) if dy else (1,):
                    cands.append((cx + sx * dx, cy + sy * dy))
    cands.sort(key=lambda p: (abs(p[0] - cx) + abs(p[1] - cy)))
    for flip in (orig_flip, not orig_flip):
        for (x, y) in cands:
            if bool(flip) != bool(fp.IsFlipped()):
                fp.Flip(fp.GetPosition(), False)
            fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
            if pads_clean(fp, items):
                print(f'{ref}: clean home at ({x:.1f},{y:.1f}) '
                      f'flipped={fp.IsFlipped()}', flush=True)
                repair6.save_checkpoint(board, out)
                print('saved', out, flush=True)
                return
    fp.SetPosition(orig_pos)
    if bool(orig_flip) != bool(fp.IsFlipped()):
        fp.Flip(fp.GetPosition(), False)
    print(f'{ref}: NO CLEAN HOME in grid', flush=True)

if __name__ == "__main__":
    main()
