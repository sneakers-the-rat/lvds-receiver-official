import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew
from repairg import save_checkpoint
mm = lambda v: round(v/1e6, 3)
board = pcbnew.LoadBoard(sys.argv[1])
victim = None
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != 'GND': continue
    s, e = t.GetStart(), t.GetEnd()
    if (mm(s.x), mm(s.y)) == (22.645, -1.5) or (mm(s.x), mm(s.y)) == (22.64, -1.5):
        victim = t
assert victim is not None, 'stub not found'
board.Remove(victim)
save_checkpoint(board, sys.argv[2])
print('removed C29.2 stub, saved', sys.argv[2])
