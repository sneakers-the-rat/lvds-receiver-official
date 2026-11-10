#!/usr/bin/env python3
"""Render exp254 (pass 217 frontier) zoomed on the XI gap: the final XI connection
that needs to be made, plus the wires around it. Same geometry renderer as
render_problems.py; pixel = (board_mm - origin_mm) * scale, y down as on screen."""
import math
import wx
_app = wx.App(False)
import pcbnew
from PIL import Image, ImageDraw, ImageFont

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp254.kicad_pcb'
OUT = '/home/hatch/workspace/your_files/board-problems/board-xi-gap.png'
IU = 1e6

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
COPPER_LAYERS = [pcbnew.B_Cu, pcbnew.In2_Cu, pcbnew.In1_Cu, pcbnew.F_Cu]
NET_HIGHLIGHT = [('XI', (0, 229, 255))]
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def hl(netname):
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
        self.d.line([self.px(x1, y1), self.px(x2, y2)], fill=color + (alpha,),
                    width=max(1, int(w_mm * self.scale)))

    def circle(self, x, y, r_mm, fill=None, outline=None, width=1):
        cx, cy = self.px(x, y)
        r = r_mm * self.scale
        self.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline, width=width)

    def poly(self, pts, fill=None, outline=None):
        self.d.polygon([self.px(x, y) for x, y in pts], fill=fill, outline=outline)

    def ellipse(self, x0, y0, x1, y1, outline=None, width=3):
        self.d.ellipse([self.px(x0, y0), self.px(x1, y1)], outline=outline, width=width)

    def dashed_line(self, x1, y1, x2, y2, color, dash_mm=0.9, gap_mm=0.6, width=4):
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

    def text(self, x, y, s, size=14, color=(235, 240, 245), anchor='la'):
        f = ImageFont.truetype(FONT, size)
        self.d.text(self.px(x, y), s, font=f, fill=color + (255,), anchor=anchor)


def draw_board(cv):
    tracks = list(b.GetTracks())
    for layer in COPPER_LAYERS:
        col = LAYER_COLORS[layer]
        for t in tracks:
            if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() != layer:
                continue
            s, e = t.GetStart(), t.GetEnd()
            cv.line(s.x / IU, s.y / IU, e.x / IU, e.y / IU, t.GetWidth() / IU, col, alpha=215)
    for t in tracks:
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            cv.circle(p.x / IU, p.y / IU, t.GetWidth() / IU / 2, fill=(212, 175, 55, 255))
            cv.circle(p.x / IU, p.y / IU, t.GetDrillValue() / IU / 2, fill=(13, 17, 23, 255))
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
            # translucent pads: the big exposed pads (e.g. U7's EP) must not bury
            # the tracks running underneath the chip
            big = max(sx, sy) > 3.0
            cv.poly(corners, fill=col + (60 if big else 205,))
    for t in tracks:
        col = hl(t.GetNetname())
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
            col = hl(pad.GetNetname())
            if col:
                p = pad.GetPosition()
                cv.circle(p.x / IU, p.y / IU, max(pad.GetSize().x, pad.GetSize().y) / IU / 2 + 0.15,
                          outline=col + (255,), width=3)
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref in ('U6', 'U7', 'C22', 'C20', 'C16', 'C23', 'X1', 'U5'):
            p = fp.GetPosition()
            cv.text(p.x / IU, p.y / IU, ref, size=max(12, int(cv.scale * 0.55)),
                    color=(255, 255, 255), anchor='ma')


def marker(cv, x, y, n, color):
    cx, cy = cv.px(x, y)
    r = max(12, int(cv.scale * 0.5))
    cv.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (255,),
                 outline=(255, 255, 255, 255), width=2)
    f = ImageFont.truetype(FONT, int(r * 1.15))
    cv.d.text((cx, cy), str(n), font=f, fill=(10, 10, 10, 255), anchor='mm')


z = Canvas(64, 1, 94, 30, 30)
draw_board(z)
CYN, MAG, ORANGE = (0, 229, 255), (255, 64, 200), (255, 140, 0)
# the loop under the chip that curls around the stitch via (pass-217 STP B chain country)
z.ellipse(74.9, 12.7, 77.3, 17.6, outline=ORANGE + (255,), width=3)
z.text(78.1, 17.9, 'the loop under the chip', size=15, color=ORANGE)
# the connection to make: straight dashed run, arc via -> U7.28 pad
z.dashed_line(75.625, 18.625, 76.25, 11.562, CYN)
marker(z, 75.625, 18.625, 1, CYN)     # XI arc via (bottom layer endpoint)
marker(z, 76.25, 11.562, 2, CYN)      # U7.28 XI pad
marker(z, 75.6, 14.75, 3, ORANGE)     # GND EP-stitch via the loop curls around
marker(z, 74.75, 4.662, 4, MAG)       # U6.40 USB_RST pad
z.img.save(OUT)
print('saved', OUT, z.img.size)
