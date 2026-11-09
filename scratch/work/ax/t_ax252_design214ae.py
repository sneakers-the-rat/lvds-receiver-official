import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')
c20 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.5) < 0.01 and it[2][0] in (75.725, 77.275)]
rip_items(c20)
add_items({0: [('pad', 'XI', (75.72, 18.75, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (76.68, 18.75, 0.280, 0.310, 0.0), 0.2)]})
c22 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.0) < 0.01 and it[2][0] in (72.02, 72.98)]
rip_items(c22)
add_items({0: [('pad', 'PHY_1V8', (79.12, 18.6, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (80.08, 18.6, 0.280, 0.310, 0.0), 0.2)]})
arm = []
for it in pool[2]:
    if it[1] == 'PHY_1V8' and it[0] == 'seg' and it[2][1] >= 16.0 \
            and max(it[2][0], it[2][2]) <= 77.85:
        arm.append(it)
for it in pool[0]:
    if it[1] == 'PHY_1V8' and it[0] == 'seg' and max(it[2][0], it[2][2]) < 72.0:
        arm.append(it)
arm += [it for it in pool[2] if it[0] == 'via'
        and ((abs(it[2][0] - 71.375) < 0.01 and abs(it[2][1] - 17.625) < 0.01)
             or (abs(it[2][0] - 73.434) < 0.01
                 and abs(it[2][1] - 17.685) < 0.01)
             or (abs(it[2][0] - 76.487) < 0.01
                 and abs(it[2][1] - 9.139) < 0.01))]
rip_items(arm)
# thin PHY_1V8 B south loop hw0.3 -> hw0.15 AND shift its vertical
# east x76.8 -> x76.95 (corner follows), opening the STP descent lens
fat = [it for it in pool[2] if it[1] == 'PHY_1V8' and it[0] == 'seg'
       and abs(it[2][4] - 0.3) < 1e-9 and it[2][1] < 15.5]
print('re-laying south-loop segs:', len(fat), flush=True)
for it in fat:
    print('   ', L.fmt_it(it), flush=True)
rip_items(fat)
newsegs = []
for it in fat:
    x1, y1, x2, y2, hw = it[2]
    pts = []
    for (x, y) in ((x1, y1), (x2, y2)):
        if abs(x - 76.8) < 0.01:
            x = 76.95
            if abs(y - 10.988) < 0.01:
                y = 11.05
        if abs(x - 77.35) < 0.01 and abs(y - 10.0) < 0.01:
            x, y = 77.45, 10.1
        pts.append((x, y))
    newsegs.append(('seg', 'PHY_1V8',
                    (pts[0][0], pts[0][1], pts[1][0], pts[1][1], 0.15),
                    it[3]))
add_items({2: newsegs})
# move PHY_1V8's south via east (77.869,10.056) -> (77.98,10.02): rip the
# via, its F feed seg and the re-laid B seg; re-add at the new site
stub = [it for it in pool[0] if it[1] == 'PHY_1V8' and it[0] == 'seg'
        and abs(it[2][2] - 77.869) < 0.01 and abs(it[2][3] - 10.056) < 0.01]
bseg = [it for it in pool[2] if it[1] == 'PHY_1V8' and it[0] == 'seg'
        and abs(it[2][0] - 77.869) < 0.01 and abs(it[2][1] - 10.056) < 0.01]
via = [it for it in pool[2] if it[0] == 'via'
       and abs(it[2][0] - 77.869) < 0.01 and abs(it[2][1] - 10.056) < 0.01]
print('stub rip:', [(L.fmt_it(i)) for i in stub + bseg + via], flush=True)
rip_items(stub + bseg + via)
add_items({0: [('seg', 'PHY_1V8', (77.25, 10.75, 77.98, 10.02, 0.1), 0.25)],
           2: [('seg', 'PHY_1V8', (77.98, 10.02, 77.45, 10.1, 0.15), 0.25),
               ('via', 'PHY_1V8', (77.98, 10.02, 0.25), 0.25)]})

# SDA B jog: move its vertical west (x69.5) across the STP dive band
sda = [it for it in pool[2] if it[1] == 'I2C_SDA' and it[0] == 'seg'
       and ((abs(it[2][0] - 69.875) < 0.01 and abs(it[2][2] - 69.875) < 0.01
             and abs(it[2][1] - 0.625) < 0.01)
            or (abs(it[2][0] - 69.9) < 0.01 and abs(it[2][1] - 0.82) < 0.01))]
print('sda rip:', [L.fmt_it(i) for i in sda], flush=True)
rip_items(sda)
add_items({2: [('seg', 'I2C_SDA', (69.9, 0.82, 69.875, 0.625, 0.125), 0.2),
               ('seg', 'I2C_SDA', (69.875, 0.625, 69.875, -1.3, 0.125), 0.2),
               ('seg', 'I2C_SDA', (69.875, -1.3, 69.5, -1.675, 0.125), 0.2),
               ('seg', 'I2C_SDA', (69.5, -1.675, 69.5, -3.0, 0.125), 0.2),
               ('seg', 'I2C_SDA', (69.5, -3.0, 69.875, -3.375, 0.125), 0.2),
               ('seg', 'I2C_SDA', (69.875, -3.375, 69.875, -9.125, 0.125),
                0.2)]})
# HV_SHDN In2 detour: dip its mouth chain south around the dive window
hv = [it for it in pool[1] if it[1] == 'HV_SHDN' and it[0] == 'seg'
      and ((abs(it[2][0] - 69.875) < 0.01 and abs(it[2][1] + 2.375) < 0.01)
           or (abs(it[2][0] - 70.125) < 0.01
               and abs(it[2][1] + 2.125) < 0.01))]
print('hv rip:', [L.fmt_it(i) for i in hv], flush=True)
rip_items(hv)
add_items({1: [('seg', 'HV_SHDN', (69.875, -2.375, 69.7, -2.9, 0.125), 0.2),
               ('seg', 'HV_SHDN', (69.7, -2.9, 70.1, -3.25, 0.125), 0.2),
               ('seg', 'HV_SHDN', (70.1, -3.25, 70.7, -2.75, 0.125), 0.2)]})

# ---- item 8: HV_SHDN chain-1 southern re-lay: rip the detour + the
# west staircase (70.7,-2.75) -> pad; the chain re-dives east of the
# mouth (design below), freeing the In2 field west of x69.5.
hvrip = [it for it in pool[1] if it[1] == 'HV_SHDN' and it[0] == 'seg'
         and min(it[2][0], it[2][2]) >= 68.0
         and max(it[2][0], it[2][2]) <= 70.71
         and max(it[2][1], it[2][3]) <= -2.3]
print('hv south rip:', len(hvrip), flush=True)
for it in hvrip:
    print('   ', L.fmt_it(it), flush=True)
assert len(hvrip) == 14, len(hvrip)
rip_items(hvrip)

# ---- item 9: PG_3V3 B re-lay: rip its x68.925 vertical + SW staircase
# (68.9,0.45) -> (69.375,-5.125); it re-lays west, freeing the B field
# between PG and SDA for STP's dive via.
pgrip = [it for it in pool[2] if it[1] == 'PG_3V3' and it[0] == 'seg'
         and min(it[2][0], it[2][2]) >= 68.55
         and max(it[2][0], it[2][2]) <= 69.45
         and min(it[2][1], it[2][3]) >= -5.13
         and max(it[2][1], it[2][3]) <= 0.46]
print('pg rip:', len(pgrip), flush=True)
rip_items(pgrip)

# STP's dive via as a blocker while PG re-lays
blk = ('via', 'ZZB', (69.15, -3.55, 0.25), 0.2)
add_items({l: [blk] for l in range(3)})

astar_pg = make_astar((66.8, 70.2, -5.6, 1.0), 0.05)
Jpg = astar_pg('PG_3V3', ((2,), 68.9, 0.45), (2, 69.375, -5.125),
               hw=0.125)
print('PG re-lay:', 'FOUND' if Jpg else 'NONE',
      ('vias=' + str(Jpg['vias'])) if Jpg else '', flush=True)
if Jpg:
    add_items(journey_items_dense(Jpg, 'PG_3V3', hw=0.125))

astar_hv = make_astar((67.0, 72.6, -6.6, 0.0), 0.05)
Jhv = astar_hv('HV_SHDN', ((1,), 70.7, -2.75), (1, 68.6, -5.5),
               hw=0.125)
print('HV re-lay:', 'FOUND' if Jhv else 'NONE',
      ('vias=' + str(Jhv['vias'])) if Jhv else '', flush=True)
if Jhv:
    add_items(journey_items_dense(Jhv, 'HV_SHDN', hw=0.125))

n = rip_items([blk])
print('blocker removed:', n, flush=True)
assert n == 3, n

box = (64.0, 79.5, -6.0, 20.5)
cur = ((2,), 76.065, 17.99)
legs = []
for label, g in (('B (76.35,18.1)', (2, 76.35, 18.1)),
                 ('B (76.15,13.5)', (2, 76.15, 13.5)),
                 ('B (75.8,10.15)', (2, 75.8, 10.15)),
                 ('B (76.7,9.4)', (2, 76.7, 9.4)),
                 ('B (77.7,9.45)', (2, 77.7, 9.45)),
                 ('B (78.3,9.2)', (2, 78.3, 9.2)),
                 ('B (77.45,8.2)', (2, 77.45, 8.2)),
                 ('B (77.5,6.0)', (2, 77.5, 6.0)),
                 ('B (77.5,0.0)', (2, 77.5, 0.0)),
                 ('B (76.0,-1.25)', (2, 76.0, -1.25)),
                 ('B (73.0,-1.5)', (2, 73.0, -1.5)),
                 ('I (74.0,-1.0)', (1, 74.0, -1.0)),
                 ('I (72.7,-1.3)', (1, 72.7, -1.3)),
                 ('I (72.3,-2.4)', (1, 72.3, -2.4)),
                 ('I (71.5,-3.3)', (1, 71.5, -3.3)),
                 ('I (69.65,-3.6)', (1, 69.65, -3.6)),
                 ('F pad', (0, 71.3375, -2.25))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', cur, g, hw=0.10)
    print(f'STP stage -> {label}:', 'FOUND' if J else 'NONE',
          ('vias=' + str(J['vias'])) if J else '', flush=True)
    if not J:
        break
    legs.append(J)
    cur = ((g[0],), g[1], g[2])
out = {}
if Jpg:
    out['pg_journey'] = Jpg
if Jhv:
    out['hv_journey'] = Jhv
if len(legs) == 17:
    out['stp_legs'] = legs
    print('STP HAUL COMPLETE', flush=True)
json.dump(out, open('scratch/work/ax/design214_ax252.json', 'w'))
