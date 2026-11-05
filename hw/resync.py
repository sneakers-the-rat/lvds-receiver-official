#!/usr/bin/env python3
"""Re-sync the routed board to the corrected schematic (pass 81).

Absorbs the parts-fix netlist (scratch/netlist_map.json: 152 parts /
648 pins / 223 nets) into hw/pdlvds_rx.exp21.kicad_pcb:

- creates the 7 new real nets (HV_EN, HV_OVP1/2, HV_R29M, HV_R30M,
  HV_R31A, HV_R31B);
- footprint swaps in place: C4->ECWFD film, D4->D_SMB, L1/L2->
  Murata DFE, R29->R_0603, R31->R_1210, T1->XFMR_EFD20_SMD10,
  X1->Crystal_SMD_HC49-SD, U9->TMP117_WSON6 (redrawn, same name);
- cluster placement iteration: T1 (EFD20, 23.11x26.1) east in the
  strip; the R31 string (R31 + 2 new R_1210) and R29 string
  (R29 + 1 new R_0603) move to the strip's north row; R34 moves
  clear of T1's body; R30's string partner goes south of R30;
  C4 (25.3x8.4 body) takes the first candidate clear of SH1/R30;
  D9-D11 (OVP stack, DNP) in a row on the west strip;
- J5 interlock: the HV_SHDN run to U6 is severed at the In2
  segment above the divider via; the U6-side copper is reassigned
  to HV_EN (U6.97 = PC7 now drives HV_EN); J5 sits at the west
  board edge bridging HV_EN -> HV_SHDN;
- TP_HV class fix: TP1 relocates from (45,20) — 0.15 mm from the
  GND run at x~46 vs the 1.0 mm HV class — to (40.8,23) and is
  re-stubbed into the TP_HV web (segments asserted);
- every pad's net is (re)assigned from the map for every ref the
  map names (unconnected-* pseudo-nets are left netless);
- zones refilled at the end (pours re-carve around moved pads).

Placements are candidate-searched in-script: a candidate wins only
if the part's pads clear every other part's pads by >=0.25 mm and,
for T1/C4, the body box clears other pads and SH1's box.
Usage: xvfb-run -a python3 hw/resync.py <src> <out>
"""
import json
import math
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
import gridplace
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MMf = pcbnew.FromMM
MMt = pcbnew.ToMM
SYS = '/usr/share/kicad/footprints'
SRC, OUT = sys.argv[1], sys.argv[2]
PHASE = sys.argv[3] if len(sys.argv) > 3 else 'AB'
board = pcbnew.LoadBoard(SRC)
nmap = json.load(open('scratch/netlist_map.json'))
LOG = []
_DEAD = []  # keepalive: removed items' proxies must never be GC'd
            # (a freed proxy corrupts board iteration in KiCad 7 SWIG)

def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s, flush=True)

# ---------- nets ----------
def get_net(name):
    ni = board.FindNet(name)
    if not ni:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
    return ni

for n in ('HV_EN', 'HV_OVP1', 'HV_OVP2', 'HV_R29M', 'HV_R30M',
          'HV_R31A', 'HV_R31B'):
    get_net(n)

# ---------- footprint loading ----------
def load_fp(fpid):
    lib, name = fpid.split(':')
    path = 'hw/pdlvds.pretty' if lib == 'pdlvds' else f'{SYS}/{lib}.pretty'
    fp = pcbnew.FootprintLoad(path, name)
    assert fp, f'cannot load {fpid}'
    return fp

def pad_net_assign(fp, ref):
    want = nmap[ref]['pins']
    for p in fp.Pads():
        net = want.get(p.GetNumber())
        if net and not net.startswith('unconnected-('):
            p.SetNet(get_net(net))

# ---------- collision model ----------
def all_pads(exclude_refs):
    out = []
    for fp in board.GetFootprints():
        if fp.GetReference() in exclude_refs:
            continue
        for p in fp.Pads():
            out.append((fp.GetReference(), p))
    return out

