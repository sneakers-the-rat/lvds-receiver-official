"""t_at4: dump B-layer (and optionally F) items in a box from exp241esc."""
import wx
_app = wx.App(False)
import pcbnew, sys
from collections import defaultdict

SRC = 'hw/pdlvds_rx.exp241esc.kicad_pcb'
X0, X1, Y0, Y1 = 64.0, 73.0, -9.0, 2.0
board = pcbnew.LoadBoard(SRC)
out = defaultdict(list)
for tr in board.GetTracks():
    if isinstance(tr, pcbnew.PCB_VIA):
        x, y = pcbnew.ToMM(tr.GetPosition().x), pcbnew.ToMM(tr.GetPosition().y)
        if X0 <= x <= X1 and Y0 <= y <= Y1:
            out[(tr.GetNetname(), 'via')].append(
                f"via ({x:.3f},{y:.3f}) d{pcbnew.ToMM(tr.GetWidth()):.2f}")
    elif tr.GetLayer() == pcbnew.B_Cu:
        sx, sy = pcbnew.ToMM(tr.GetStart().x), pcbnew.ToMM(tr.GetStart().y)
        ex, ey = pcbnew.ToMM(tr.GetEnd().x), pcbnew.ToMM(tr.GetEnd().y)
        if (X0 <= sx <= X1 and Y0 <= sy <= Y1) or (X0 <= ex <= X1 and Y0 <= ey <= Y1):
            out[(tr.GetNetname(), 'B')].append(
                f"({sx:.3f},{sy:.3f})->({ex:.3f},{ey:.3f}) w{pcbnew.ToMM(tr.GetWidth()):.2f}")
for k in sorted(out):
    print(f"== {k[0]} [{k[1]}] x{len(out[k])}")
    for s in sorted(out[k]):
        print('   ', s)
