import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au43_phase1b.py').read()
exec(src.split("J40 = json.load")[0], g)
pool0 = g['pool']
journey_items_dense = g['journey_items_dense']
import t_ai_lib as L
C = g['C']
def is_sda_via(it):
    return it[0] == 'via' and it[1] == 'I2C_SDA' and \
        abs(it[2][0] - 69.05) < 0.01 and abs(it[2][1] - 2.05) < 0.01
def is_sda_stub(it):
    return it[0] == 'seg' and it[1] == 'I2C_SDA' and \
        abs(it[2][0] - 68.45) < 0.01 and abs(it[2][1] - 2.1) < 0.01
pool = {l: [it for it in pool0[l]
            if not is_sda_via(it) and not is_sda_stub(it)]
        for l in range(3)}
J40 = json.load(open('scratch/work/au/joint_au40.json'))
for l, its in journey_items_dense(J40['jobs']['bheal'], 'I2C_SCL',
                                  hw=0.10).items():
    pool[l] += its
def gate_pool(l):
    return [o for o in pool[l] if o[1] != 'I2C_SDA'
            and not (o[1] == 'PG_3V3' and 60.0 < C(o)[0] < 70.0
                     and 0.0 < C(o)[1] < 16.0)]
for l in range(3):
    m, w = L.pt_margin(l, 69.05, 2.05, 'I2C_SDA', 0.25, gate_pool(l))
    print(f'L{l} via gate (excl PG pocket): {m:+.3f} vs {L.fmt_it(w)}')