def pads_clear(fp, exclude_refs, gap=0.25):
    """fp's pads vs every other part's pads (effective shapes)."""
    others = all_pads(set(exclude_refs) | {fp.GetReference()})
    for p in fp.Pads():
        s = p.GetEffectiveShape(0)
        for ref2, p2 in others:
            if s.Collide(p2.GetEffectiveShape(0), MMf(gap - 0.001)):
                return f'{ref2} pad'
    return None

def body_clear(fp, extra_boxes=()):
    """fp's bounding box vs other parts' pads + given solid boxes."""
    bb = fp.GetBoundingBox()
    rect = pcbnew.SHAPE_RECT(
        pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()),
        int(bb.GetRight() - bb.GetLeft()),
        int(bb.GetBottom() - bb.GetTop()))
    for ref2, p2 in all_pads({fp.GetReference()}):
        s = p2.GetEffectiveShape(0)
        if s.Collide(rect, MMf(0.0)):
            return f'{ref2} pad in body'
    for (x1, y1, x2, y2) in extra_boxes:
        r = pcbnew.SHAPE_RECT(pcbnew.VECTOR2I(MMf(x1), MMf(y1)),
                              MMf(x2 - x1), MMf(y2 - y1))
        if r.Collide(rect, MMf(0.0)):
            return 'solid box in body'
    return None

def try_place(fp, ref, candidates, body=False, extra_boxes=()):
    for (x, y, rot) in candidates:
        fp.SetPosition(pcbnew.VECTOR2I(MMf(x), MMf(y)))
        fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        bad = pads_clear(fp, set())
        if bad:
            log(f'  {ref} @({x},{y},{rot}): pads blocked by {bad}')
            continue
        if body:
            bad = body_clear(fp, extra_boxes)
            if bad:
                log(f'  {ref} @({x},{y},{rot}): body blocked: {bad}')
                continue
        log(f'  {ref} placed @({x},{y}) rot={rot}')
        return (x, y, rot)
    raise AssertionError(f'{ref}: no candidate cleared')

# ---------- swaps (position preserved unless moved later) ----------
def swap(ref, move_candidates=None, body=False, extra_boxes=()):
    old = board.FindFootprintByReference(ref)
    pos, rot = old.GetPosition(), old.GetOrientationDegrees()
    new = load_fp(nmap[ref]['footprint'])
    new.SetReference(ref)
    new.SetValue(nmap[ref]['value'])
    _DEAD.append(old)
    board.Remove(old)
    board.Add(new)
    if move_candidates:
        try_place(new, ref, move_candidates, body, extra_boxes)
    else:
        new.SetPosition(pos)
        new.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        log(f'  {ref} swapped in place -> {nmap[ref]["footprint"]}')
    pad_net_assign(new, ref)
    return new

if PHASE == 'B':
    pass  # swaps/cluster already applied in phase A
else:
    pass
def place_new(ref, candidates=None, grid=None, body=False,
              extra_boxes=()):
    fp = load_fp(nmap[ref]['footprint'])
    fp.SetReference(ref)
    fp.SetValue(nmap[ref]['value'])
    board.Add(fp)
    if grid is not None:
        region, home = grid
        got = gridplace.place(board, fp, region, home, body=body,
                              solids=extra_boxes, log=log)
        assert got, f'{ref}: grid placement failed'
    else:
        try_place(fp, ref, candidates, body, extra_boxes)
    pad_net_assign(fp, ref)
    return fp

# string partners identified by their map nets
def partner(net_a, net_b):
    for ref, e in nmap.items():
        pins = set(e['pins'].values())
        if net_a in pins and net_b in pins and \
                not board.FindFootprintByReference(ref):
            return ref
    raise AssertionError(f'no unplaced partner for {net_a}/{net_b}')


