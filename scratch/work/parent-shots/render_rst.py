#!/usr/bin/env python3
"""The one remaining connection (pass 219 frontier, exp257): USB_RST.
The net has NO tracks or vias at all -- just two bare pads: U6.40 (STM32,
(74.750,4.662)) and U7.9 (USB3300 reset, (74.250,16.438)). The ULPI_CK via
(75.125,5.875) d0.6 sits immediately north of U6.40 and seals its direct
exit; the approved build moves CK's U6-side escape east (~(75.4,5.9)).
Style per user rules: pads as bare outlines, vias slate, no yellow;
only the subject net highlighted."""
import math
import wx
_app = wx.App(False)
import pcbnew
from PIL import Image, ImageDraw, ImageFont

BOARD = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
OUT = '/home/hatch/workspace/your_files/board-problems/board-usbrst-gap-v1.png'
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
RST = (0, 229, 255)
WHITE = (240, 244, 248)


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


z = Canvas(70.5, 2.0, 80.5, 20.0, 64)
tracks = list(b.GetTracks())
for layer in ORDER:
    col = LAYER_COLORS[layer]
    for t in tracks:
        if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() != layer:
            continue
        s, e = t.GetStart(), t.GetEnd()
        z.line(s.x / IU, s.y / IU, e.x / IU, e.y / IU, t.GetWidth() / IU, col, alpha=255)
for t in tracks:
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        z.circle(p.x / IU, p.y / IU, t.GetWidth() / IU / 2, fill=(150, 160, 175, 255))
        z.circle(p.x / IU, p.y / IU, t.GetDrillValue() / IU / 2, fill=(13, 17, 23, 255))
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
# the two USB_RST pads (the net has no copper at all)
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() == 'USB_RST':
            p = pad.GetPosition()
            z.circle(p.x / IU, p.y / IU, max(pad.GetSize().x, pad.GetSize().y) / IU / 2 + 0.18,
                     outline=RST + (255,), width=4)
# the fence: ULPI_CK via (75.125,5.875)
z.circle(75.125, 5.875, 0.55, outline=WHITE + (255,), width=3)
for fp in b.GetFootprints():
    if fp.GetReference() in ('U6', 'U7'):
        p = fp.GetPosition()
        z.text(p.x / IU, p.y / IU, fp.GetReference(), size=17, anchor='ma')


def marker(x, y, n, color):
    cx, cy = z.px(x, y)
    r = 17
    z.d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (255,),
                outline=(255, 255, 255, 255), width=3)
    f = ImageFont.truetype(FONT, 20)
    z.d.text((cx, cy), str(n), font=f, fill=(10, 10, 10, 255), anchor='mm')


z.dashed_line(74.750, 4.662, 74.250, 16.438, RST)
marker(74.750, 4.662, 1, RST)      # U6.40 - STM32 pin that drives the reset
marker(74.250, 16.438, 2, RST)     # U7.9 - USB3300 reset pad
marker(75.125, 5.875, 3, WHITE)    # ULPI_CK via - seals U6.40's north exit
z.text(73.1, 3.6, 'U6.40', size=15)
z.text(72.6, 15.4, 'U7.9', size=15)
z.img.save(OUT)
print('saved', OUT, z.img.size)
