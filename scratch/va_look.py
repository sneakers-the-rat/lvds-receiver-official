import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
import repair
mm = lambda v: round(v/1e6, 2)
b = pcbnew.LoadBoard('scratch/exp182cand.kicad_pcb')
groups = repair.compute_groups(b).get('+VA', [])
print(f'+VA copper groups: {len(groups)}')
for g in groups:
    pads = [it.desc for it in g if it.kind == 'pad']
    pos = []
    for it in g:
        if it.kind == 'pad':
            pos.append(it.desc)
    print(f'  group items={len(g)} pads={pads}')
print('--- +VA pads and positions:')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() == '+VA':
            p = pcbnew.ToMM(pad.GetPosition())
            print(f'   {fp.GetReference()}.{pad.GetNumber()} @({mm(p.x)},{mm(p.y)})')
print('--- +VA zones:')
for z in b.Zones():
    if z.GetNetname() == '+VA':
        print('   zone layers:', [z.GetLayerName(l) for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if z.IsOnLayer(l)])
