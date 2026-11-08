"""t_ai3: rip items named by specs from a board copy and save.
Usage: t_ai3_rip.py SRC OUT spec[;spec...]
spec = via:NET:x:y | seg:NET:x:y | pad:NET:x:y
A seg spec removes every seg of NET having an endpoint at (x,y)
(a chain is ripped by naming each joint). Vias matched by centre.
All netcodes captured BEFORE any Remove() (the net-name map dies
after a removal - standing tooling law)."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

SRC, OUT = sys.argv[1], sys.argv[2]
specs = []
for s in sys.argv[3].split(';'):
    k, n, x, y = s.split(':')
    specs.append((k, n, float(x), float(y)))

board = pcbnew.LoadBoard(SRC)
codes = {}
for name in {s[1] for s in specs}:
    codes[name] = board.GetNetcodeFromNetname(name)
print('netcodes captured:', codes)

def hit(t, spec):
    kind, net, x, y = spec
    if t.GetNetname() != net:
        return False
    if kind == 'via':
        if not isinstance(t, pcbnew.PCB_VIA):
            return False
        p = pcbnew.ToMM(t.GetPosition())
        return abs(p[0] - x) < 0.01 and abs(p[1] - y) < 0.01
    if kind == 'seg':
        if isinstance(t, pcbnew.PCB_VIA):
            return False
        a = pcbnew.ToMM(t.GetStart())
        b = pcbnew.ToMM(t.GetEnd())
        return (abs(a[0] - x) < 0.01 and abs(a[1] - y) < 0.01) or \
            (abs(b[0] - x) < 0.01 and abs(b[1] - y) < 0.01)
    return False

victims = [t for t in board.GetTracks()
           if any(hit(t, s) for s in specs)]
print(f'ripping {len(victims)} tracks')
for t in victims:
    board.Remove(t)
board.Save(OUT)
print('saved', OUT)
