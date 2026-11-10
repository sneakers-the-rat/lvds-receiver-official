import sys, math
sys.path.insert(0, 'scratch/work/ax')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp251.kicad_pcb')

def mm(v):
    return (v.x / 1e6, v.y / 1e6)

stp_pads = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == 'ULPI_STP':
            stp_pads.append((mm(p.GetPosition()),
                             (p.GetSize().x / 2e6, p.GetSize().y / 2e6)))
print('STP pads:', stp_pads, flush=True)

def anchored(e, layer, skip_key):
    for o in b.GetTracks():
        if o.GetNetname() != 'ULPI_STP':
            continue
        if isinstance(o, pcbnew.PCB_VIA):
            if math.hypot(mm(o.GetPosition())[0] - e[0],
                          mm(o.GetPosition())[1] - e[1]) < 0.011:
                return True
        else:
            if (o.GetLayer(), mm(o.GetStart()), mm(o.GetEnd())) == skip_key:
                continue
            if o.GetLayer() != layer:
                continue
            for oe in (mm(o.GetStart()), mm(o.GetEnd())):
                if math.hypot(oe[0] - e[0], oe[1] - e[1]) < 0.011:
                    return True
    for (cx, cy), (hw, hh) in stp_pads:
        if abs(e[0] - cx) <= hw + 0.01 and abs(e[1] - cy) <= hh + 0.01:
            return True
    return False

JOINTS = [(71.5, -3.3), (74.0, -1.0), (69.65, -3.6), (77.45, 8.2),
          (75.8, 10.15), (78.3, 9.2)]
total = 0
for it in range(40):
    victim = None
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        if t.GetNetname() != 'ULPI_STP':
            continue
        if t.GetLength() / 1e6 > 0.3:
            continue
        s, e = mm(t.GetStart()), mm(t.GetEnd())
        near = any(math.hypot(s[0] - jx, s[1] - jy) < 0.65 or
                   math.hypot(e[0] - jx, e[1] - jy) < 0.65
                   for jx, jy in JOINTS)
        if not near:
            continue
        key = (t.GetLayer(), s, e)
        if not anchored(s, t.GetLayer(), key) or \
                not anchored(e, t.GetLayer(), key):
            victim = (t, s, e)
            break
    if victim is None:
        break
    t, s, e = victim
    print(f'iter {it}: deleting spur {s} -> {e} layer {t.GetLayer()}',
          flush=True)
    b.Remove(t)
    total += 1
print('total spurs deleted:', total, flush=True)
b.Save('hw/pdlvds_rx.exp251.kicad_pcb')
print('saved exp251 v5 (spur loop)', flush=True)
