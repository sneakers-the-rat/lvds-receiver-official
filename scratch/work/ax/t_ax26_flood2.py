"""t_ax26: door-1 open; B binders along the eastern descent corridor
+ B flood map from (69.5,12.75), box (68.5,74.5,0,13.5)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import numpy as np
from collections import deque

pool = load_board_pool()
cands = [it for it in pool[0] if it[0] == 'via' and it[1] == 'I2C_SCL'
         and abs(it[2][0] - 69.625) < 0.01 and abs(it[2][1] - 12.625) < 0.01]
for c in cands:
    rip_items([c])
newvia = ('via', 'I2C_SCL', (69.5, 12.75, 0.3), 0.2)
add_items({0: [newvia], 2: [newvia]})
pool[1].append(newvia)
c3 = [it for it in pool[0] if it[0] == 'via' and it[1] == '+3V3D'
      and abs(it[2][0] - 70.875) < 0.01 and abs(it[2][1] - 12.625) < 0.01]
for c in c3:
    rip_items([c])
nv3 = ('via', '+3V3D', (70.875, 12.625, 0.25), 0.25)
add_items({0: [nv3], 2: [nv3]})
pool[1].append(nv3)

others = {l: [o for o in pool[l] if o[1] != 'I2C_SCL'] for l in range(3)}
print('— descent corridor binders (B):', flush=True)
for (x, y) in ((70.5, 12.0), (71.5, 11.0), (72.3, 10.0), (71.85, 9.0),
               (71.5, 7.25), (72.5, 6.0), (72.5, 4.5), (72.5, 3.4),
               (71.5, 2.6), (70.5, 1.9), (71.85, 11.5), (73.0, 11.94),
               (70.15, 10.0), (70.15, 8.0)):
    m, b = L.pt_margin(2, x, y, 'I2C_SCL', 0.10, others[2])
    print(f'B ({x},{y}): {m:+.3f} binder {L.fmt_it(b)}', flush=True)
print('— In2 binders:', flush=True)
for (x, y) in ((71.85, 9.0), (72.5, 6.0), (70.15, 10.0)):
    m, b = L.pt_margin(1, x, y, 'I2C_SCL', 0.10, others[1])
    print(f'In2 ({x},{y}): {m:+.3f} binder {L.fmt_it(b)}', flush=True)
print('— F binders:', flush=True)
for (x, y) in ((71.85, 9.0), (72.5, 6.0), (70.15, 10.0)):
    m, b = L.pt_margin(0, x, y, 'I2C_SCL', 0.10, others[0])
    print(f'F ({x},{y}): {m:+.3f} binder {L.fmt_it(b)}', flush=True)
