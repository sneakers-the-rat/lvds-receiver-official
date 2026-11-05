#!/usr/bin/env python3
"""TMP117 DRV0006B footprint proof (finding F-04, docs/08).

Parses hw/pdlvds.pretty/TMP117_WSON6.kicad_mod and checks, against the
TI SNOSD82D package outline (p.40) and land pattern example (p.41):

  * signal pads are 0.45 (X) x 0.30 (Y) mm          [p.41: 6X (0.45), 6X (0.3)]
  * column centrelines are 1.95 mm apart (x = +/-0.975)  [p.41: (1.95)]
  * row pitch is 0.65 mm (y = -0.65, 0, +0.65)      [p.40/p.41: 4X 0.65]
  * exposed-pad land matches the package exposed thermal pad
    1.0 (X) x 1.6 (Y) mm                            [p.40: 1 +/-0.1, 1.6 +/-0.1]
  * NO pair of pads overlaps (rect intersection area == 0 for all pairs)

Exit 0 and prints PASS only if every check holds.
"""
import re, sys, itertools

PATH = "hw/pdlvds.pretty/TMP117_WSON6.kicad_mod"
txt = open(PATH).read()
pads = {}
for m in re.finditer(r'\(pad "(\d+)" [^()]*\(at (-?[\d.]+) (-?[\d.]+)\) \(size ([\d.]+) ([\d.]+)\)', txt):
    pads[m.group(1)] = tuple(float(m.group(i)) for i in (2, 3, 4, 5))  # x, y, w, h

assert len(pads) == 7, f"expected 7 pads, found {len(pads)}"
print(f"{'pad':>4} {'x':>7} {'y':>7} {'w(X)':>6} {'h(Y)':>6}   rect x:[lo,hi] y:[lo,hi]")
rects = {}
for n in sorted(pads, key=int):
    x, y, w, h = pads[n]
    rects[n] = (x - w / 2, x + w / 2, y - h / 2, y + h / 2)
    print(f"{n:>4} {x:7.3f} {y:7.3f} {w:6.2f} {h:6.2f}   [{rects[n][0]:+.3f},{rects[n][1]:+.3f}] [{rects[n][2]:+.3f},{rects[n][3]:+.3f}]")

fails = []
# TI callout checks
for n in "123456":
    x, y, w, h = pads[n]
    if (w, h) != (0.45, 0.30):
        fails.append(f"pad {n} size {w}x{h} != 0.45x0.30 (TI land pattern 6X 0.45 / 6X 0.3)")
    if abs(abs(x) - 0.975) > 1e-9:
        fails.append(f"pad {n} |x|={abs(x)} != 0.975 (column span 1.95)")
    if abs(y) not in (0.0, 0.65):
        fails.append(f"pad {n} y={y} not on 0.65 pitch grid")
if pads["7"][2:] != (1.0, 1.6):
    fails.append(f"EP size {pads['7'][2]}x{pads['7'][3]} != 1.0x1.6 (TI package outline)")
if pads["7"][:2] != (0.0, 0.0):
    fails.append("EP not centred")

# pairwise overlap
worst = 0.0
for a, b in itertools.combinations(sorted(pads, key=int), 2):
    ax0, ax1, ay0, ay1 = rects[a]
    bx0, bx1, by0, by1 = rects[b]
    ox = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    oy = max(0.0, min(ay1, by1) - max(ay0, by0))
    area = ox * oy
    worst = max(worst, area)
    if area > 0:
        fails.append(f"pads {a}/{b} OVERLAP by {ox:.3f} x {oy:.3f} mm (area {area:.4f} mm^2)")

# signal-to-EP clearance (X direction is the binding one)
ep = rects["7"]
clr = min(rects[n][0] - ep[1] for n in ("4", "5", "6"))
print(f"\nmin signal-to-EP clearance (X): {clr:.3f} mm")
print(f"max pairwise overlap area: {worst:.4f} mm^2")
if fails:
    print("FAIL:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("PASS: TMP117 footprint matches TI DRV0006B callouts; zero pad overlaps.")
