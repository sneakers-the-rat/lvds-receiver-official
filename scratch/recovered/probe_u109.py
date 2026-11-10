import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM, TM = pcbnew.FromMM, pcbnew.ToMM

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp14.kicad_pcb')
items = build_items(board)
# U10.9 at (16.15,-15.50), half (0.72,0.15); necks east/west dv 0.55..1.5
px, py, hx = 16.15, -15.50, 0.72
for ang, (ca, sa) in (('E', (1.0, 0.0)), ('W', (-1.0, 0.0))):
    startd = max(hx - 0.08, 0.25 * hx)
    sx, sy = px + startd * ca, py
    vx, vy = px + 1.0 * ca, py
    neck = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(sx), MM(sy)),
                                pcbnew.VECTOR2I(MM(vx), MM(vy)), MM(0.25))
    print(f'--- U10.9 neck {ang} ({sx:.2f},{sy:.2f})->({vx:.2f},{vy:.2f}):')
    for kind, n2, l2, s2, desc in items:
        if n2 == 'HV_SHDN':
            continue
        shared = {pcbnew.F_Cu} & l2
        if not shared:
            continue
        need = need_for('HV_SHDN', n2, shared)
        if neck.Collide(s2, MM(need - 0.001)):
            print(f'    {kind} {n2} {desc}')
# any +5V pads near (17.5,-15.5)?
print('--- pads with net +5V within 3 mm of (17.5,-15.5):')
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() != '+5V':
            continue
        p = pad.GetPosition()
        if abs(TM(p.x) - 17.5) < 3 and abs(TM(p.y) + 15.5) < 3:
            print(f'    {fp.GetReference()}.{pad.GetNumber()} @({TM(p.x):.2f},{TM(p.y):.2f})')
