"""t_ba13: probe C23 candidate sites with check_pcb's own
courtyard_pairs(). Baseline first (expect 0 gated pairs, blind
SH1-only), then for each candidate centre/rot: move C23 in a
fresh in-memory load, re-run, report pairs involving C23."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from check_pcb import courtyard_pairs

MM = 1e6
SRC = 'hw/pdlvds_rx.exp252.kicad_pcb'


def probe(cx, cy, rot):
    b = pcbnew.LoadBoard(SRC)
    for fp in b.GetFootprints():
        if fp.GetReference() == 'C23':
            fp.SetPosition(pcbnew.VECTOR2I(int(cx * MM), int(-cy * MM)))
            fp.SetOrientationDegrees(rot)
    pairs, blind = courtyard_pairs(b)
    mine = [p for p in pairs if 'C23' in p]
    return pairs, mine


b0 = pcbnew.LoadBoard(SRC)
pairs0, blind0 = courtyard_pairs(b0)
print(f'baseline: gated pairs {len(pairs0)}, blind {len(blind0)}')
for p in pairs0[:6]:
    print('   pair:', p)
refs = set()
for p in blind0:
    refs.add(p[0])
    refs.add(p[1])
print('   blind refs:', sorted(refs))

for (cx, cy, rot) in [(70.75, 14.75, 180), (68.5, 10.5, 0),
                      (67.5, 12.0, 0), (69.0, 9.0, 0), (70.0, 17.0, 0),
                      (66.0, 14.75, 0), (68.8, 14.75, 0)]:
    pairs, mine = probe(cx, cy, rot)
    print(f'site ({cx},{cy}) rot {rot}: total pairs {len(pairs)}, '
          f'C23 pairs {mine}')
print('=== done ===')
