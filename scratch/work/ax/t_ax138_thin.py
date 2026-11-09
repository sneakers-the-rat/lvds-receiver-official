import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
bv = [it for it in pool[2] if it[1] == '+3V3A' and it[0] == 'seg'
      and abs(it[2][0] - 73.625) < 0.01 and abs(it[2][2] - 73.625) < 0.01]
print('B vertical segs:', [L.fmt_it(i) for i in bv], flush=True)
rip_items(bv)
add_items({2: [('seg', '+3V3A', (73.625, 8.625, 73.625, 10.625, 0.10),
                0.25)], 0: [], 1: []})
via = {l: [('via', 'GND', (72.9, 9.45, 0.25), 0.2)] for l in range(3)}
worst = (9.9, None, None)
for l in range(3):
    for it in via[l]:
        for o in pool[l]:
            if o[1] == 'GND':
                continue
            m = item_margin(l, it, [o])
            if m < worst[0]:
                worst = (m, it, o)
print('stitch via (72.9,9.6) gate worst', f"{worst[0]:+.3f}",
      'vs', L.fmt_it(worst[2]), flush=True)
if worst[0] < -0.001:
    print('ABORT')
    sys.exit(0)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
MM = 1000000
def V(x, y):
    return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
def mm(v):
    return (v.x / MM, v.y / MM)
victims = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_TRACK) and not isinstance(t, pcbnew.PCB_VIA) \
            and t.GetNetname() == '+3V3A' and t.GetLayer() == pcbnew.B_Cu:
        s, e = mm(t.GetStart()), mm(t.GetEnd())
        if abs(s[0] - 73.625) < 0.01 and abs(e[0] - 73.625) < 0.01 \
                and 8.0 < s[1] < 11.0 and 8.0 < e[1] < 11.0:
            victims.append(t)
print('board B vertical victims:', len(victims))
assert len(victims) == len(bv)
for t in victims:
    b.Remove(t)
nc3 = b.GetNetcodeFromNetname('+3V3A')
t = pcbnew.PCB_TRACK(b)
t.SetStart(V(73.625, 8.625))
t.SetEnd(V(73.625, 10.625))
t.SetLayer(pcbnew.B_Cu)
t.SetWidth(200000)
t.SetNetCode(nc3)
b.Add(t)
nc = b.GetNetcodeFromNetname('GND')
t = pcbnew.PCB_VIA(b)
t.SetPosition(V(72.9, 9.45))
t.SetWidth(500000)
t.SetDrill(300000)
t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
t.SetViaType(pcbnew.VIATYPE_THROUGH)
t.SetNetCode(nc)
b.Add(t)
for fp in b.GetFootprints():
    if fp.GetReference() == 'C23':
        for f in fp.Fields():
            if f.GetName() == 'Reference':
                f.SetPosition(V(67.3, 16.9))
                print('C23 refdes -> (67.3,16.9)')
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp250.kicad_pcb')
print('saved')
