"""t_ax0_pre: ax session harness. Reuses the au71/au97 exact-item-model
functions (fragments, item_margin, make_astar, try_emit, gate_pairs,
journey_items_dense) via the proven namespace-patch pattern (aw
t_aw33), then replaces the pool with a FAITHFUL load of the shipped
board (t_ai_lib.load_items, NO ablations) so every gate runs against
the board as built, not the au manifest."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
sys.path.insert(0, 'scratch/work/ai')
import pcbnew
import t_ai_lib as L

g = {'__name__': 'axpre'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)

_fns = (g['fragments'], g['item_margin'], g['make_astar'],
        g['try_emit'], g['gate_pairs'], g['journey_items_dense'])
_ns = {id(g): g}
for _fn in _fns:
    _ns[id(_fn.__globals__)] = _fn.__globals__

fragments = g['fragments']
item_margin = g['item_margin']
make_astar = g['make_astar']
try_emit = g['try_emit']
gate_pairs = g['gate_pairs']
journey_items_dense = g['journey_items_dense']
C = g['C']
NET_HW = g['NET_HW']

BOARD = 'hw/pdlvds_rx.exp241.kicad_pcb'


def load_board_pool(path=BOARD):
    board = pcbnew.LoadBoard(path)
    items = L.load_items(board)
    pool = {li: list(items[li]) for li in range(3)}
    for _d in _ns.values():
        _d['pool'] = pool
        _d['NEW'] = {0: [], 1: [], 2: []}
        _d['JOURNEYS'] = {}
        _d['NET_HW'] = NET_HW
    return pool


def add_items(new_items):
    """new_items: {layer: [item,...]} appended to the live pool."""
    pool = _ns[id(g)]['pool']
    for l, its in new_items.items():
        pool[l] += its
    return pool


def rip_items(specs):
    """specs: list of items (exact tuples) to remove from the live pool.
    Removes from EVERY layer list containing the item (vias live in
    all three). Returns total (item, layer) removals; a seg counts 1,
    a via counts 3."""
    pool = _ns[id(g)]['pool']
    n = 0
    for it in specs:
        for l in range(3):
            if it in pool[l]:
                pool[l].remove(it)
                n += 1
    return n


def chain_segs(pool, net, l, start, end):
    """Goal-directed walk of a net's seg chain on one layer from the
    seg incident to start to the seg incident to end (rounded coords).
    Returns the item list in walk order."""
    segs = [it for it in pool[l] if it[1] == net and it[0] == 'seg']
    bypt = {}
    for it in segs:
        d = it[2]
        bypt.setdefault((round(d[0], 3), round(d[1], 3)), []).append(it)
        bypt.setdefault((round(d[2], 3), round(d[3], 3)), []).append(it)
    out = []
    cur = (round(start[0], 3), round(start[1], 3))
    goal = (round(end[0], 3), round(end[1], 3))
    guard = 0
    while cur != goal and guard < 500:
        guard += 1
        cands = []
        for it in bypt.get(cur, []):
            if it in out:
                continue
            d = it[2]
            a = (round(d[0], 3), round(d[1], 3))
            b = (round(d[2], 3), round(d[3], 3))
            far = b if a == cur else a
            dist = (far[0] - goal[0]) ** 2 + (far[1] - goal[1]) ** 2
            cands.append((dist, it, far))
        if not cands:
            raise SystemExit(f'chain walk stuck at {cur} for {net} L{l}')
        cands.sort(key=lambda t: t[0])
        _, nxt, far = cands[0]
        out.append(nxt)
        cur = far
    return out


def fragsets(pool, net, bbox):
    """au fragments(net, box) reads the namespace pool (kept in sync by
    load_board_pool/add_items/rip_items); returns fragment list."""
    return fragments(net, bbox)
