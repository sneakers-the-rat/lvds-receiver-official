#!/usr/bin/env python3
"""D8 stage 2: move D8 to (66.50, 12.35) per d8_scan (worst modelled
clearance 0.230, courtyards clear R46/C16); re-lay the BIST_DRV feed
(its via moves north out of the new pad); BIST_A stub chain already
lands inside the new pad 2 - untouched. Zone refill at the end."""
import pcbnew, wx
_app = wx.App(False)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp276.kicad_pcb')
FCU = b.GetLayerID('F.Cu'); IN2 = b.GetLayerID('In2.Cu')
MM = 1e6
def P(x, y): return pcbnew.VECTOR2I(int(x*MM), int(y*MM))
def near(p, x, y, tol=0.011):
    return abs(p.x/MM - x) < tol and abs(p.y/MM - y) < tol

d8 = b.FindFootprintByReference('D8')
d8.SetPosition(P(66.50, 12.35))
print('D8 moved to (66.50, 12.35)')

# find BIST_DRV items at the old via point (65.38, 11.88)
rip, via_info, in2_far = [], None, None
for t in list(b.GetTracks()):
    if t.GetNetname() != 'BIST_DRV':
        continue
    s, e = t.GetStart(), t.GetEnd()
    if t.Type() == pcbnew.PCB_VIA_T:
        if near(s, 65.38, 11.88):
            via_info = (t.GetWidth()/MM, t.GetDrill()/MM)
            rip.append(t)
    elif t.GetLayer() == FCU:
        if (near(s, 64.85, 12.00) or near(e, 64.85, 12.00) or
                near(s, 65.38, 11.88) or near(e, 65.38, 11.88)):
            rip.append(t)
    elif t.GetLayer() == IN2:
        if near(s, 65.38, 11.88) or near(e, 65.38, 11.88):
            in2_far = (e if near(s, 65.38, 11.88) else s)
            in2_w = t.GetWidth()/MM
            rip.append(t)
assert via_info and in2_far is not None, (via_info, in2_far)
print('ripping %d BIST_DRV items; via dia/drill %s; In2 far joint (%.2f, %.2f) w %.2f'
      % (len(rip), via_info, in2_far.x/MM, in2_far.y/MM, in2_w))
for t in rip:
    b.Remove(t)

net = b.FindNet('BIST_DRV')
via = pcbnew.PCB_VIA(b)
via.SetPosition(P(65.38, 10.55))
via.SetWidth(int(via_info[0]*MM)); via.SetDrill(int(via_info[1]*MM))
via.SetLayerPair(FCU, b.GetLayerID('B.Cu'))
via.SetNet(net)
b.Add(via)
def add_track(x1, y1, x2, y2, layer, w):
    tr = pcbnew.PCB_TRACK(b)
    tr.SetStart(P(x1, y1)); tr.SetEnd(P(x2, y2))
    tr.SetLayer(layer); tr.SetWidth(int(w*MM)); tr.SetNet(net)
    b.Add(tr)
add_track(65.20, 11.50, 65.38, 10.55, FCU, 0.20)
add_track(65.38, 10.55, in2_far.x/MM, in2_far.y/MM, IN2, in2_w)
print('new BIST_DRV via (65.38, 10.55) + F stub + In2 leg added')

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp276.kicad_pcb')
print('refilled + saved exp276')
