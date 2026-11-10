"""gridroute: rasterized multi-layer A* over exact board geometry.

Purpose: existence questions of the form "does any corridor exist
for net N if partners P1..Pk may be re-laid" -- answered against
the board's real items (crossing-inclusive), with referee-class
inflation: every fixed item inflates by (item half-width + routed
half-width + pair clearance + eps). Pair clearance: 0.25 when
either net is a power net (+*, HV_*, APD_*), else 0.20; 0.30 when
routing on In2 against an In2 track (check_pcb buried rule).
Vias pierce all layers; a via cell must be free on the via grid
(every layer's inflation with via radius). Zones are ignored:
refill carves them around tracks at their own clearance.

The output is a configuration to BUILD and referee, never a
verdict: grid pitch and eps leave a small residue that the build
step absorbs. eps defaults to 0.02 at pitch 0.05.
"""
import heapq
import math

import numpy as np

LAYERS = ('F', 'In2', 'B')  # In1 is the solid GND plane: unusable


def is_power(net):
    return net.startswith('+') or net.startswith('HV') or \
        net.startswith('APD')


def pair_clr(item_net, layer, item_on_layer):
    """Clearance for routing a 0.2-class signal on `layer` past an
    item of `item_net` that exists on that layer. The check_pcb
    0.30 buried rule applies to In2 track vs In2 track only (board
    evidence: pass 219's DIR via sits 0.597 from an In2 track with
    no census line, so via pairs use the plain class)."""
    c = 0.25 if is_power(item_net) else 0.20
    if layer == 'In2' and item_on_layer == 'In2':
        c = max(c, 0.30)
    return c


def via_clr(item_net):
    return 0.25 if is_power(item_net) else 0.20


class Item:
    __slots__ = ('net', 'kind', 'layer', 'a', 'b', 'hw', 'rect')

    def __init__(self, net, kind, layer=None, a=None, b=None,
                 hw=0.0, rect=None):
        self.net, self.kind, self.layer = net, kind, layer
        self.a, self.b, self.hw, self.rect = a, b, hw, rect


def load_items(board_path, keep=None):
    """All tracks/vias/pads as Items (mm). keep(item)->bool filter
    for district relevance is the caller's job."""
    import wx
    wx.App(False)
    import pcbnew
    b = pcbnew.LoadBoard(board_path)
    LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1',
          pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
    items = []
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            items.append(Item(t.GetNetname(), 'via',
                              a=(p.x / 1e6, p.y / 1e6),
                              hw=t.GetWidth() / 2e6))
        else:
            s, e = t.GetStart(), t.GetEnd()
            items.append(Item(t.GetNetname(), 'trk',
                              layer=LN[t.GetLayer()],
                              a=(s.x / 1e6, s.y / 1e6),
                              b=(e.x / 1e6, e.y / 1e6),
                              hw=t.GetWidth() / 2e6))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            rect = (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                    bb.GetRight() / 1e6, bb.GetBottom() / 1e6)
            layers = []
            if p.IsOnLayer(pcbnew.F_Cu):
                layers.append('F')
            if p.IsOnLayer(pcbnew.B_Cu):
                layers.append('B')
            if p.IsOnLayer(pcbnew.In2_Cu):
                layers.append('In2')
            if not layers:
                layers = ['F', 'In2', 'B']
            for lay in layers:
                items.append(Item(p.GetNetname(), 'pad', layer=lay,
                                  rect=rect))
    if keep:
        items = [it for it in items if keep(it)]
    return items


