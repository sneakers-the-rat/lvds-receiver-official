import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
FULL = (-50.0, 200.0, -100.0, 100.0)
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
for net in ('ULPI_STP', 'XI', 'USB_RST', 'DM_PHY', 'ULPI_DIR', 'ULPI_CK'):
    fs = fragments(net, FULL)
    print(net, 'fragments:', len(fs), [len(f['items']) for f in fs],
          'terms:', [f['terms'] for f in fs], flush=True)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
for ref in ('C20', 'C22', 'X1', 'U5', 'C28'):
    for fp in b.GetFootprints():
        if fp.GetReference() == ref:
            bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            print(ref, 'pos', (round(fp.GetPosition().x / 1e6, 3),
                               round(fp.GetPosition().y / 1e6, 3)),
                  'court', (round(bb.GetLeft() / 1e6, 2),
                            round(bb.GetTop() / 1e6, 2),
                            round(bb.GetRight() / 1e6, 2),
                            round(bb.GetBottom() / 1e6, 2)), flush=True)
            for p in fp.Pads():
                print('   pad', p.GetNumber(), p.GetNetname(),
                      (round(p.GetPosition().x / 1e6, 3),
                       round(p.GetPosition().y / 1e6, 3)),
                      (round(p.GetSize().x / 1e6, 3),
                       round(p.GetSize().y / 1e6, 3)), flush=True)
print('== items (73,80,15.5,21) all layers:', flush=True)
for l in range(3):
    for it in pool[l]:
        d = it[2]
        if 73 < d[0] < 80 and 15.5 < d[1] < 21:
            print('  ', 'FIB'[l], L.fmt_it(it), flush=True)