if PHASE != 'B':
    # Board growth (user standing order: enlarge when geometry
    # demands it): the EFD20 transformer (23.11x26.1) has no
    # feasible point in the 30 mm strip — the flyback cluster
    # (Q1/R24/R27/R28/C30/C35/D5) fills its only window. Extend
    # the north edge -30 -> -45 (mirrors expand_board.py's p65
    # mechanics; connector edges and the APD cluster do not move).
    n_edge = 0
    for d in board.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        s, e = d.GetStart(), d.GetEnd()
        sx, sy, ex, ey = MMt(s.x), MMt(s.y), MMt(e.x), MMt(e.y)
        def isx(v, t):
            return abs(v - t) < 0.1
        top = isx(sy, -30) and isx(ey, -30) and abs(ex - sx) > 90
        west = isx(sx, 0) and isx(ex, 0) and abs(ey - sy) > 90
        east = isx(sx, 100) and isx(ex, 100) and abs(ey - sy) > 90
        if top:
            d.SetStart(pcbnew.VECTOR2I(s.x, MMf(-45.0)))
            d.SetEnd(pcbnew.VECTOR2I(e.x, MMf(-45.0)))
            n_edge += 1
        elif west or east:
            for getter, setter in ((d.GetStart, d.SetStart),
                                   (d.GetEnd, d.SetEnd)):
                p = getter()
                if isx(MMt(p.y), -30):
                    setter(pcbnew.VECTOR2I(p.x, MMf(-45.0)))
            n_edge += 1
    assert n_edge >= 3, f'outline extension hit {n_edge} segments'
    log(f'outline: north edge -30 -> -45 ({n_edge} segments)')

    sh1 = board.FindFootprintByReference('SH1')
    sb = sh1.GetBoundingBox()
    SH1_BOX = (MMt(sb.GetLeft()), MMt(sb.GetTop()),
               MMt(sb.GetRight()), MMt(sb.GetBottom()))
    log(f'SH1 solid box: {SH1_BOX}')

    log('swaps:')
    swap('D4')
    swap('L1')
    swap('L2')
    swap('X1')
    swap('U9')
    swap('R30')  # same footprint; partner placed below
    c4 = swap('C4', move_candidates=[(13.5, 22, 0), (16, 20, 0),
                                     (13.5, 18, 0), (22, 22, 0),
                                     (18, 16, 0)],
              body=True, extra_boxes=[SH1_BOX])

    # ---------- HV cluster: strings + R34 first, then T1 ----------
    import gridplace
    log('HV cluster placement (grid search):')
    r33 = board.FindFootprintByReference('R33')
    gridplace.place(board, r33, (22, -3.6, 30, -2.4), (26, -3.0),
                    log=log)
    r31 = swap('R31')
    gridplace.place(board, r31, (27, -2.8, 44, -1.0), (32, -1.8), log=log)
    r29 = swap('R29')
    gridplace.place(board, r29, (38, -2.8, 54, -1.0), (44.5, -1.8),
                    log=log)


    p = partner('HV_R31A', 'HV_R31B')
    place_new(p, grid=((30, -2.8, 50, -1.0), (35.6, -1.8)))
    p = partner('HV_R31B', 'HV_FBX')
    place_new(p, grid=((33, -2.8, 53, -1.0), (39.2, -1.8)))
    p = partner('HV_R29M', 'APD_K')
    place_new(p, grid=((40, -2.8, 56, -1.0), (47.3, -1.8)))
    p = partner('HV_R30M', 'GND')
    place_new(p, candidates=[(17.5, 28.5, 0)])

    

    c9 = board.FindFootprintByReference('C9')
    got = gridplace.place(board, c9, (45, -30.5, 50, -27.5),
                          (47, -29), log=log)
    assert got, 'C9: no feasible point'
    t1 = swap('T1')
    got = gridplace.place(board, t1, (32.4, -31.9, 36, -31.1),
                          (33, -31.4), body=True, step=0.25, log=log,
                          body_wh=(23.11, 26.1))
    if not got:
        got = gridplace.place(board, t1, (24, -33, 42, -29.5),
                              (31.5, -31), body=True, log=log,
                              body_wh=(23.11, 26.1))
    assert got, 'T1: no feasible point'
    pad_net_assign(t1, 'T1')

    r34 = board.FindFootprintByReference('R34')
    got = gridplace.place(board, r34, (40, -9, 60, -0.5), (48, -4),
                          body=True, log=log)
    if not got:
        got = gridplace.place(board, r34, (14, -27.5, 30, -20.5),
                              (20, -24), body=True, log=log)
    assert got, 'R34: no feasible point in either region'

if PHASE == 'A':
    board.Save(OUT)
    log(f'saved {OUT} (phase A: swaps + cluster placement)')
    open('results/resync-log.txt', 'w').write('\n'.join(LOG) + '\n')
    sys.exit(0)

