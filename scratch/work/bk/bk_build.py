#!/usr/bin/env python3
"""bk build: exp257 -> exp258 candidate, applying bk_lib RIPS + ADDS via
build_lib.Surgery (collect-then-remove, refill, save, reload census diff)."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bk')
import build_lib as BL
import bk_lib as L

SRC = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
DST = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp258.kicad_pcb'
LAY = {'F': BL.F, 'In1': BL.IN1, 'In2': BL.IN2, 'B': BL.B}
DRILL = {0.4: 0.20, 0.5: 0.30, 0.6: 0.30}  # board setup min hole = 0.30

nets = sorted({r[1] for r in L.RIPS} | {it.net for _, it in L.ADDS})
print('nets:', nets)
S = BL.Surgery(SRC, DST, nets=tuple(nets))

# ---- rips: find ALL matches first, then remove ----
victims = []
for kind, net, layer, a, b in L.RIPS:
    if kind == 'via':
        nc = S.NC[net]
        hits = [t for t in S.b.GetTracks()
                if t.GetNetCode() == nc and t.Type() == BL.pcbnew.PCB_VIA_T
                and S._near((BL._mm(t.GetPosition().x), BL._mm(t.GetPosition().y)), a)]
        assert len(hits) >= 1, f'rip via {net}@{a}: {len(hits)} hits'
        print(f'rip via {net}@{a}: {len(hits)}')
        victims += hits
    else:
        def pred(t, a=a, b=b):
            s, e = S.ends(t)
            return (S._near(s, a) and S._near(e, b)) or (S._near(s, b) and S._near(e, a))
        hits = S.find_tracks(net, LAY[layer], pred)
        assert len(hits) >= 1, f'rip trk {net}[{layer}] {a}->{b}: {len(hits)} hits'
        print(f'rip trk {net}[{layer}] {a}->{b}: {len(hits)}')
        victims += hits
S.remove(victims)

# ---- adds ----
for label, it in L.ADDS:
    if it.kind == 'via':
        dia = round(it.hw * 2, 3)
        S.add_via(it.net, it.a[0], it.a[1], dia=dia, drill=DRILL[dia])
    else:
        S.add_track(it.net, LAY[it.layer], it.a, it.b, round(it.hw * 2, 3))
print(f'adds applied: {len(L.ADDS)}')

diffs = S.finish()
print('census diffs:', len(diffs))
