#!/usr/bin/env python3
"""Build hw/pdlvds_rx.kicad_pcb with pcbnew: footprints from the verified
schematic netlist (results/netlist.xml, re-exported fresh), placement
from hw/placement.py, GND plane + pours, then grid A* routing
(hw/router.py). Run: python3 hw/gen_pcb.py [--no-route]
"""
import os, subprocess, sys, xml.etree.ElementTree as ET
sys.path.insert(0, 'hw')
import wx
_wxapp = wx.App(False)   # pcbnew zone filler needs an app context;
                         # run this script under xvfb-run -a
import pcbnew
import circuit
from placement import PLACE

HW = os.path.dirname(os.path.abspath(__file__))
FP_ROOT = "/usr/share/kicad/footprints"
MM = pcbnew.FromMM

def export_netlist():
    out = os.path.join(HW, "..", "results", "netlist.xml")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format",
                    "kicadxml", "-o", out, os.path.join(HW, "pdlvds_rx.kicad_sch")],
                   check=True, capture_output=True)
    return out

def load_netlist(path):
    tree = ET.parse(path)
    comps, nets = {}, {}
    for comp in tree.getroot().iter("comp"):
        fp = comp.find("footprint")
        comps[comp.get("ref")] = fp.text if fp is not None else None
    for net in tree.getroot().iter("net"):
        pins = [(n.get("ref"), n.get("pin")) for n in net.iter("node")]
        nets[net.get("name")] = pins
    return comps, nets

def build(route=True):
    nl = export_netlist()
    comps, pin_nets = load_netlist(nl)
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.m_CopperLayerCount = 4
    # board outline 100 x 80 + HV isolation slot (closed cutout loop)
    for (x1, y1, x2, y2) in [(0, 0, 100, 0), (100, 0, 100, 80),
                             (100, 80, 0, 80), (0, 80, 0, 0)]:
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        seg.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
        seg.SetWidth(MM(0.05))
        board.Add(seg)
    # slot between HV island and AFE: rectangle x 12..46, y 23.6..25.1
    sx1, sy1, sx2, sy2 = 12, 23.6, 46, 25.1
    for (x1, y1, x2, y2) in [(sx1, sy1, sx2, sy1), (sx2, sy1, sx2, sy2),
                             (sx2, sy2, sx1, sy2), (sx1, sy2, sx1, sy1)]:
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        seg.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
        seg.SetWidth(MM(0.05))
        board.Add(seg)
    # nets
    net_objs = {}
    for name in sorted(pin_nets):
        if name.startswith("unconnected-"):
            continue
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        net_objs[name] = ni
    # footprints
    fps = {}
    for part in circuit.PARTS:
        ref = part["ref"]
        lib, name = part["fp"]
        libpath = (os.path.join(HW, "pdlvds.pretty") if lib == "pdlvds"
                   else os.path.join(FP_ROOT, lib + ".pretty"))
        fp = pcbnew.FootprintLoad(libpath, name)
        if fp is None:
            raise RuntimeError(f"footprint load failed: {lib}:{name}")
        fp.SetReference(ref)
        fp.SetValue(part["value"])
        x, y, rot = PLACE[ref]
        fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        fp.SetOrientationDegrees(rot)
        board.Add(fp)
        fps[ref] = fp
    # net assignment from netlist
    padnet = {}
    for name, pins in pin_nets.items():
        if name.startswith("unconnected-"):
            continue
        for ref, pin in pins:
            padnet[(ref, pin)] = net_objs[name]
    missing = []
    for ref, fp in fps.items():
        for pad in fp.Pads():
            key = (ref, pad.GetNumber())
            if key in padnet:
                pad.SetNet(padnet[key])
            elif pad.GetNumber() not in ("", ):
                pass  # intentionally unconnected pad
    board.BuildListOfNets()
    # GND zones: In1.Cu solid plane; F.Cu and B.Cu pours (lower priority)
    gnd = net_objs["GND"]
    for layer, prio in [(pcbnew.In1_Cu, 0), (pcbnew.F_Cu, 1), (pcbnew.B_Cu, 1)]:
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetNetCode(gnd.GetNetCode())
        z.SetLocalClearance(MM(0.25))
        z.SetMinThickness(MM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        out = z.Outline()
        chain = pcbnew.SHAPE_LINE_CHAIN()
        for (x, y) in [(0.3, 0.3), (99.7, 0.3), (99.7, 79.7), (0.3, 79.7)]:
            chain.Append(pcbnew.VECTOR2I(MM(x), MM(y)))
        chain.SetClosed(True)
        out.AddOutline(chain)
        if layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            # Surface pours must keep the 1.0 mm HV creepage rule, so
            # the fill is voided over the HV island, the APD site and
            # the APD jumper cluster. (Buried In1.Cu is NOT voided:
            # internal clearance to HV is dielectric-limited, see
            # check_pcb.py's layer-aware rule, and the island's GND
            # pads reach the plane through it.)
            for (hx0, hx1, hy0, hy1) in [(2, 50, 2, 27), (5, 16, 36, 46),
                                         (11, 16, 53, 58)]:
                hole = pcbnew.SHAPE_LINE_CHAIN()
                for (x, y) in [(hx0, hy0), (hx1, hy0), (hx1, hy1), (hx0, hy1)]:
                    hole.Append(pcbnew.VECTOR2I(MM(x), MM(y)))
                hole.SetClosed(True)
                try:
                    out.AddHole(hole, 0)
                except Exception:
                    try:
                        out.AddHole(hole)
                    except Exception as e:
                        print(f"WARNING: zone hole failed on L{layer}: {e}")
        if hasattr(z, "SetPriority"):
            z.SetPriority(prio)
        board.Add(z)
    outpath = os.path.join(HW, "pdlvds_rx.kicad_pcb")
    board.Save(outpath)
    # ZONE_FILLER segfaults on a purely in-memory board in this KiCad
    # 7.0.11 build; a save/reload cycle makes Fill work (verified).
    board = pcbnew.LoadBoard(outpath)
    if route:
        import router
        fps2 = {fp.GetReference(): fp for fp in board.GetFootprints()}
        # NETINFO_ITEMs must belong to the RELOADED board: handing the
        # router net objects from the pre-save board makes SetNet attach
        # foreign objects (wrong net codes / SWIG failure). Rebuild the
        # map from the reloaded board via FindNet.
        nets2 = {}
        for name in net_objs:
            ni = board.FindNet(name)
            if ni is None:
                raise RuntimeError(f"net {name} missing after reload")
            nets2[name] = ni
        router.route(board, nets2, fps2)
    # Checkpoint: save the routed board BEFORE the zone fill, so a
    # timeout during the (slow) fill can never discard a completed
    # route — a follow-up fill+save is a 1-minute job, a re-route is
    # not. (v3 lost its safety margin exactly here.)
    board.Save(outpath)
    print("checkpoint save (routed, unfilled)", flush=True)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(outpath)
    print("saved", outpath)
    return board

if __name__ == "__main__":
    build(route="--no-route" not in sys.argv)