# ---------- D9-D11 OVP stack (west strip row, chain order) ----------
log('OVP stack:')
chain = []
for a, b in (('HV_RAW', 'HV_OVP1'), ('HV_OVP1', 'HV_OVP2'),
             ('HV_OVP2', 'GND')):
    for ref, e in nmap.items():
        pins = set(e['pins'].values())
        if a in pins and b in pins and \
                not board.FindFootprintByReference(ref):
            chain.append(ref)
assert len(chain) == 3, f'OVP chain: {chain}'
for i, ref in enumerate(chain):
    place_new(ref, grid=((4, -27, 24, -23), (6 + 6 * i, -25)))

# ---------- J5 interlock split ----------
log('J5 interlock:')
items = build_items(board)

def seg_shape(x1, y1, x2, y2, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x1), MMf(y1)),
                                pcbnew.VECTOR2I(MMf(x2), MMf(y2)),
                                MMf(w))

def seg_blocked(net, x1, y1, x2, y2, w, layer):
    s = seg_shape(x1, y1, x2, y2, w)
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        if layer not in l2:
            continue
        need = need_for(net, n2, {layer})
        if s.Collide(s2, MMf(need - 0.001)):
            return (n2, desc)
    return None

def disc_blocked(net, x, y):
    s = seg_shape(x, y, x, y, 0.6)
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        need = need_for(net, n2, l2)
        if s.Collide(s2, MMf(need - 0.001)):
            return (n2, desc)
    return None

# sever: the HV_SHDN In2 track centred ~(8.88,-17.75)
sever = None
for t in board.GetTracks():
    if t.GetNetname() == 'HV_SHDN' and t.GetLayer() == pcbnew.In2_Cu:
        cx = MMt((t.GetStart().x + t.GetEnd().x) / 2)
        cy = MMt((t.GetStart().y + t.GetEnd().y) / 2)
        if abs(cx - 8.88) < 0.3 and abs(cy + 17.75) < 0.6:
            sever = t
            log(f'  sever candidate: ({cx:.2f},{cy:.2f}) '
                f'({MMt(t.GetStart().x):.2f},{MMt(t.GetStart().y):.2f})'
                f'->({MMt(t.GetEnd().x):.2f},{MMt(t.GetEnd().y):.2f})')
            break
assert sever is not None, 'sever segment not found'
sx = (MMt(sever.GetStart().x) + MMt(sever.GetEnd().x)) / 2
_DEAD.append(sever)
board.Remove(sever)

# union-find HV_SHDN copper after the sever
shdn = [t for t in board.GetTracks() if t.GetNetname() == 'HV_SHDN']
parent = list(range(len(shdn)))

def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i

def tshape(t):
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        return seg_shape(MMt(p.x), MMt(p.y), MMt(p.x), MMt(p.y),
                         MMt(t.GetWidth()))
    s, e = t.GetStart(), t.GetEnd()
    return seg_shape(MMt(s.x), MMt(s.y), MMt(e.x), MMt(e.y),
                     MMt(t.GetWidth()))

shapes = [tshape(t) for t in shdn]
laysets = []
for t in shdn:
    laysets.append(set(t.GetLayerSet().Seq()))
for i in range(len(shdn)):
    for j in range(i + 1, len(shdn)):
        if laysets[i] & laysets[j] and \
                shapes[i].Collide(shapes[j], MMf(0.001)):
            a, b = find(i), find(j)
            if a != b:
                parent[a] = b
# the keep-group touches R26.1's pad (10.68,-20.5)
keep_root = None
for i, t in enumerate(shdn):
    if shapes[i].Collide(seg_shape(10.68, -20.5, 10.68, -20.5, 0.8),
                          MMf(0.001)):
        keep_root = find(i)
assert keep_root is not None, 'keep group not found'
n_en = 0
for i, t in enumerate(shdn):
    if find(i) != keep_root:
        t.SetNet(get_net('HV_EN'))
        n_en += 1
log(f'  reassigned {n_en} HV_SHDN items -> HV_EN (U6-side run); '
    f'keep-group stays HV_SHDN')

