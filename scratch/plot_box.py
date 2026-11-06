#!/usr/bin/env python3
"""Plot a board locality for the look-step: pads, tracks, vias in a box.
Usage: python3 scratch/plot_box.py BOARD X0 Y0 X1 Y1 OUT.png [NET ...]
Y grows downward (KiCad convention). Tracks colored by layer; pads
drawn as their bounding boxes with Ref.pin(net) labels."""
import sys
import pcbnew
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

MM = 1_000_000
board = pcbnew.LoadBoard(sys.argv[1])
x0, y0, x1, y1 = (float(v) for v in sys.argv[2:6])
out = sys.argv[6]
only = set(sys.argv[7:])
LC = {pcbnew.F_Cu: '#e53935', pcbnew.In1_Cu: '#fb8c00',
      pcbnew.In2_Cu: '#00acc1', pcbnew.B_Cu: '#1e88e5'}

fig, ax = plt.subplots(figsize=(11, 9), dpi=150)
for fp in board.GetFootprints():
    for p in fp.Pads():
        pos = p.GetPosition()
        px, py = pos.x / MM, pos.y / MM
        if not (x0 - 2 <= px <= x1 + 2 and y0 - 2 <= py <= y1 + 2):
            continue
        bb = p.GetBoundingBox()
        w = (bb.GetRight() - bb.GetLeft()) / MM
        h = (bb.GetBottom() - bb.GetTop()) / MM
        net = p.GetNetname()
        hl = only and net in only
        ax.add_patch(Rectangle((px - w / 2, py - h / 2), w, h,
                               facecolor='#ffd54f' if hl else '#bdbdbd',
                               edgecolor='black', lw=0.6, zorder=3))
        ax.annotate(f"{fp.GetReference()}.{p.GetNumber()}\n{net}",
                    (px, py), fontsize=4.5, ha='center', va='center',
                    zorder=4)
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        pos = t.GetPosition()
        px, py = pos.x / MM, pos.y / MM
        if x0 <= px <= x1 and y0 <= py <= y1:
            net = t.GetNetname()
            if only and net not in only:
                continue
            ax.add_patch(Circle((px, py), t.GetWidth() / MM / 2,
                                facecolor='none', edgecolor='#6a1b9a',
                                lw=1.0, zorder=2))
            ax.annotate(net, (px, py), fontsize=4, color='#6a1b9a',
                        ha='left', va='bottom', zorder=2)
    elif t.Type() == pcbnew.PCB_TRACE_T:
        a, e = t.GetStart(), t.GetEnd()
        ax_, ay, bx, by = a.x / MM, a.y / MM, e.x / MM, e.y / MM
        if max(ax_, bx) < x0 or min(ax_, bx) > x1 or \
           max(ay, by) < y0 or min(ay, by) > y1:
            continue
        net = t.GetNetname()
        if only and net not in only:
            continue
        ax.plot([ax_, bx], [ay, by], color=LC.get(t.GetLayer(), '#999'),
                lw=max(0.7, t.GetWidth() / MM * 6), alpha=0.75,
                solid_capstyle='round', zorder=1)
        mx, my = (ax_ + bx) / 2, (ay + by) / 2
        if x0 <= mx <= x1 and y0 <= my <= y1:
            ax.annotate(net, (mx, my), fontsize=4, alpha=0.9, zorder=2)
ax.set_xlim(x0, x1)
ax.set_ylim(y1, y0)
ax.set_aspect('equal')
ax.grid(True, lw=0.3, alpha=0.4)
plt.tight_layout()
plt.savefig(out)
print('saved', out)
