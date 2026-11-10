#!/usr/bin/env python3
"""Render exp252 from board geometry (pcbnew) and annotate the three open nets.

Outputs:
  ~/workspace/your_files/board-problems/board-full.png     (whole board, district boxed)
  ~/workspace/your_files/board-problems/board-zoom.png     (U7/U6 district, numbered markers)
Coordinate mapping is exact: pixel = (board_mm - origin_mm) * scale. Board y grows downward,
same as KiCad screen orientation.
"""
import math
import wx
_app = wx.App(False)
import pcbnew
from PIL import Image, ImageDraw, ImageFont

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp252.kicad_pcb'
OUTDIR = '/home/hatch/workspace/your_files/board-problems'
IU = 1e6  # KiCad internal units per mm

b = pcbnew.LoadBoard(BOARD)
bb = b.GetBoardEdgesBoundingBox()
BX0, BY0 = bb.GetLeft() / IU, bb.GetTop() / IU
BX1, BY1 = bb.GetRight() / IU, bb.GetBottom() / IU

LAYER_COLORS = {
    pcbnew.F_Cu: (219, 68, 44),
    pcbnew.In1_Cu: (46, 139, 87),
    pcbnew.In2_Cu: (155, 89, 182),
    pcbnew.B_Cu: (52, 110, 219),
}
COPPER_LAYERS = [pcbnew.B_Cu, pcbnew.In2_Cu, pcbnew.In1_Cu, pcbnew.F_Cu]  # draw bottom-up
NET_HIGHLIGHT = [
    ('PHY_1V8', (255, 214, 0)),    # yellow
    ('XI', (0, 229, 255)),         # cyan
    ('USB_RST', (255, 64, 200)),   # magenta
]
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_REG = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def net_highlight(netname):
    for prefix, col in NET_HIGHLIGHT:
        if netname == prefix or netname.startswith(prefix):
            return col
    return None


class Canvas:
    def __init__(self, x0, y0, x1, y1, scale, bg=(13, 17, 23)):
        self.x0, self.y0, self.scale = x0, y0, scale
        self.img = Image.new('RGB', (int((x1 - x0) * scale), int((y1 - y0) * scale)), bg)
        self.d = ImageDraw.Draw(self.img, 'RGBA')

    def px(self, x, y):
        return ((x - self.x0) * self.scale, (y - self.y0) * self.scale)

    def line(self, x1, y1, x2, y2, w_mm, color, alpha=255):
        a, b_ = self.px(x1, y1), self.px(x2, y2)
        self.d.line([a, b_], fill=color + (alpha,), width=max(1, int(w_mm * self.scale)))

    def circle(self, x, y, r_mm, fill=None, outline=None, width=1):
        cx, cy = self.px(x, y)
        r = r_mm * self.scale
        self.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline, width=width)

    def poly(self, pts, fill=None, outline=None):
        self.d.polygon([self.px(x, y) for x, y in pts], fill=fill, outline=outline)

    def rect(self, x0, y0, x1, y1, outline=None, width=2):
        a, b_ = self.px(x0, y0), self.px(x1, y1)
        self.d.rectangle([a, b_], outline=outline, width=width)

    def dashed_line(self, x1, y1, x2, y2, color, dash_mm=0.9, gap_mm=0.6, width=3):
        ax, ay = self.px(x1, y1)
        bx, by = self.px(x2, y2)
        total = math.hypot(bx - ax, by - ay)
        dash, gap = dash_mm * self.scale, gap_mm * self.scale
        t = 0.0
        while t < total:
            t2 = min(t + dash, total)
            self.d.line([(ax + (bx - ax) * t / total, ay + (by - ay) * t / total),
                         (ax + (bx - ax) * t2 / total, ay + (by - ay) * t2 / total)],
                        fill=color + (255,), width=width)
            t += dash + gap

    def text(self, x, y, s, size=13, color=(235, 240, 245), bold=True, anchor='la'):
        f = ImageFont.truetype(FONT if bold else FONT_REG, size)
        self.d.text(self.px(x, y), s, font=f, fill=color + (255,), anchor=anchor)


