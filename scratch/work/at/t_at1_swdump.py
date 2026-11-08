"""t_at1: dump all tracks/vias/pads in SW box from a board, grouped by net+layer."""
import wx
_app = wx.App(False)
import pcbnew, sys
from collections import defaultdict

SRC = sys.argv[1] if len(sys.argv) > 1 else 'hw/pdlvds_rx.exp241esc.kicad_pcb'
X0, X1, Y0, Y1 = 62.0, 73.0, -4.0, 8.0
LAY = {0: 'F', 1: 'In2', 2: 'B'}
# KiCad layer ids: F_Cu=0, In2_Cu=... use GetLayerName
def lname(lid):
    return {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}.get(lid, str(lid))

board = pcbnew.LoadBoard(SRC)
out = defaultdict(list)
for tr in board.GetTracks():
    if isinstance(tr, pcbnew.PCB_VIA):
        x, y = pcbnew.ToMM(tr.GetPosition().x), pcbnew.ToMM(tr.GetPosition().y)
        if X0 <= x <= X1 and Y0 <= y <= Y1:
            out[(tr.GetNetname(), 'via')].append(
                f"via ({x:.3f},{y:.3f}) d{pcbnew.ToMM(tr.GetWidth()):.2f} dr{pcbnew.ToMM(tr.GetDrill()):.2f}")
    else:
        sx, sy = pcbnew.ToMM(tr.GetStart().x), pcbnew.ToMM(tr.GetStart().y)
        ex, ey = pcbnew.ToMM(tr.GetEnd().x), pcbnew.ToMM(tr.GetEnd().y)
        if (X0 <= sx <= X1 and Y0 <= sy <= Y1) or (X0 <= ex <= X1 and Y0 <= ey <= Y1):
            out[(tr.GetNetname(), lname(tr.GetLayer()))].append(
                f"({sx:.3f},{sy:.3f})->({ex:.3f},{ey:.3f}) w{pcbnew.ToMM(tr.GetWidth()):.2f}")
for fp in board.GetFootprints():
    for pad in fp.Pads():
        x, y = pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)
        if X0 <= x <= X1 and Y0 <= y <= Y1:
            out[(pad.GetNetname(), 'pad')].append(
                f"{fp.GetReference()}.{pad.GetNumber()} ({x:.3f},{y:.3f}) "
                f"{pcbnew.ToMM(pad.GetSize().x):.2f}x{pcbnew.ToMM(pad.GetSize().y):.2f}")
for k in sorted(out):
    print(f"== {k[0]} [{k[1]}] x{len(out[k])}")
    for s in sorted(out[k]):
        print('   ', s)
