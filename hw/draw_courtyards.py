#!/usr/bin/env python3
"""Draw courtyards for the custom footprints that have none
(D1, D2, C4, U9, T1) by TEXT insertion of fp_line rectangles on
F.CrtYd — into the board file's embedded footprints and into
hw/pdlvds.pretty/*.kicad_mod, so a re-sync keeps them.

Why text: KiCad 7.0.11's pcbnew file writer zeroes the endpoints
of FP_SHAPE items whose points were set through the Python API
(verified three ways in-session: in-memory GetStart() correct
after Add, saved file shows (start 0 0) (end 0 0), reloaded
courtyard empty). Parser-born shapes write fine, so the
courtyards are inserted as text and verified by reload.

Courtyard definition: union bbox of the footprint's body outline
(Fab shapes, else Silkscreen shapes; text excluded) and its
pads, expanded by the standard 0.25 mm allowance. SH1 is
deliberately NOT drawn: it is a shield can whose outline
encloses the frontend it exists to cover — its closure is the
pending clip-pattern conversion (parts audit), and until then
the audit's bbox fallback reports it in every pass (named gap).

Run: xvfb-run -a python3 hw/draw_courtyards.py IN OUT
(IN is the board; OUT gets the board + courtyards. The library
files under hw/pdlvds.pretty/ are updated in place.)
"""
import re
import sys
import uuid
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb

MM = pcbnew.FromMM
TARGETS = ('D1', 'D2', 'C4', 'U9', 'T1')
LIBDIR = 'hw/pdlvds.pretty'

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

rects = {}   # ref -> (lib_item_name, local rect mm (x0,y0,x1,y1))
for ref in TARGETS:
    fp = fps[ref]
    assert not fp.IsFlipped() and abs(fp.GetOrientationDegrees()) < 0.01
    shapes = [d for d in fp.GraphicalItems()
              if isinstance(d, pcbnew.PCB_SHAPE)]
    boxes = [d.GetBoundingBox() for d in shapes
             if d.GetLayer() == pcbnew.F_Fab]
    if not boxes:
        boxes = [d.GetBoundingBox() for d in shapes
                 if d.GetLayer() == pcbnew.F_SilkS]
    boxes += [p.GetBoundingBox() for p in fp.Pads()]
    pos = fp.GetPosition()
    x0 = (min(b.GetLeft() for b in boxes) - MM(0.25) - pos.x) / 1e6
    x1 = (max(b.GetRight() for b in boxes) + MM(0.25) - pos.x) / 1e6
    y0 = (min(b.GetTop() for b in boxes) - MM(0.25) - pos.y) / 1e6
    y1 = (max(b.GetBottom() for b in boxes) + MM(0.25) - pos.y) / 1e6
    rects[ref] = (str(fp.GetFPID().GetLibItemName()), (x0, y0, x1, y1))
    print(f"{ref}: local courtyard rect ({x0:.3f},{y0:.3f})-"
          f"({x1:.3f},{y1:.3f}) lib={rects[ref][0]}")


def fmt(v):
    s = f"{v:.6f}".rstrip('0').rstrip('.')
    return s if s else '0'


def line_forms(rect):
    x0, y0, x1, y1 = rect
    pts = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
           ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
    out = []
    for (ax, ay), (bx, by) in pts:
        out.append(
            f'    (fp_line (start {fmt(ax)} {fmt(ay)}) '
            f'(end {fmt(bx)} {fmt(by)}) '
            f'(stroke (width 0.05) (type solid)) '
            f'(layer "F.CrtYd") (tstamp {uuid.uuid4()}))\n')
    return ''.join(out)


def block_end(text, start):
    """Index just past the matching close paren of the form
    starting at `start` (which points at its opening paren)."""
    depth = 0
    i = start
    instr = False
    while i < len(text):
        c = text[i]
        if instr:
            if c == '\\':
                i += 2
                continue
            if c == '"':
                instr = False
        elif c == '"':
            instr = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError('unbalanced')


def insert_into_board(text, ref, forms):
    for m in re.finditer(r'\(footprint ', text):
        end = block_end(text, m.start())
        block = text[m.start():end]
        if f'(fp_text reference "{ref}"' in block:
            return text[:end - 1] + forms + text[end - 1:]
    raise ValueError(f'footprint {ref} not found')


def insert_into_lib(text, forms):
    m = re.search(r'\(footprint ', text)
    end = block_end(text, m.start())
    return text[:end - 1] + forms + text[end - 1:]


with open(SRC) as f:
    btext = f.read()
for ref in TARGETS:
    btext = insert_into_board(btext, ref, line_forms(rects[ref][1]))
with open(OUT, 'w') as f:
    f.write(btext)
print('board written:', OUT)

for ref in TARGETS:
    libname = rects[ref][0]
    path = f"{LIBDIR}/{libname}.kicad_mod"
    with open(path) as f:
        ltext = f.read()
    if '"F.CrtYd"' in ltext:
        print(f'library {libname}: courtyard already present, skip')
        continue
    ltext = insert_into_lib(ltext, line_forms(rects[ref][1]))
    with open(path, 'w') as f:
        f.write(ltext)
    print(f'library {libname}: courtyard inserted')

# verify by reload in a fresh board object is NOT possible twice
# in one process (SWIG) — the caller verifies in a new process.
print('rects:', {r: rects[r][1] for r in TARGETS})