def draw_board(cv):
    # board edge
    cv.rect(BX0, BY0, BX1, BY1, outline=(200, 208, 216, 255), width=2)
    # zone fills (F/B only, faint) - context pours
    try:
        for zone in b.Zones():
            for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
                if not zone.GetIsRuleArea() and zone.IsOnLayer(layer):
                    polys = zone.GetFilledPolysList(layer)
                    for i in range(polys.OutlineCount()):
                        chain = polys.Outline(i)
                        pts = [(chain.Point(j).x / IU, chain.Point(j).y / IU)
                               for j in range(chain.PointCount())]
                        if len(pts) > 2:
                            cv.poly(pts, fill=(120, 130, 110, 26))
    except Exception as e:
        print('zone fill skipped:', e)
    # tracks, bottom layer first
    tracks = list(b.GetTracks())
    for layer in COPPER_LAYERS:
        col = LAYER_COLORS[layer]
        for t in tracks:
            if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() != layer:
                continue
            s, e = t.GetStart(), t.GetEnd()
            cv.line(s.x / IU, s.y / IU, e.x / IU, e.y / IU, t.GetWidth() / IU, col, alpha=215)
    # vias
    for t in tracks:
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            cv.circle(p.x / IU, p.y / IU, t.GetWidth() / IU / 2, fill=(212, 175, 55, 255))
            cv.circle(p.x / IU, p.y / IU, t.GetDrillValue() / IU / 2, fill=(13, 17, 23, 255))
    # pads
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            ls = pad.GetLayerSet()
            on_f, on_b = ls.Contains(pcbnew.F_Cu), ls.Contains(pcbnew.B_Cu)
            if not (on_f or on_b):
                continue
            p = pad.GetPosition()
            sx, sy = pad.GetSize().x / IU, pad.GetSize().y / IU
            ang = math.radians(pad.GetOrientation().AsDegrees())
            ca, sa = math.cos(ang), math.sin(ang)
            corners = []
            for dx, dy in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)):
                corners.append((p.x / IU + dx * ca - dy * sa, p.y / IU + dx * sa + dy * ca))
            col = (212, 175, 55) if (on_f and on_b) else ((240, 120, 90) if on_f else (110, 150, 240))
            cv.poly(corners, fill=col + (255,))
    # highlight the three open nets on top
    for t in tracks:
        col = net_highlight(t.GetNetname())
        if not col:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            cv.circle(p.x / IU, p.y / IU, t.GetWidth() / IU / 2 + 0.12, outline=col + (255,), width=3)
        else:
            s, e = t.GetStart(), t.GetEnd()
            cv.line(s.x / IU, s.y / IU, e.x / IU, e.y / IU, t.GetWidth() / IU + 0.1, col, alpha=255)
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            col = net_highlight(pad.GetNetname())
            if col:
                p = pad.GetPosition()
                cv.circle(p.x / IU, p.y / IU, max(pad.GetSize().x, pad.GetSize().y) / IU / 2 + 0.15,
                          outline=col + (255,), width=3)
    # refdes labels for the parts that matter
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref in ('U6', 'U7', 'U4', 'U5', 'C22', 'C20', 'C16', 'C23', 'X1', 'X2', 'R20', 'C14'):
            p = fp.GetPosition()
            cv.text(p.x / IU, p.y / IU, ref, size=max(11, int(cv.scale * 0.55)),
                    color=(255, 255, 255), anchor='ma')


def marker(cv, x, y, n, color):
    cx, cy = cv.px(x, y)
    r = max(11, int(cv.scale * 0.5))
    cv.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (255,), outline=(255, 255, 255, 255), width=2)
    f = ImageFont.truetype(FONT, int(r * 1.15))
    cv.d.text((cx, cy), str(n), font=f, fill=(10, 10, 10, 255), anchor='mm')


import os
os.makedirs(OUTDIR, exist_ok=True)

# ---------- full board ----------
full = Canvas(BX0 - 1, BY0 - 1, BX1 + 1, BY1 + 1, 10)
draw_board(full)
full.rect(56, -8, 98, 36, outline=(255, 255, 0, 255), width=3)
full.text(56.5, -6.8, 'PROBLEM DISTRICT (zoom below)', size=15, color=(255, 255, 0))
full.img.save(f'{OUTDIR}/board-full.png')
print('full saved', full.img.size)

# ---------- zoom ----------
z = Canvas(56, -8, 98, 36, 26)
draw_board(z)
# the saturated braid box
z.rect(70.5, 9.5, 80.5, 20.0, outline=(255, 255, 255, 200), width=2)
z.text(70.7, 8.15, 'the saturated braid', size=15, color=(255, 255, 255))
# missing connections, dashed
z.dashed_line(71.375, 17.625, 77.90, 10.08, (255, 214, 0))    # PHY feed that must exist
z.dashed_line(75.625, 18.625, 76.25, 11.562, (0, 229, 255))   # XI drop that must exist
YEL, CYN, MAG = (255, 214, 0), (0, 229, 255), (255, 64, 200)
marker(z, 72.5, 18.0, 1, YEL)        # C22
marker(z, 71.375, 17.625, 2, YEL)    # cut tail end
marker(z, 77.90, 10.08, 3, YEL)      # PHY main run (goal via)
marker(z, 75.27, 10.33, 4, (255, 255, 255))  # notch via moved in pass 215
marker(z, 76.25, 11.562, 5, CYN)     # U7.28 XI pad
marker(z, 75.625, 18.625, 6, CYN)    # XI bottom-layer arc via
marker(z, 74.75, 4.662, 7, MAG)      # U6.40 USB_RST pad
z.img.save(f'{OUTDIR}/board-zoom.png')
print('zoom saved', z.img.size)