class Raster:
    """Blocked grids: track grids per layer + one via grid."""

    def __init__(self, x0, y0, x1, y1, pitch=0.05, eps=0.02,
                 routed_hw=0.10):
        self.x0, self.y0, self.pitch = x0, y0, pitch
        self.nx = int(math.ceil((x1 - x0) / pitch))
        self.ny = int(math.ceil((y1 - y0) / pitch))
        self.eps, self.routed_hw = eps, routed_hw
        self.track = {L: np.zeros((self.ny, self.nx), bool)
                      for L in LAYERS}
        self.via = np.zeros((self.ny, self.nx), bool)

    def centre(self, i, j):
        return (self.x0 + (i + 0.5) * self.pitch,
                self.y0 + (j + 0.5) * self.pitch)

    def cell(self, x, y):
        return (int((x - self.x0) / self.pitch),
                int((y - self.y0) / self.pitch))

    def _window(self, cx, cy, r):
        i0 = max(0, int((cx - r - self.x0) / self.pitch) - 1)
        i1 = min(self.nx - 1, int((cx + r - self.x0) / self.pitch) + 1)
        j0 = max(0, int((cy - r - self.y0) / self.pitch) - 1)
        j1 = min(self.ny - 1, int((cy + r - self.y0) / self.pitch) + 1)
        return i0, i1, j0, j1

    def _stamp_disc(self, grid, cx, cy, r):
        i0, i1, j0, j1 = self._window(cx, cy, r)
        if i1 < i0 or j1 < j0:
            return
        xs = self.x0 + (np.arange(i0, i1 + 1) + 0.5) * self.pitch
        ys = self.y0 + (np.arange(j0, j1 + 1) + 0.5) * self.pitch
        X, Y = np.meshgrid(xs, ys)
        grid[j0:j1 + 1, i0:i1 + 1] |= (X - cx) ** 2 + (Y - cy) ** 2 <= r * r

    def _stamp_seg(self, grid, a, b, r):
        ax, ay = a
        bx, by = b
        cx, cy = (ax + bx) / 2, (ay + by) / 2
        rad = math.hypot(bx - ax, by - ay) / 2 + r
        i0, i1, j0, j1 = self._window(cx, cy, rad)
        if i1 < i0 or j1 < j0:
            return
        xs = self.x0 + (np.arange(i0, i1 + 1) + 0.5) * self.pitch
        ys = self.y0 + (np.arange(j0, j1 + 1) + 0.5) * self.pitch
        X, Y = np.meshgrid(xs, ys)
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        if L2 == 0:
            d2 = (X - ax) ** 2 + (Y - ay) ** 2
        else:
            t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
            d2 = (X - (ax + t * dx)) ** 2 + (Y - (ay + t * dy)) ** 2
        grid[j0:j1 + 1, i0:i1 + 1] |= d2 <= r * r

    def _stamp_rect(self, grid, rect, r):
        x0, y0, x1, y1 = rect
        i0, i1, j0, j1 = self._window((x0 + x1) / 2, (y0 + y1) / 2,
                                      math.hypot(x1 - x0, y1 - y0) / 2 + r)
        if i1 < i0 or j1 < j0:
            return
        xs = self.x0 + (np.arange(i0, i1 + 1) + 0.5) * self.pitch
        ys = self.y0 + (np.arange(j0, j1 + 1) + 0.5) * self.pitch
        X, Y = np.meshgrid(xs, ys)
        dx = np.maximum(np.maximum(x0 - X, X - x1), 0)
        dy = np.maximum(np.maximum(y0 - Y, Y - y1), 0)
        grid[j0:j1 + 1, i0:i1 + 1] |= dx * dx + dy * dy <= r * r

    def add_item(self, it, routed_hw=None):
        """Block cells for one fixed item (track grids + via grid)."""
        rh = self.routed_hw if routed_hw is None else routed_hw
        if it.kind == 'trk':
            r = it.hw + rh + pair_clr(it.net, it.layer, it.layer) + self.eps
            self._stamp_seg(self.track[it.layer], it.a, it.b, r)
            rv = 0.25 + it.hw + via_clr(it.net) + self.eps
            self._stamp_seg(self.via, it.a, it.b, rv)
        elif it.kind == 'via':
            for L in LAYERS:
                r = it.hw + rh + via_clr(it.net) + self.eps
                self._stamp_disc(self.track[L], it.a[0], it.a[1], r)
            rv = 0.25 + it.hw + via_clr(it.net) + self.eps
            self._stamp_disc(self.via, it.a[0], it.a[1], rv)
        elif it.kind == 'pad':
            r = rh + pair_clr(it.net, it.layer, it.layer) + self.eps
            self._stamp_rect(self.track[it.layer], it.rect, r)
            rv = 0.25 + via_clr(it.net) + self.eps
            self._stamp_rect(self.via, it.rect, rv)

    def add_routed(self, net, layer_segs, vias, hw=0.10):
        """Mark a routed net's copper as obstacle for later nets."""
        for (L, a, b) in layer_segs:
            it = Item(net, 'trk', layer=L, a=a, b=b, hw=hw)
            self.add_item(it, routed_hw=0.125)
        for (x, y) in vias:
            it = Item(net, 'via', a=(x, y), hw=0.25)
            self.add_item(it, routed_hw=0.125)

    def copy(self):
        r = Raster.__new__(Raster)
        r.x0, r.y0, r.pitch = self.x0, self.y0, self.pitch
        r.nx, r.ny, r.eps, r.routed_hw = self.nx, self.ny, self.eps, \
            self.routed_hw
        r.track = {L: g.copy() for L, g in self.track.items()}
        r.via = self.via.copy()
        return r