j5 = place_new('J5', [(3.5, -16.5, 90), (3.5, -16.5, 0),
                      (2.8, -19, 90)])
j5pads = {p.GetNumber(): (MMt(p.GetPosition().x),
                          MMt(p.GetPosition().y))
          for p in j5.Pads()}
log(f'  J5 pads: {j5pads}')
items = build_items(board)  # refresh after edits

def add_track(net, x1, y1, x2, y2, w, layer):
    bad = seg_blocked(net, x1, y1, x2, y2, w, layer)
    assert not bad, f'{net} seg ({x1},{y1})->({x2},{y2}) L{layer}: {bad}'
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MMf(x1), MMf(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MMf(x2), MMf(y2)))
    t.SetWidth(MMf(w))
    t.SetLayer(layer)
    t.SetNet(get_net(net))
    board.Add(t)

# J5.2 (HV_SHDN) east to the divider via web (8.88,-18.38); the
# direct diagonal crosses a +5V track, so waypoint candidates are
# tried until both legs clear.
x2, y2 = j5pads['2']
def try_bridge(net, x1, y1, x2, y2, w, layer, waypoints):
    if not seg_blocked(net, x1, y1, x2, y2, w, layer):
        add_track(net, x1, y1, x2, y2, w, layer)
        return (x2, y2)
    for (wx, wy) in waypoints:
        if not seg_blocked(net, x1, y1, wx, wy, w, layer) and \
                not seg_blocked(net, wx, wy, x2, y2, w, layer):
            add_track(net, x1, y1, wx, wy, w, layer)
            add_track(net, wx, wy, x2, y2, w, layer)
            return (wx, wy)
    raise AssertionError(f'{net} bridge: no clear path')

try:
    try_bridge('HV_SHDN', x2, y2, 8.88, -18.38, 0.25, pcbnew.F_Cu,
               [(6.04, -19.8), (7.6, -18.9), (6.04, -14.8),
                (8.2, -17.0), (5.2, -19.2)])
except AssertionError:
    try:
        try_bridge('HV_SHDN', x2, y2, 9.5, -18.9, 0.25, pcbnew.F_Cu,
                   [(6.04, -19.8), (7.6, -19.6), (8.6, -17.2)])
        log('  HV_SHDN bridge landed on the (9.5,-18.9) via')
    except AssertionError:
        # drop to In2 and land on the pass-80 detour's west corner
        done = None
        for (vx, vy) in ((7.2, -20.8), (6.5, -19.5), (8.2, -21.6),
                         (7.8, -19.0)):
            if disc_blocked('HV_SHDN', vx, vy):
                continue
            if seg_blocked('HV_SHDN', x2, y2, vx, vy, 0.25,
                           pcbnew.F_Cu):
                continue
            if seg_blocked('HV_SHDN', vx, vy, 9.5, -21.0, 0.25,
                           pcbnew.In2_Cu):
                continue
            done = (vx, vy)
            break
        assert done, 'HV_SHDN bridge: F and In2 landings all blocked'
        vx, vy = done
        add_track('HV_SHDN', x2, y2, vx, vy, 0.25, pcbnew.F_Cu)
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MMf(vx), MMf(vy)))
        v.SetWidth(MMf(0.6))
        v.SetDrill(MMf(0.3))
        v.SetNet(get_net('HV_SHDN'))
        board.Add(v)
        add_track('HV_SHDN', vx, vy, 9.5, -21.0, 0.25, pcbnew.In2_Cu)
        log(f'  HV_SHDN bridge dropped to In2 at ({vx},{vy})')
# J5.1 (HV_EN): east on F, via down, In2 to the severed run end
x1, y1 = j5pads['1']
landed = None
for (vx, vy) in ((8.55, y1), (8.55, -15.2), (7.8, y1), (8.55, -14.6),
                 (8.3, -13.8), (4.6, -14.2), (5.2, -13.6),
                 (4.6, -18.6), (5.5, -15.0), (6.2, -12.8)):
    if disc_blocked('HV_EN', vx, vy):
        continue
    if seg_blocked('HV_EN', x1, y1, vx, vy, 0.25, pcbnew.F_Cu):
        continue
    # land on the severed run: its south end (8.88,-17.12) or any
    # point of the long In2 segment at the via's own latitude
    tx, ty = (sx, -17.12) if vy < -16.5 else (8.88, vy)
    if seg_blocked('HV_EN', vx, vy, tx, ty, 0.25, pcbnew.In2_Cu):
        continue
    landed = (vx, vy, tx, ty)
    break
