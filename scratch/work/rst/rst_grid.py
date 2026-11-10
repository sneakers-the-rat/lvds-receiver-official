import sys, math
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
import gridroute as G
import bm_gate as BG

BG.clr = lambda net: 0.20
SRC = 'hw/pdlvds_rx.exp272.kicad_pcb'
items = G.load_items(SRC)
for it in items:
    it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
print('total items:', len(items), flush=True)

BX0, BX1, BY0, BY1 = 73.3, 76.2, 17.0, 19.9
EX = 1.6
def bbox(it):
    if it.rect:
        return it.rect
    pts = [q for q in (it.a, it.b) if q]
    if not pts:
        return None
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    r = it.hw or 0.3
    return (min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r)

def is_victim(it):
    if it.net in ('ULPI_DIR', 'ULPI_NXT'):
        if it.rect:
            return False
        pts = [q for q in (it.a, it.b) if q]
        return any(15.5 < p[1] < 21 for p in pts)
    if it.net == 'DM_PHY' and it.kind == 'trk' and it.layer == 'F.Cu':
        pts = [q for q in (it.a, it.b) if q]
        return any(15.5 < p[1] < 20 for p in pts)
    return False

pool = []
for it in items:
    if is_victim(it):
        continue
    b = bbox(it)
    if b and b[0] <= BX1 + EX and b[2] >= BX0 - EX and b[1] <= BY1 + EX and b[3] >= BY0 - EX:
        pool.append(it)
print('local pool:', len(pool), flush=True)

def solo(net):
    out = []
    x = BX0
    while x <= BX1 + 1e-9:
        y = BY0
        while y <= BY1 + 1e-9:
            ms = BG.margin_via((round(x, 2), round(y, 2)), net, pool, r=0.25)
            worst = min((m for m, d in ms), default=9)
            if worst >= 0.005:
                out.append((worst, (round(x, 2), round(y, 2))))
            y += 0.05
        x += 0.05
    out.sort(reverse=True)
    return out

rst = solo('USB_RST'); print(f'RST solo: {len(rst)} top {rst[:4]}', flush=True)
dir_ = solo('ULPI_DIR'); print(f'DIR solo: {len(dir_)} top {dir_[:4]}', flush=True)
nxt = solo('ULPI_NXT'); print(f'NXT solo: {len(nxt)} top {nxt[:4]}', flush=True)

# decimate: keep spatially diverse top spots (lists are big; joint search streams into a bounded heap)
import heapq
def decimate(L, cap=200, sep=0.20):
    kept = []
    for m, v in L:
        if all(math.hypot(v[0] - k[1][0], v[1] - k[1][1]) >= sep for k in kept):
            kept.append((m, v))
            if len(kept) >= cap:
                break
    return kept
rst = decimate(rst); dir_ = decimate(dir_); nxt = decimate(nxt)
print(f'decimated: RST {len(rst)} DIR {len(dir_)} NXT {len(nxt)}', flush=True)

K = 25
heap = []
def push(score, vr, vd, vn):
    item = (score, vr, vd, vn)
    if len(heap) < K:
        heapq.heappush(heap, item)
    elif score > heap[0][0]:
        heapq.heapreplace(heap, item)
npairs = 0
for mr, vr in rst:
    for md, vd in dir_:
        if math.hypot(vr[0] - vd[0], vr[1] - vd[1]) < 0.70:
            continue
        npairs += 1
        for mn, vn in nxt:
            if math.hypot(vr[0] - vn[0], vr[1] - vn[1]) < 0.70:
                continue
            if math.hypot(vd[0] - vn[0], vd[1] - vn[1]) < 0.70:
                continue
            push(mr + md + mn, vr, vd, vn)
print('RST x DIR pairs (decimated):', npairs, flush=True)
heap.sort(reverse=True)
print(f'top triples (of streamed search):', flush=True)
for sc, vr, vd, vn in heap:
    print(f'  score {sc:+.3f}  RST {vr}  DIR {vd}  NXT {vn}', flush=True)
