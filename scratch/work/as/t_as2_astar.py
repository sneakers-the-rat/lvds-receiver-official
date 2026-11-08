"""t_as2: wider SCK dive-via scan + In2 A* approach from saddle exit B.
Via scan x[71.8,76.2] y[1.9,5.7] step 0.025 (all-layer pt_margin, boxed pool).
For each via with margin >= -0.001: A* on 0.1 grid (8-dir) over In2 box
x[70.6,76.4] y[1.7,5.9]; edge legal iff seg_margin >= -0.001 (step 0.05);
cost = length + 2.0*(0.05 - margin) penalty for knife edges. Reports path."""
import sys, wx, json, heapq, math
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin, apply_rip, in_box_pool

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp236.kicad_pcb')
items = load_items(board)
mods = json.load(open('scratch/work/ar/mods_v7.json'))
statics, nrip = apply_rip({l: list(items[l]) for l in range(3)},
                          [tuple(r) for r in mods['rips']])
BOX = (66.0, 79.5, -1.0, 10.5)
pool = in_box_pool(statics, BOX, pad=1.0)
pre = [(0,(71.425,6.75,70.1,6.78,0.1)), (0,(70.1,6.78,68.7,6.8,0.1)),
       (0,(68.7,6.8,67.8,8.1,0.1)),
       (1,(67.8,8.1,69.0,6.2,0.1)), (1,(69.0,6.2,69.45,5.45,0.1)),
       (1,(69.45,5.45,69.85,4.62,0.1)), (1,(69.85,4.62,70.294,4.204,0.1)),
       (1,(70.294,4.204,71.094,4.958,0.1))]
for l,g in pre: pool[l].append(('seg','SPI_SCK',g,0.2))
for l in range(3): pool[l].append(('via','SPI_SCK',(67.8,8.1,0.25),0.2))

cands = []
x = 71.80
while x <= 76.201:
    y = 1.90
    while y <= 5.701:
        worst = 9
        for l in range(3):
            m,w = pt_margin(l, x, y, 'SPI_SCK', 0.25, pool[l])
            if m < worst: worst = m
        if worst >= -0.001: cands.append((worst, round(x,3), round(y,3)))
        y += 0.025
    x += 0.025
cands.sort(reverse=True)
print(f'{len(cands)} via candidates:', flush=True)
for c in cands[:25]: print(f'  ({c[1]},{c[2]}) {c[0]:+.3f}', flush=True)

B = (71.094,4.958)
GX0, GY0, STEP = 70.6, 1.7, 0.1
def node(p): return (round((p[0]-GX0)/STEP), round((p[1]-GY0)/STEP))
def pt(n): return (GX0+n[0]*STEP, GY0+n[1]*STEP)
def edge_ok(a, b, extra):
    m,_ = seg_margin(1, a, b, 'SPI_SCK', 0.1, list(pool[1])+extra, step=0.05)
    return m
for worst0, vx, vy in cands[:25]:
    extra = [('via','SPI_SCK',(vx,vy,0.25),0.2)]
    start, goal = node(B), node((vx,vy))
    # final approach: goal node centre may be off-grid point; use exact via pt as goal
    openh = [(0.0, start)]
    came = {start: None}; gs = {start: 0.0}; worst_edge = {start: 9.9}
    found = None
    while openh:
        f, cur = heapq.heappop(openh)
        cp = pt(cur)
        # try direct finish to exact via point
        mfin = edge_ok(cp, (vx,vy), extra)
        if mfin >= -0.001:
            found = (cur, mfin); break
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                if dx==0 and dy==0: continue
                nb = (cur[0]+dx, cur[1]+dy)
                if nb in came: continue
                np_ = pt(nb)
                if not (70.6 <= np_[0] <= 76.4 and 1.7 <= np_[1] <= 5.9): continue
                m = edge_ok(cp, np_, extra)
                if m < -0.001: continue
                ng = gs[cur] + math.hypot(dx,dy)*STEP + 2.0*max(0.0, 0.05-m)
                came[nb] = cur; gs[nb] = ng; worst_edge[nb] = min(worst_edge[cur], m)
                h = math.hypot(np_[0]-vx, np_[1]-vy)
                heapq.heappush(openh, (ng+h, nb))
    if found:
        cur, mfin = found
        path = [pt(cur)]
        while came[cur] is not None:
            cur = came[cur]; path.append(pt(cur))
        path.reverse()
        print(f'VIA ({vx},{vy}) margin {worst0:+.3f}: A* path {len(path)} pts, worst edge {min(worst_edge[node(path[-1])] if node(path[-1]) in worst_edge else 9, mfin):+.3f}', flush=True)
        print('   ', [(round(a,2),round(b,2)) for a,b in path], '-> via', (vx,vy), flush=True)
    else:
        print(f'VIA ({vx},{vy}) margin {worst0:+.3f}: A* NO PATH', flush=True)
