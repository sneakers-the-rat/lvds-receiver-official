import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au43_phase1b.py').read()
exec(src.split("J40 = json.load")[0], g)
pool0 = g['pool']
import t_ai_lib as L
def is_sda_via(it):
    return it[0] == 'via' and it[1] == 'I2C_SDA' and \
        abs(it[2][0] - 69.05) < 0.01 and abs(it[2][1] - 2.05) < 0.01
def is_sda_stub(it):
    return it[0] == 'seg' and it[1] == 'I2C_SDA' and \
        abs(it[2][0] - 68.45) < 0.01 and abs(it[2][1] - 2.1) < 0.01
pool = {l: [it for it in pool0[l]
            if not is_sda_via(it) and not is_sda_stub(it)]
        for l in range(3)}
removed = {l: len(pool0[l]) - len(pool[l]) for l in range(3)}
print('removed per layer:', removed)
for l in range(3):
    m, w = L.pt_margin(l, 69.05, 2.05, 'I2C_SDA', 0.25,
                       [o for o in pool[l] if o[1] != 'I2C_SDA'])
    print(f'L{l} via gate: {m:+.3f} vs {L.fmt_it(w)}')
m, w = L.seg_margin(0, (68.225, 2.1), (69.05, 2.05), 'I2C_SDA', 0.10,
                    [o for o in pool[0] if o[1] != 'I2C_SDA'])
print(f'stub gate: {m:+.3f} vs {L.fmt_it(w)}')
