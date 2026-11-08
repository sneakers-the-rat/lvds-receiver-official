"""t_ao6: exp232 SE re-fan repair. The t_ao5 build banked HV_INTVCC
(DRC unconnected 13->12) but the inherited se_refan rejoin point
(31.375,-5.5) does not exist on exp231's SE chain -- the tail seg
dangles (DRC track_dangling 1) and the kept chain survives only via
an X-crossing with the re-fan's seg2. Repair: rip the dangling tail,
seg2, and the orphaned kept seg (32.125,-4.875)->(31.875,-4.625);
emit seg2' (32.0,-4.5)->(32.125,-4.875) landing on the real kept
joint. New seg gated in-model exact before emit; reload-verified."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, seg_margin, in_box_pool, apply_rip,
                      fmt_it)
from router import netclass

SRC, OUT = sys.argv[1], sys.argv[2]
BOX = (29.0, 34.6, -6.4, 1.5)
NEWSEG = ('+5V', 0, (32.000, -4.500), (32.125, -4.875), 0.6)
RIPS = [('seg', '+5V', 31.700, -5.100),    # tail (31.7,-5.1)->(31.375,-5.5)
        ('seg', '+5V', 32.000, -4.500),    # seg2 (32.0,-4.5)->(31.7,-5.1)
        ('seg', '+5V', 32.125, -4.875)]    # orphan (32.125,-4.875)->(31.875,-4.625)
# NOTE: spec (32.000,-4.500) also endpoint-matches seg1 J->(32.0,-4.5)
# and the NEW seg's start -- on the BOARD rip pass it would kill seg1
# too. Board rips below therefore match FULL endpoint pairs, not the
# single-point model specs.
BOARD_RIPS = [((31.700, -5.100), (31.375, -5.500)),
              ((32.000, -4.500), (31.700, -5.100)),
              ((32.125, -4.875), (31.875, -4.625))]

board0 = pcbnew.LoadBoard(SRC)
items = load_items(board0)
statics, nrip = apply_rip(items, RIPS)
print(f'model rips: {nrip}')
it2 = {li: list(statics[li]) for li in range(3)}
o = ('seg', NEWSEG[0], (NEWSEG[2][0], NEWSEG[2][1], NEWSEG[3][0],
                        NEWSEG[3][1], NEWSEG[4] / 2), netclass('+5V')[1])
it2[0].append(o)
pool = in_box_pool(it2, BOX, pad=1.2)
m, w = seg_margin(0, NEWSEG[2], NEWSEG[3], '+5V', NEWSEG[4] / 2,
                  pool[0])
print(f'new seg in-model gate: {m:+.3f} vs {fmt_it(w)}')
if m < -0.001:
    print('GATE FAILURE -- not building')
    sys.exit(1)

code = board0.GetNetcodeFromNetname('+5V')

def pair_hit(t, pair):
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != '+5V':
        return False
    a_ = pcbnew.ToMM(t.GetStart()); b_ = pcbnew.ToMM(t.GetEnd())
    (p, q) = pair
    return (abs(a_[0] - p[0]) < 0.01 and abs(a_[1] - p[1]) < 0.01
            and abs(b_[0] - q[0]) < 0.01 and abs(b_[1] - q[1]) < 0.01) \
        or (abs(a_[0] - q[0]) < 0.01 and abs(a_[1] - q[1]) < 0.01
            and abs(b_[0] - p[0]) < 0.01 and abs(b_[1] - p[1]) < 0.01)

victims = [t for t in board0.GetTracks()
           if any(pair_hit(t, pr) for pr in BOARD_RIPS)]
print(f'ripping {len(victims)} board objects')
for t in victims:
    a_ = pcbnew.ToMM(t.GetStart()); b_ = pcbnew.ToMM(t.GetEnd())
    print(f'   SEG +5V ({a_[0]:.3f},{a_[1]:.3f})->({b_[0]:.3f},{b_[1]:.3f})')
assert len(victims) == 3, 'expected exactly 3 victims'
for t in victims:
    board0.Remove(t)

t = pcbnew.PCB_TRACK(board0)
t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(NEWSEG[2][0]),
                           pcbnew.FromMM(NEWSEG[2][1])))
t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(NEWSEG[3][0]),
                         pcbnew.FromMM(NEWSEG[3][1])))
t.SetWidth(pcbnew.FromMM(NEWSEG[4]))
t.SetLayer(pcbnew.F_Cu)
t.SetNetCode(code)
board0.Add(t)
filler = pcbnew.ZONE_FILLER(board0)
filler.Fill(board0.Zones())
board0.Save(OUT)
print('saved', OUT)

b2 = pcbnew.LoadBoard(OUT)
ok = True
found = False
for t in b2.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != '+5V':
        continue
    if pair_hit(t, (NEWSEG[2], NEWSEG[3])):
        found = True
    if any(pair_hit(t, pr) for pr in BOARD_RIPS):
        print('  ripped seg STILL PRESENT')
        ok = False
print('new seg present:', found)
print('reload census:', 'OK' if (ok and found) else 'MISMATCH')
sys.exit(0 if (ok and found) else 2)
