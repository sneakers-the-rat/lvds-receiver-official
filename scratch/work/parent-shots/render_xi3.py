#!/usr/bin/env python3
"""Tight render of the XI gap on exp254: U7 and the corridor under it, nothing else.
Fixes vs earlier renders: unique output name, much tighter crop, NO gold/yellow
anywhere (vias and pads are neutral), pads drawn as outlines only so the copper
under the chip is fully visible."""
import math
import wx
_app = wx.App(False)
import pcbnew
from PIL import Image, ImageDraw, ImageFont

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp254.kicad_pcb'
OUT = '/home/hatch/workspace/your_files/board-problems/board-xi-gap-v3.png'
IU = 1e6
b = pcbnew.LoadBoard(BOARD)

LAYER_COLORS = {
    pcbnew.F_Cu: (219, 68, 44),
    pcbnew.In1_Cu: (46, 160, 90),
    pcbnew.In2_Cu: (170, 100, 210),
    pcbnew.B_Cu: (52, 110, 219),
}
ORDER = [pcbnew.B_Cu, pcbnew.In2_Cu, pcbnew.In1_Cu, pcbnew.F_Cu]
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
XI = (0, 229, 255)


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

    def poly_outline(self, pts, outline, width=1):
        p = [self.px(x, y) for x, y in pts]
        self.d.line(p + [p[0]], fill=outline + (255,), width=width)

    def dashed_line(self, x1, y1, x2, y2, color, dash_mm=0.8, gap_mm=0.55, width=5):
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

    def text(self, x, y, s, size=16, color=(235, 240, 245), anchor='la'):
        f = ImageFont.truetype(FONT, size)
        self.d.text(self.px(x, y), s, font=f, fill=color + (255,), anchor=anchor)


z = Canvas(70.5, 7.5, 83.0, 21.5, 72)
tracks = list(b.GetTracks())
# 1) all copper tracks, saturated, bottom layer first
for layer in ORDER:
    col = LAYER_COLORS[layer]
    for t in tracks:
        if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() != layer:
            continue
        s, e = t.GetStart(), t.GetEnd()
        z.line(s.x / IU, s.y / IU, e.x / IU, e.y / IU, t.GetWidth() / IU, col, alpha=255)
# 2) vias in neutral slate - no gold anywhere
for t in tracks:
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        z.circle(p.x / IU, p.y / IU, t.GetWidth() / IU / 2, fill=(150, 160, 175, 255))
        z.circle(p.x / IU, p.y / IU, t.GetDrillValue() / IU / 2, fill=(13, 17, 23, 255))
# 3) pads as bare outlines only - nothing buries the under-chip copper
for fp in b.GetFootprints():
    for pad in fp.Pads():
        ls = pad.GetLayerSet()
        if not (ls.Contains(pcbnew.F_Cu) or ls.Contains(pcbnew.B_Cu)):
            continue
        p = pad.GetPosition()
        sx, sy = pad.GetSize().x / IU, pad.GetSize().y / IU
        ang = math.radians(pad.GetOrientation().AsDegrees())
        ca, sa = math.cos(ang), math.sin(ang)
        corners = []
        for dx, dy in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)):
            corners.append((p.x / IU + dx * ca - dy * sa, p.y / IU + dx * sa + dy * ca))
        big = max(sx, sy) > 3.0
        z.poly_outline(corners, (110, 118, 130) if big else (185, 192, 205), width=1 if big else 2)
# 4) XI on top
for t in tracks:
    if t.GetNetname() != 'XI':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        z.circle(p.x / IU, p.y / IU, t.GetWidth() / IU / 2 + 0.12, outline=XI + (255,), width=4)
    else:
        s, e = t.GetStart(), t.GetEnd()
        z.line(s.x / IU, s.y / IU, e.x / IU, e.y / IU, t.GetWidth() / IU + 0.12, XI, alpha=255)
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() == 'XI':
            p = pad.GetPosition()
            z.circle(p.x / IU, p.y / IU, max(pad.GetSize().x, pad.GetSize().y) / IU / 2 + 0.16,
                     outline=XI + (255,), width=4)
# labels
for fp in b.GetFootprints():
    if fp.GetReference() in ('U7', 'C20', 'C22'):
        p = fp.GetPosition()
        z.text(p.x / IU, p.y / IU, fp.GetReference(), size=17, anchor='ma')


def marker(x, y, n, color):
    cx, cy = z.px(x, y)
    r = 17
    z.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (255,),
                outline=(255, 255, 255, 255), width=3)
    f = ImageFont.truetype(FONT, 20)
    z.d.text((cx, cy), str(n), font=f, fill=(10, 10, 10, 255), anchor='mm')


ORANGE = (255, 140, 0)
# the under-chip loop (pass-217 STP B chain country), now with nothing drawn over it
z.d.ellipse([z.px(74.9, 12.7), z.px(77.3, 17.6)], outline=ORANGE + (255,), width=4)
z.text(77.7, 16.9, 'the loop\nunder the chip', size=17, color=ORANGE)
z.dashed_line(75.625, 18.625, 76.25, 11.562, XI)
marker(75.625, 18.625, 1, XI)
marker(76.25, 11.562, 2, XI)
marker(75.6, 14.75, 3, ORANGE)
z.img.save(OUT)
print('saved', OUT, z.img.size)
