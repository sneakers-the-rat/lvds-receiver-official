"""t_ba24a: decisive courtyard probe for C22 at (77.5,9.7)
rot 270 -- build a copy, SAVE, RELOAD, run check_pcb's
courtyard_pairs on the reloaded file (the production path).
Also probe (77.5,9.7) rot 90 and two alternates."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from check_pcb import courtyard_pairs

MM = 1e6
SRC = 'hw/pdlvds_rx.exp252.kicad_pcb'


def probe(cx, cy, rot, tag):
    b = pcbnew.LoadBoard(SRC)
    for fp in b.GetFootprints():
        if fp.GetReference() == 'C22':
            fp.SetPosition(pcbnew.VECTOR2I(int(cx * MM), int(cy * MM)))
            fp.SetOrientationDegrees(rot)
    out = f'scratch/work/ba/probe_{tag}.kicad_pcb'
    b.Save(out)
    b2 = pcbnew.LoadBoard(out)
    pairs, blind = courtyard_pairs(b2)
    mine = [p for p in pairs if 'C22' in p]
    print(f'{tag} C22 at ({cx},{cy}) rot {rot}: total pairs '
          f'{len(pairs)}, C22 pairs {mine}, blind {blind}')
    return mine


probe(77.5, 9.7, 270, 'n270')
probe(77.5, 9.7, 90, 'n90')
probe(76.85, 9.6, 180, 'n2')
probe(72.5, 18.0, 0, 'ctrl')
print('=== done ===')
