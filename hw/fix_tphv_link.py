#!/usr/bin/env python3
"""Close TP_HV's In2 gap: hops2's In2 run ends at (44.46,-7.6) but
the via-up moved east to (44.9,-7.6) during the run (CMP_QN graze),
leaving a 0.14 mm gap -- TP_HV audits as 2 groups on exp35.
Add the In2 link segment (44.46,-7.6)->(44.9,-7.6), asserted.
Usage: xvfb-run -a python3 hw/fix_tphv_link.py <src> <out>
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MMf = pcbnew.FromMM
SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)

s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(44.46), MMf(-7.6)),
                         pcbnew.VECTOR2I(MMf(44.9), MMf(-7.6)),
                         MMf(0.25))
for kind, n2, l2, s2, desc in items:
    if n2 == 'TP_HV' or kind == 'zone':
        continue
    if pcbnew.In2_Cu not in l2:
        continue
    need = need_for('TP_HV', n2, {pcbnew.In2_Cu})
    assert not s.Collide(s2, MMf(need - 0.001)), \
        f'TP_HV In2 link blocked by {n2} {desc}'
t = pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(MMf(44.46), MMf(-7.6)))
t.SetEnd(pcbnew.VECTOR2I(MMf(44.9), MMf(-7.6)))
t.SetWidth(MMf(0.25))
t.SetLayer(pcbnew.In2_Cu)
t.SetNet(board.FindNet('TP_HV'))
board.Add(t)
print('TP_HV In2 link placed (44.46,-7.6)->(44.9,-7.6)')
board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')
