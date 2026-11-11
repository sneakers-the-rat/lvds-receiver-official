#!/usr/bin/env python3
"""Attach the project's own 3D models to a COPY of a board file.

    xvfb-run -a python3 scripts/attach_models.py <board-in> <board-out>

The shipped board's custom footprints (transformer, shield can and
clips, both photodiodes, the BIST LED) carry no 3D model — KiCad's
library has none for them — so a GLB export would show those pads
bare. This script binds the project-authored models in
hw/models3d/pdlvds/ (see scripts/gen_models3d.py) to the copy named
on the command line, keyed by reference designator. The input board
is never written; scripts/export_glb.sh runs this on a throwaway
copy in a temp directory purely so the render shows the real parts.

Model paths are written absolute (resolved against this repo), which
is safe precisely because the copy is a render intermediate, never
a design file.
"""
import os
import sys

import pcbnew
import wx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "hw", "models3d", "pdlvds")

BIND = {
    "T1": "T1_weflex_hv.wrl",
    "SH1": "SH1_can.wrl",
    "CL1": "CLIP_s1001.wrl",
    "CL2": "CLIP_s1001.wrl",
    "CL3": "CLIP_s1001.wrl",
    "CL4": "CLIP_s1001.wrl",
    "CL5": "CLIP_s1001.wrl",
    "D1": "D1_c30737.wrl",
    "D2": "D2_s8664.wrl",
    "D8": "D8_smt740.wrl",
}


def main():
    src, dst = sys.argv[1], sys.argv[2]
    _app = wx.App(False)
    board = pcbnew.LoadBoard(src)
    bound = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in BIND:
            m = pcbnew.FP_3DMODEL()
            m.m_Filename = os.path.join(MODELS, BIND[ref])
            m.m_Offset = pcbnew.VECTOR3D(0, 0, 0)
            m.m_Scale = pcbnew.VECTOR3D(1, 1, 1)
            m.m_Rotation = pcbnew.VECTOR3D(0, 0, 0)
            fp.Models().push_back(m)
            bound.append(ref)
    missing = sorted(set(BIND) - set(bound))
    if missing:
        print("attach_models: WARNING — refdes not on board: %s" % missing)
    board.Save(dst)
    print("attach_models: bound %d models (%s) -> %s"
          % (len(bound), ", ".join(sorted(bound)), dst))


if __name__ == "__main__":
    main()
