import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
MM, TM = pcbnew.FromMM, pcbnew.ToMM

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp14.kicad_pcb')
for net, (x, y) in (('HV_GATE', (17.30, -14.50)),
                    ('HV_INTVCC', (17.30, -15.00))):
    disc = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x), MM(y)),
                                pcbnew.VECTOR2I(MM(x), MM(y)), MM(0.6))
    need = check_pcb.need_for(net, '+5V', {pcbnew.F_Cu, pcbnew.In1_Cu,
                                           pcbnew.In2_Cu, pcbnew.B_Cu})
    print(f'--- blockers of {net} disc @({x},{y}), need {need}:')
    for t in board.GetTracks():
        if t.GetNetname() != '+5V':
            continue
        if disc.Collide(t.GetEffectiveShape(), MM(need - 0.001)):
            if t.Type() == pcbnew.PCB_VIA_T:
                p = t.GetPosition()
                print(f'    VIA @({TM(p.x):.3f},{TM(p.y):.3f})')
            else:
                s, e = t.GetStart(), t.GetEnd()
                print(f'    TRK L{t.GetLayer()} ({TM(s.x):.3f},{TM(s.y):.3f})'
                      f'->({TM(e.x):.3f},{TM(e.y):.3f}) w={TM(t.GetWidth()):.2f}')
