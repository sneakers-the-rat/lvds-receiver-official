import sys, math
sys.path.insert(0, 'scratch/work/ax')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp251.kicad_pcb')

def mm(v):
    return (v.x / 1e6, v.y / 1e6)

LAY = {'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
spurs = [((71.5, -3.3), 'In2'), ((74.0, -1.0), 'In2'),
         ((69.6, -3.6), 'In2'), ((77.45, 8.2), 'B'),
         ((75.85, 10.1), 'B'), ((78.25, 9.2), 'B')]

def endpoint_degree(e, layer, skip):
    deg = 0
    sk = (skip.GetLayer(), mm(skip.GetStart()), mm(skip.GetEnd()))
    for o in b.GetTracks():
        if o.GetNetname() != 'ULPI_STP':
            continue
        if not isinstance(o, pcbnew.PCB_VIA) and \
                (o.GetLayer(), mm(o.GetStart()), mm(o.GetEnd())) == sk:
            continue  # the candidate itself (post-dedupe: unique)
        if isinstance(o, pcbnew.PCB_VIA):
            if math.hypot(mm(o.GetPosition())[0] - e[0],
                          mm(o.GetPosition())[1] - e[1]) < 0.011:
                deg += 1
        elif o.GetLayer() == layer:
            for oe in (mm(o.GetStart()), mm(o.GetEnd())):
                if math.hypot(oe[0] - e[0], oe[1] - e[1]) < 0.011:
                    deg += 1
    return deg

victims = []
for (px, py), ln in spurs:
    cand = []
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
            continue
        if t.GetNetname() != 'ULPI_STP' or t.GetLayer() != LAY[ln]:
            continue
        if t.GetLength() / 1e6 > 0.0751 + 1e-9:
            continue
        s, e = mm(t.GetStart()), mm(t.GetEnd())
        if min(math.hypot(s[0] - px, s[1] - py),
               math.hypot(e[0] - px, e[1] - py)) >= 0.06:
            continue
        degs = (endpoint_degree(s, LAY[ln], t),
                endpoint_degree(e, LAY[ln], t))
        if sorted(degs) == [0, 2] or sorted(degs) == [0, 1]:
            cand.append((t, degs))
    assert len(cand) == 1, ((px, py), ln, len(cand))
    print(f'spur at {(px, py)} {ln}: degs {cand[0][1]}', flush=True)
    victims.append(cand[0][0])
for t in victims:
    b.Remove(t)
print('spurs removed:', len(victims), flush=True)
b.Save('hw/pdlvds_rx.exp251.kicad_pcb')
print('saved exp251 v4 (spurs)', flush=True)
