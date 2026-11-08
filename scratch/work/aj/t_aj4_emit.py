"""t_aj4: emit segs/vias named by specs into a board copy and save.
Usage: t_aj4_emit.py SRC OUT spec[;spec...]
spec = via:NET:x:y:dia:drill | seg:NET:L:x1:y1:x2:y2:w  (L in F/In2/B)
Netcodes captured before any Add (same discipline as the rip tool).
No zone refill here -- callers refill before refereeing."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

SRC, OUT = sys.argv[1], sys.argv[2]
specs = [s.split(':') for s in sys.argv[3].split(';') if s.strip()]
board = pcbnew.LoadBoard(SRC)
codes = {}
for sp in specs:
    if sp[1] not in codes:
        codes[sp[1]] = board.GetNetcodeFromNetname(sp[1])
print('netcodes captured:', codes)
KLAY = {'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
MM = pcbnew.FromMM
for sp in specs:
    if sp[0] == 'via':
        _, net, x, y, dia, drill = sp
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(float(x)), MM(float(y))))
        v.SetWidth(MM(float(dia)))
        v.SetDrill(MM(float(drill)))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetNetCode(codes[net])
        board.Add(v)
        print(f'via {net} ({x},{y}) d{dia} drill{drill}')
    else:
        _, net, lay, x1, y1, x2, y2, w = sp
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(float(x1)), MM(float(y1))))
        t.SetEnd(pcbnew.VECTOR2I(MM(float(x2)), MM(float(y2))))
        t.SetWidth(MM(float(w)))
        t.SetLayer(KLAY[lay])
        t.SetNetCode(codes[net])
        board.Add(t)
        print(f'seg {net} {lay} ({x1},{y1})->({x2},{y2}) w{w}')
board.Save(OUT)
print('saved', OUT)