assert landed, 'HV_EN landing: no via site cleared'
vx, vy, tx, ty = landed
add_track('HV_EN', x1, y1, vx, vy, 0.25, pcbnew.F_Cu)
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MMf(vx), MMf(vy)))
v.SetWidth(MMf(0.6))
v.SetDrill(MMf(0.3))
v.SetNet(get_net('HV_EN'))
board.Add(v)
add_track('HV_EN', vx, vy, tx, ty, 0.25, pcbnew.In2_Cu)
log('  J5 bridged: HV_EN (U6.97 side) -> J5.1, J5.2 -> HV_SHDN web')

# ---------- TP1 relocation (TP_HV class fix) ----------
log('TP1 relocation:')
tp1 = board.FindFootprintByReference('TP1')
ox, oy = MMt(tp1.GetPosition().x), MMt(tp1.GetPosition().y)
# delete TP_HV track segments touching the old pad
for t in list(board.GetTracks()):
    if t.GetNetname() != 'TP_HV':
        continue
    for p in (t.GetStart(), t.GetEnd()):
        if MMt(p.x) == ox and MMt(p.y) == oy:
            _DEAD.append(t)
            board.Remove(t)
            log('  removed stub segment touching old TP1 pad')
            break
items = build_items(board)
# web endpoints: TP_HV track endpoints, nearest first to the new site
ends = set()
for kind, net, layers, shape, desc in items:
    pass
for t in board.GetTracks():
    if t.GetNetname() == 'TP_HV':
        for p in (t.GetStart(), t.GetEnd()):
            ends.add((MMt(p.x), MMt(p.y)))
NX, NY = 39.5, 20.5
tp1.SetPosition(pcbnew.VECTOR2I(MMf(NX), MMf(NY)))
# targets: web endpoints plus known web segment centres (landing
# mid-segment connects by overlap in the audit's union-find)
targets = sorted(ends, key=lambda e: math.dist(e, (NX, NY)))
targets += [(45.0, 19.25), (44.25, 18.0), (43.5, 17.25),
            (42.5, 16.25)]
joined = None
for (ex, ey) in targets:
    if math.dist((ex, ey), (NX, NY)) < 1.0:
        joined = (ex, ey)  # web already reaches the new pad
        break
    if not seg_blocked('TP_HV', NX, NY, ex, ey, 0.25, pcbnew.F_Cu):
        add_track('TP_HV', NX, NY, ex, ey, 0.25, pcbnew.F_Cu)
        joined = (ex, ey)
        break
    for (wx, wy) in ((42.5, 24.6), (39.5, 20.5), (43.0, 25.5),
                     (38.0, 24.0)):
        if not seg_blocked('TP_HV', NX, NY, wx, wy, 0.25,
                           pcbnew.F_Cu) and \
                not seg_blocked('TP_HV', wx, wy, ex, ey, 0.25,
                                pcbnew.F_Cu):
            add_track('TP_HV', NX, NY, wx, wy, 0.25, pcbnew.F_Cu)
            add_track('TP_HV', wx, wy, ex, ey, 0.25, pcbnew.F_Cu)
            joined = (ex, ey)
            break
    if joined:
        break
assert joined, 'TP1: no clear stub join'
log(f'  TP1 moved ({ox},{oy}) -> ({NX},{NY}), stub joined at {joined}')

# ---------- global pad-net assignment from the map ----------
n_assign = 0
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref not in nmap:
        continue
    for p in fp.Pads():
        want = nmap[ref]['pins'].get(p.GetNumber())
        if want and not want.startswith('unconnected-(') and \
                p.GetNetname() != want:
            p.SetNet(get_net(want))
            n_assign += 1
log(f'global assignment: {n_assign} pads (re)set from the map')

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
log(f'saved {OUT} (re-synced, zones refilled)')
open('results/resync-log.txt', 'w').write('\n'.join(LOG) + '\n')
