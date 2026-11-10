"""build_lib: shared board-surgery primitives for build drivers.

One parameterized implementation of the idiom every pass build has
re-copied (bb's t_bb24 form): netcode capture BEFORE any Remove,
victim rip with asserted counts, track/via emission with widths
taken from victims, mandatory zone refill, save, reload, and a
whole-board per-net track census diff (the Save net-rename check:
any net whose count changes unexpectedly is named).

Usage:
    import build_lib as BL
    S = BL.Surgery('hw/pdlvds_rx.expNNN.kicad_pcb',
                   'hw/pdlvds_rx.expMMM.kicad_pcb', nets=('XI', ...))
    S.rip_seg('ULPI_NXT', BL.F, (75.25, 16.875), (74.65, 17.8))
    S.rip_via('ULPI_DIR', (75.5, 17.521))
    w = S.width_of_last_rip()
    S.add_track('ULPI_NXT', BL.F, a, b, w)
    S.add_via('ULPI_DIR', 74.90, 17.521)
    S.finish()   # refill, save, reload, print census diff
"""
import wx
_app = wx.App(False)
import pcbnew

F, IN1, IN2, B = pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
MM = pcbnew.FromMM


def _mm(v):
    return v / 1e6


class Surgery:
    def __init__(self, src, dst, nets=()):
        self.b = pcbnew.LoadBoard(src)
        self.dst = dst
        self.nets = tuple(nets)
        self.NC = {n: self.b.GetNetcodeFromNetname(n) for n in self.nets}
        self.base = self._census()
        self._last_width = None
        print('netcodes:', self.NC)

    def _census(self):
        out = {}
        for t in self.b.GetTracks():
            n = t.GetNetname()
            kind = 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk'
            out[(n, kind)] = out.get((n, kind), 0) + 1
        return out

    def ends(self, t):
        s, e = t.GetStart(), t.GetEnd()
        return (_mm(s.x), _mm(s.y)), (_mm(e.x), _mm(e.y))

    @staticmethod
    def _near(p, q, tol=0.03):
        return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol

    def find_tracks(self, net, layer, pred):
        nc = self.NC[net]
        return [t for t in self.b.GetTracks()
                if t.GetNetCode() == nc and t.Type() == pcbnew.PCB_TRACE_T
                and t.GetLayer() == layer and pred(t)]

    # NOTE (KiCad 8 SWIG): after BOARD.Remove(), a fresh GetTracks()
    # can return a non-iterable wrapper. The safe pattern is: FIND
    # every victim first, then REMOVE them all, then add. The find_*
    # methods below only locate; remove() performs the rips.
    def find_seg(self, net, layer, a, b, expect=1, tol=0.03):
        def pred(t):
            s, e = self.ends(t)
            return (self._near(s, a, tol) and self._near(e, b, tol)) or \
                   (self._near(s, b, tol) and self._near(e, a, tol))
        victims = self.find_tracks(net, layer, pred)
        assert len(victims) == expect, \
            f'find_seg {net} {a}->{b}: {len(victims)} victims, expect {expect}'
        self._last_width = _mm(victims[0].GetWidth())
        print(f'found {net} seg {a}->{b} (w={self._last_width})')
        return victims

    def find_via(self, net, at, expect=1, tol=0.03):
        nc = self.NC[net]
        victims = [t for t in self.b.GetTracks()
                   if t.GetNetCode() == nc and t.Type() == pcbnew.PCB_VIA_T
                   and self._near((_mm(t.GetPosition().x),
                                   _mm(t.GetPosition().y)), at, tol)]
        assert len(victims) == expect, \
            f'find_via {net} @{at}: {len(victims)} victims, expect {expect}'
        print(f'found {net} via @{at}')
        return victims

    def remove(self, victims):
        for t in victims:
            self.b.Remove(t)
        print(f'removed {len(victims)} items')
        return victims

    def rip_seg(self, net, layer, a, b, expect=1, tol=0.03):
        return self.remove(self.find_seg(net, layer, a, b, expect, tol))

    def rip_via(self, net, at, expect=1, tol=0.03):
        return self.remove(self.find_via(net, at, expect, tol))

    def find_where(self, net, layer, pred, expect, label):
        victims = self.find_tracks(net, layer, pred)
        assert len(victims) == expect, \
            f'find_where {label}: {len(victims)} victims, expect {expect}'
        if victims:
            self._last_width = _mm(victims[0].GetWidth())
        print(f'found {label}: {len(victims)} (w={self._last_width})')
        return victims

    def width_of_last_rip(self):
        return self._last_width

    def add_track(self, net, layer, a, b, width):
        t = pcbnew.PCB_TRACK(self.b)
        t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
        t.SetWidth(MM(width))
        t.SetLayer(layer)
        t.SetNetCode(self.NC[net])
        self.b.Add(t)
        return t

    def add_polyline(self, net, layer, pts, width):
        for a, b in zip(pts, pts[1:]):
            self.add_track(net, layer, a, b, width)

    def add_via(self, net, x, y, dia=0.5, drill=0.3):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(dia))
        v.SetDrill(MM(drill))
        v.SetNetCode(self.NC[net])
        self.b.Add(v)
        return v

    def finish(self):
        filler = pcbnew.ZONE_FILLER(self.b)
        filler.Fill(self.b.Zones())
        self.b.Save(self.dst)
        print('saved', self.dst)
        b2 = pcbnew.LoadBoard(self.dst)
        now = {}
        for t in b2.GetTracks():
            n = t.GetNetname()
            kind = 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk'
            now[(n, kind)] = now.get((n, kind), 0) + 1
        diffs = []
        for k in sorted(set(self.base) | set(now)):
            if self.base.get(k) != now.get(k):
                diffs.append((k, self.base.get(k), now.get(k)))
        print('reload census diff (net, kind): base -> now')
        for k, a, c in diffs:
            print(f'  {k}: {a} -> {c}')
        return diffs
