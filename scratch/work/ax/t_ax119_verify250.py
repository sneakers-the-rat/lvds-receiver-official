import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
FULL = (-50.0, 200.0, -100.0, 100.0)
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for net, box in (('PHY_1V8A', FULL), ('XO', FULL), ('+3V3D', FULL),
                 ('GND', (67.0, 73.0, 9.0, 15.5))):
    fs = fragments(net, box)
    print(net, 'fragments:', len(fs),
          'sizes:', [len(f['items']) for f in fs], flush=True)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
for ref in ('C16', 'C23'):
    for fp in b.GetFootprints():
        if fp.GetReference() == ref:
            for p in fp.Pads():
                print(ref, 'pad', p.GetNumber(), p.GetNetname(),
                      (round(p.GetPosition().x / 1e6, 3),
                       round(p.GetPosition().y / 1e6, 3)), flush=True)
            print(ref, 'refdes at',
                  (round(fp.GetReferenceText().GetPosition().x / 1e6, 2),
                   round(fp.GetReferenceText().GetPosition().y / 1e6, 2)),
                  flush=True)
n = 0
for l in range(3):
    n += sum(1 for it in pool[l] if it[1] == 'PHY_1V8A')
print('PHY items total:', n, flush=True)
