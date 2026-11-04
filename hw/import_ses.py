#!/usr/bin/env python3
"""Import a Freerouting .ses session file into a KiCad board.

Own importer (KiCad 7.0.11's pcbnew.ImportSpecctraSES module-level
wrapper has an unclear calling convention; this gives full control
and an auditable record of what was created).

SES facts relied on (Specctra session format, as written by
Freerouting 2.5.0 for a KiCad-exported DSN):
  * (network_out (net NAME (wire (path LAYER WIDTH x y x y ...))
    (via PADSTACK x y) ...)) — coordinates in the SES file's own
    resolution units ((resolution um N) = N units per um; Freerouting
    writes um 10, i.e. 0.1 um units — NOT um), Y axis pointing UP
    (KiCad's DSN export negates Y), so importing negates Y back and
    scales units -> mm via the parsed resolution.
  * Via padstack names look like "Via[0-3]_600:300_um" (dia:drill
    in um).
  * Wires may also appear under (bundle ...) groupings in some
    writers; handled by walking the net subtree recursively.

After adding the copper, zones are refilled via the usual
save/reload cycle (ZONE_FILLER needs it on this KiCad build).

Run: xvfb-run -a python3 hw/import_ses.py BASE.kicad_pcb IN.ses OUT.kicad_pcb
"""
import re, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

MM = pcbnew.FromMM
LAYER_IDS = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu,
             "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}

def parse_sexp(text):
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    pos = 0
    def parse():
        nonlocal pos
        tok = tokens[pos]; pos += 1
        if tok == '(':
            out = []
            while tokens[pos] != ')':
                out.append(parse())
            pos += 1
            return out
        if tok.startswith('"'):
            return tok[1:-1]
        return tok
    return parse()

def walk(node):
    yield node
    if isinstance(node, list):
        for ch in node[1:]:
            yield from walk(ch)

def main():
    base_path, ses_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    ses_text = open(ses_path).read()
    # SES coordinates are in the file's resolution units:
    # (resolution um N) means N units per um (Freerouting writes
    # um 10 -> 1 unit = 0.1 um). mm = raw / N / 1000. Assuming um
    # (N=1) mis-scales every coordinate by exactly N (found 2026-11-04:
    # a full import landed at 10x, tracks 10x away from their pads).
    rm = re.search(r'\(resolution\s+um\s+([\d.]+)\)', ses_text)
    units_per_um = float(rm.group(1)) if rm else 1.0
    TO_MM = 1.0 / (units_per_um * 1000.0)
    print(f"SES resolution: {units_per_um} units/um (1 unit = {TO_MM} mm)")
    tree = parse_sexp(ses_text)
    board = pcbnew.LoadBoard(base_path)
    n_tracks = n_vias = 0
    skipped_layers = set()
    net_objs = {}
    def net_obj(name):
        if name not in net_objs:
            net_objs[name] = board.FindNet(name)
        return net_objs[name]
    for node in walk(tree):
        if not (isinstance(node, list) and node and node[0] == 'net'
                and len(node) >= 2 and isinstance(node[1], str)):
            continue
        netname = node[1]
        no = net_obj(netname)
        if no is None:
            print(f"WARNING: net {netname} not on board, skipped")
            continue
        for sub in walk(node):
            if not isinstance(sub, list) or not sub:
                continue
            if sub[0] == 'path' and len(sub) >= 4:
                layer, width_um = sub[1], float(sub[2]) * TO_MM * 1000.0
                coords = [float(v) * TO_MM for v in sub[3:]]
                pts = [(coords[i], -coords[i + 1])
                       for i in range(0, len(coords) - 1, 2)]
                if layer not in LAYER_IDS:
                    skipped_layers.add(layer)
                    continue
                for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                    if (x1, y1) == (x2, y2):
                        continue
                    tr = pcbnew.PCB_TRACK(board)
                    tr.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
                    tr.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
                    tr.SetWidth(MM(width_um / 1000.0))
                    tr.SetLayer(LAYER_IDS[layer])
                    tr.SetNet(no)
                    board.Add(tr)
                    n_tracks += 1
            elif sub[0] == 'via' and len(sub) >= 4:
                m = re.search(r'_(\d+):(\d+)_um', str(sub[1]))
                dia, drill = (0.6, 0.3) if not m else \
                    (int(m.group(1)) / 1000.0, int(m.group(2)) / 1000.0)
                x, y = float(sub[2]) * TO_MM, -float(sub[3]) * TO_MM
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
                via.SetWidth(MM(dia)); via.SetDrill(MM(drill))
                via.SetNet(no)
                via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                board.Add(via)
                n_vias += 1
    print(f"imported {n_tracks} track segments, {n_vias} vias"
          + (f"; SKIPPED layers: {skipped_layers}" if skipped_layers
             else ""))
    board.Save(out_path)
    board = pcbnew.LoadBoard(out_path)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(out_path)
    print(f"saved {out_path} (zones refilled)")

if __name__ == "__main__":
    main()
