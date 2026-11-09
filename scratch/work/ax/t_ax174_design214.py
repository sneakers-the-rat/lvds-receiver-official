import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp250.kicad_pcb')

# --- virtual pass-214 geometry changes ---
# C20 0603 pads -> 0402 pads at (76.2,18.75)
c20 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.5) < 0.01 and it[2][0] in (75.725, 77.275)]
rip_items(c20)
add_items({0: [('pad', 'XI', (75.72, 18.75, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (76.68, 18.75, 0.280, 0.310, 0.0), 0.2)]})
# C22 pads leave (72.02/72.98,18.0); new pads at (79.6,18.6)
c22 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 18.0) < 0.01 and it[2][0] in (72.02, 72.98)]
rip_items(c22)
add_items({0: [('pad', 'PHY_1V8', (79.12, 18.6, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (80.08, 18.6, 0.280, 0.310, 0.0), 0.2)]})
# PHY_1V8 B west arm + F tail + C22 via + GND stitch via (73.434,17.685)
arm = []
for it in pool[2]:
    if it[1] == 'PHY_1V8' and it[0] == 'seg':
        d = it[2]
        if d[1] >= 16.0 and max(d[0], d[2]) <= 77.85:
            arm.append(it)
for it in pool[0]:
    if it[1] == 'PHY_1V8' and it[0] == 'seg':
        arm.append(it)
arm += [it for it in pool[2] if it[0] == 'via'
        and ((abs(it[2][0] - 71.375) < 0.01 and abs(it[2][1] - 17.625) < 0.01)
             or (abs(it[2][0] - 73.434) < 0.01
                 and abs(it[2][1] - 17.685) < 0.01))]
print('ripping PHY arm items:', len(arm), flush=True)
for it in arm:
    print('   ', L.fmt_it(it), flush=True)
rip_items(arm)

out = {}
# --- STP haul, staged on B from the dive via ---
box = (66.0, 78.5, -4.0, 19.5)
cur = ((2,), 76.065, 17.99)
legs = []
for label, g in (('B (75.5,16.9)', (2, 75.5, 16.9)),
                 ('B (73.9,16.9)', (2, 73.9, 16.9)),
                 ('B (71.5,16.9)', (2, 71.5, 16.9)),
                 ('B (70.5,17.25)', (2, 70.5, 17.25)),
                 ('B (70.35,14.0)', (2, 70.35, 14.0)),
                 ('B (68.5,11.9)', (2, 68.5, 11.9)),
                 ('B (68.6,6.0)', (2, 68.6, 6.0)),
                 ('B (68.8,1.0)', (2, 68.8, 1.0)),
                 ('B (70.3,-2.25)', (2, 70.3, -2.25)),
                 ('F pad', (0, 71.3375, -2.25))):
    astar = make_astar(box, 0.05)
    J = astar('ULPI_STP', cur, g, hw=0.10)
    print(f'STP stage -> {label}:', 'FOUND' if J else 'NONE',
          ('vias=' + str(J['vias'])) if J else '', flush=True)
    if not J:
        break
    legs.append(J)
    cur = ((g[0],), g[1], g[2])
if len(legs) == 10:
    out['stp_legs'] = legs
    print('STP HAUL COMPLETE', flush=True)

# --- XI: U7.28 pad -> C20.1 pad / web west end ---
box2 = (70.0, 80.0, 8.0, 20.5)
for label, g in (('XI -> web In2 (75.625,18.625)', (1, 75.625, 18.625)),
                 ('XI -> C20.1 F (75.72,18.75)', (0, 75.72, 18.75))):
    astar = make_astar(box2, 0.05)
    J = astar('XI', ((0,), 76.25, 11.5625), g, hw=0.10)
    print(f'{label}:', 'FOUND vias=' + str(J['vias']) if J else 'NONE',
          flush=True)
    if J:
        out[label] = J

# --- USB_RST: U7.9 pad -> U6.40 pad ---
box3 = (68.0, 80.0, -2.0, 18.0)
astar = make_astar(box3, 0.05)
J = astar('USB_RST', ((0,), 74.25, 16.4375), (0, 74.75, 4.6625), hw=0.10)
print('USB_RST:', 'FOUND vias=' + str(J['vias']) if J else 'NONE', flush=True)
if J:
    out['usb_rst'] = J
json.dump(out, open('scratch/work/ax/design214_ax174.json', 'w'))
print('saved design214_ax174.json keys:', list(out.keys()), flush=True)