def astar(raster, start, goal, via_cost=3.0):
    """start/goal = (x, y, layer). Returns [(x, y, layer), ...]."""
    si, sj = raster.cell(start[0], start[1])
    gi, gj = raster.cell(goal[0], goal[1])
    sl, gl = LAYERS.index(start[2]), LAYERS.index(goal[2])
    grids = [raster.track[L] for L in LAYERS]
    via = raster.via
    ny, nx = via.shape
    INF = float('inf')
    g = {}
    came = {}
    s0 = (si, sj, sl)
    g[s0] = 0.0
    gx, gy = raster.centre(gi, gj)

    def h(i, j):
        cx, cy = raster.centre(i, j)
        return math.hypot(cx - gx, cy - gy)

    pq = [(h(si, sj), 0.0, s0)]
    DIRS = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
            (1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)),
            (-1, 1, math.sqrt(2)), (-1, -1, math.sqrt(2))]
    p = raster.pitch
    while pq:
        _, gc, cur = heapq.heappop(pq)
        if gc > g.get(cur, INF):
            continue
        i, j, l = cur
        if (i, j, l) == (gi, gj, gl):
            path = [cur]
            while path[-1] != s0:
                path.append(came[path[-1]])
            path.reverse()
            return [(raster.centre(a, b)[0], raster.centre(a, b)[1],
                     LAYERS[c]) for (a, b, c) in path]
        grid = grids[l]
        for di, dj, w in DIRS:
            ni, nj = i + di, j + dj
            if not (0 <= ni < nx and 0 <= nj < ny) or grid[nj, ni]:
                continue
            if di and dj and (grid[j, ni] or grid[nj, i]):
                continue  # no corner cutting
            ncur = (ni, nj, l)
            ng = gc + w * p
            if ng < g.get(ncur, INF):
                g[ncur] = ng
                came[ncur] = cur
                heapq.heappush(pq, (ng + h(ni, nj), ng, ncur))
        if not via[j, i]:
            for l2 in range(3):
                if l2 == l:
                    continue
                ncur = (i, j, l2)
                ng = gc + via_cost * p
                if ng < g.get(ncur, INF):
                    g[ncur] = ng
                    came[ncur] = cur
                    heapq.heappush(pq, (ng + h(i, j), ng, ncur))
    return None


def path_to_geometry(path):
    """Cell path -> (layer_segs, vias): consecutive same-layer runs
    become point lists; layer changes become vias."""
    segs = []
    vias = []
    run = [path[0]]
    for prev, cur in zip(path, path[1:]):
        if cur[2] != prev[2]:
            vias.append((prev[0], prev[1]))
            segs.append((prev[2], run))
            run = [cur]
        else:
            run.append(cur)
    segs.append((path[-1][2], run))
    out = []
    for (L, pts) in segs:
        # collinear-merge the run
        mp = [pts[0]]
        for a, b, c in zip(pts, pts[1:], pts[2:] + [None]):
            if c is None:
                mp.append(b)
                break
            v1 = (b[0] - a[0], b[1] - a[1])
            v2 = (c[0] - b[0], c[1] - b[1])
            if abs(v1[0] * v2[1] - v1[1] * v2[0]) > 1e-9:
                mp.append(b)
        out.append((L, [(x, y) for (x, y, _) in mp]))
    return out, vias
