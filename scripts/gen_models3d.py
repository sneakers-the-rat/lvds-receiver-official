#!/usr/bin/env python3
"""Generate the project-authored 3D models in hw/models3d/.

Two families live here:

  * Simplified stand-ins for five KiCad library models the board's
    footprints reference but current KiCad library releases no longer
    ship under those names (the Amphenol SMA and USB-C connectors, the
    1812 fuse, the Abracon ASE oscillator, the Murata DFE201610P
    inductor). They are written to the exact paths the footprints
    reference, so an export finds them like the originals.
  * First-party models for the project's own custom footprints, which
    ship with no 3D model at all (the WE-FLEX transformer, the Harwin
    shield can and its clips, the C30737 APD, the S8664 APD, the
    SMT740 LED). scripts/attach_models.py binds these to a throwaway
    copy of the board at render time; the shipped board file is never
    modified for rendering.

Each model is emitted twice: as VRML (.wrl — what the footprint
stanzas name, used by KiCad's GUI 3D viewer) and as STEP (.step —
kicad-cli's headless exporter loads models via its STEP path with
--subst-models; its VRML path does not resolve models headlessly,
verified 2026-11-10). Both are generated from the same solid list,
so the two can never disagree about geometry.

Geometry is deliberately simple — boxes and many-sided prisms at
the real parts' datasheet dimensions (each model names its source).
These are visualisation solids for the website's 3D view, NOT
mechanical models; the board's own STEP export remains the
mechanical record.

Conventions: dimensions in mm everywhere below. VRML output uses
the KiCad WRL convention (1 unit = 0.1 inch = 2.54 mm, origin at
the footprint centre, z = 0 on the board surface, z up); STEP is
native mm. Cylinders are 28-sided prisms — indistinguishable at
render distance, and planar-faced in both formats.

Run:  python3 scripts/gen_models3d.py
"""
import math
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "hw", "models3d")
U = 2.54  # mm per WRL unit


# ---------------------------------------------------------------- solids
# A solid is a list of faces; a face is (rgb, [points]) with points
# ordered counter-clockwise around the outward normal. A model is a
# list of solids; a solid is (rgb, [faces' point-lists]).

def prism(cx, cy, cz, poly, h, rgb):
    """Extrude a CCW (seen from +z) 2D polygon from z=cz to cz+h."""
    k = len(poly)
    bot = [(cx + x, cy + y, cz) for x, y in poly]
    top = [(x, y, cz + h) for x, y, _ in bot]
    faces = [list(reversed(bot)), top]
    for i in range(k):
        j = (i + 1) % k
        faces.append([bot[i], bot[j], top[j], top[i]])
    return (rgb, faces)


def box(cx, cy, cz, dx, dy, dz, rgb):
    hx, hy = dx / 2, dy / 2
    return prism(cx, cy, cz,
                 [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)], dz, rgb)


def cyl(cx, cy, cz, r, h, rgb, n=28):
    poly = [(r * math.cos(2 * math.pi * i / n),
             r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    return prism(cx, cy, cz, poly, h, rgb)


STEEL = (0.62, 0.64, 0.66)
SILVER = (0.78, 0.79, 0.80)
BRASS = (0.72, 0.53, 0.26)
DARK = (0.16, 0.16, 0.17)
CERAMIC = (0.82, 0.80, 0.76)
COPPER = (0.45, 0.28, 0.16)

MODELS = {}


def model(path, solids, comment):
    MODELS[path] = (solids, comment)


# ---- stand-ins for library models no longer shipped under these names

# Amphenol 132134 vertical SMA: square base flange + round body.
model("Connector_Coaxial.3dshapes/SMA_Amphenol_132134_Vertical",
      [box(0, 0, 0, 9.0, 9.0, 1.6, BRASS),
       cyl(0, 0, 1.6, 3.15, 7.5, BRASS),
       cyl(0, 0, 9.1, 1.6, 2.4, BRASS)],
      "Simplified SMA vertical connector (project-authored stand-in); "
      "base 9x9 mm, body dia 6.3 mm.")

# Amphenol 12401610E4-2A USB-C receptacle: steel shell + tongue.
model("Connector_USB.3dshapes/USB_C_Receptacle_Amphenol_12401610E4-2A",
      [box(0, 0, 0.1, 8.94, 7.35, 3.16, STEEL),
       box(0, 2.2, 1.15, 7.0, 3.4, 1.0, DARK)],
      "Simplified USB-C receptacle shell (project-authored stand-in); "
      "shell 8.94 x 7.35 x 3.16 mm.")

# 1812 fuse: ceramic body, metal end caps.
model("Fuse.3dshapes/Fuse_1812_4532Metric",
      [box(0, 0, 0, 4.5, 3.2, 0.9, CERAMIC),
       box(-1.85, 0, 0, 0.8, 3.2, 0.95, SILVER),
       box(1.85, 0, 0, 0.8, 3.2, 0.95, SILVER)],
      "Simplified 1812 fuse (project-authored stand-in); 4.5 x 3.2 mm.")

# Abracon ASE oscillator, 3.2 x 2.5 mm metal-can SMD package.
model("Oscillator.3dshapes/Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm",
      [box(0, 0, 0, 3.2, 2.5, 0.85, SILVER)],
      "Simplified ASE oscillator (project-authored stand-in); "
      "3.2 x 2.5 x 0.85 mm.")

# Murata DFE201610P wire-wound inductor, 2.0 x 1.6 mm.
model("Inductor_SMD.3dshapes/L_Murata_DFE201610P",
      [box(0, 0, 0, 2.0, 1.6, 1.0, DARK)],
      "Simplified DFE201610P inductor (project-authored stand-in); "
      "2.0 x 1.6 x 1.0 mm.")

# ---- first-party models for the project's custom footprints

# Wurth WE-FLEX HV 749196518 (EFD20): ferrite core block, winding
# window band, gull-wing pin rows at the footprint's pad positions.
_t1 = [box(0, 0, 0.4, 21.0, 21.5, 11.6, DARK),
       box(0, 0, 1.2, 12.0, 21.5, 3.0, COPPER)]
for _sx in (-13.10, 13.10):
    for _y in (-7.5, -4.5, -1.5, 1.5, 4.5, 7.5):
        _t1.append(box(_sx, _y, 0, 3.5, 0.7, 0.25, SILVER))
model("pdlvds/T1_weflex_hv", _t1,
      "Wurth WE-FLEX HV 749196518, simplified: core 21.0 x 21.5 mm, "
      "height 12.0 mm (datasheet 749196518, docs/12).")

# Harwin S02-20150300 shield can, 20 x 15 x 3.0 mm internal.
model("pdlvds/SH1_can",
      [box(0, 0, 0.25, 20.2, 15.2, 3.2, STEEL)],
      "Harwin S02-20150300 shield can, simplified: 20.2 x 15.2 x 3.2 mm "
      "outer (drawing DRG-02145).")

# Harwin S1001-46R shield clip.
model("pdlvds/CLIP_s1001",
      [box(0, 0, 0, 4.5, 1.35, 0.95, STEEL)],
      "Harwin S1001-46R shield clip, simplified: 4.5 mm long "
      "(drawing DRG-02154).")

# Excelitas C30737LH-500-90: 3 x 3 mm LCC body + window.
model("pdlvds/D1_c30737",
      [box(0, 0, 0, 3.0, 3.0, 1.05, CERAMIC),
       cyl(0, 0, 1.05, 0.55, 0.12, (0.25, 0.16, 0.30))],
      "Excelitas C30737LH-500-90, simplified: 3.0 x 3.0 mm body, "
      "window over the 0.5 mm active area (datasheet Fig. 10, docs/07).")

# Hamamatsu S8664: TO-5 can, flange dia 9.1, cap dia 8.1, height 4.2.
model("pdlvds/D2_s8664",
      [cyl(0, 0, 0, 4.55, 0.8, SILVER),
       cyl(0, 0, 0.8, 4.05, 3.4, SILVER),
       cyl(0, 0, 4.2, 2.4, 0.1, (0.30, 0.36, 0.48))],
      "Hamamatsu S8664, simplified: flange dia 9.1 mm, cap dia 8.1 mm, "
      "height 4.2 mm (datasheet KAPD1012E).")

# Ushio SMT740: 3.2 x 2.7 mm body + dia 2.4 lens.
model("pdlvds/D8_smt740",
      [box(0, 0, 0, 3.2, 2.7, 1.2, (0.88, 0.86, 0.82)),
       cyl(0, 0, 1.2, 1.2, 0.6, (0.85, 0.30, 0.25))],
      "Ushio Epitex SMT740, simplified: body 3.2 x 2.7 mm, lens dia "
      "2.4 mm (Ushio data sheet 2019.03, docs/09 F-13).")


# ---------------------------------------------------------------- VRML

def emit_wrl(path, solids, comment):
    lines = ["#VRML V2.0 utf8", "# " + comment, ""]
    for rgb, faces in solids:
        pts, index = [], {}
        tris = []
        for f in faces:
            ids = []
            for p in f:
                if p not in index:
                    index[p] = len(pts)
                    pts.append(p)
                ids.append(index[p])
            for i in range(1, len(ids) - 1):
                tris.append((ids[0], ids[i], ids[i + 1]))
        lines.append("Shape {")
        lines.append("  appearance Appearance { material Material { "
                     "diffuseColor %.3f %.3f %.3f } }" % rgb)
        lines.append("  geometry IndexedFaceSet {")
        lines.append("    coord Coordinate { point [")
        for x, y, z in pts:
            lines.append("      %.5f %.5f %.5f," % (x / U, y / U, z / U))
        lines.append("    ] }")
        lines.append("    coordIndex [")
        for t in tris:
            lines.append("      %d, %d, %d, -1," % t)
        lines.append("    ] }")
        lines.append("  }")
        lines.append("}")
    full = os.path.join(OUT, path + ".wrl")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote", os.path.relpath(full, ROOT))


# ---------------------------------------------------------------- STEP

class Step:
    def __init__(self):
        self.lines = []
        self.n = 0

    def e(self, body):
        self.n += 1
        self.lines.append("#%d = %s;" % (self.n, body))
        return "#%d" % self.n


def _norm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v) if l else v


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def emit_step(path, solids, comment):
    w = Step()

    def pt(p):
        return w.e("CARTESIAN_POINT('',(%.6f,%.6f,%.6f))" % p)

    def direction(v):
        return w.e("DIRECTION('',(%.6f,%.6f,%.6f))" % _norm(v))

    def vertex(p):
        return w.e("VERTEX_POINT('',%s)" % pt(p))

    edges = {}

    def edge(p1, p2):
        key = (p1, p2) if p1 <= p2 else (p2, p1)
        if key not in edges:
            a, b = key
            va, vb = vertex(a), vertex(b)
            dv = _sub(b, a)
            ln = math.sqrt(sum(c * c for c in dv))
            vec = w.e("VECTOR('',%s,%.6f)" % (direction(dv), ln))
            line = w.e("LINE('',%s,%s)" % (pt(a), vec))
            edges[key] = w.e("EDGE_CURVE('',%s,%s,%s,.T.)" % (va, vb, line))
        return edges[key], (p1, p2) == key

    solid_ids = []
    for rgb, faces in solids:
        face_ids = []
        for f in faces:
            n = _cross(_sub(f[1], f[0]), _sub(f[2], f[1]))
            n = _norm(n)
            xdir = _norm(_sub(f[1], f[0]))
            place = w.e("AXIS2_PLACEMENT_3D('',%s,%s,%s)"
                        % (pt(f[0]), direction(n), direction(xdir)))
            surf = w.e("PLANE('',%s)" % place)
            oes = []
            for i in range(len(f)):
                e, fwd = edge(f[i], f[(i + 1) % len(f)])
                oes.append(w.e("ORIENTED_EDGE('',*,*,%s,.%s.)"
                               % (e, "T" if fwd else "F")))
            loop = w.e("EDGE_LOOP('',(%s))" % ",".join(oes))
            bound = w.e("FACE_BOUND('',%s,.T.)" % loop)
            face_ids.append(w.e("ADVANCED_FACE('',(%s),%s,.T.)"
                                % (bound, surf)))
        shell = w.e("CLOSED_SHELL('',(%s))" % ",".join(face_ids))
        solid_ids.append(w.e("MANIFOLD_SOLID_BREP('',%s)" % shell))
    solid = ",".join(solid_ids)

    # Product + representation skeleton (mirrors KiCad library STEPs).
    name = os.path.basename(path)
    lu = w.e("( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) )")
    pau = w.e("( NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.) )")
    sau = w.e("( NAMED_UNIT(*) SI_UNIT($,.STERADIAN.) SOLID_ANGLE_UNIT() )")
    unc = w.e("UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-07),%s,"
              "'DISTANCE_ACCURACY_VALUE','Maximum Tolerance')" % lu)
    ctx = w.e("( GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((%s)) "
              "GLOBAL_UNIT_ASSIGNED_CONTEXT((%s,%s,%s)) "
              "REPRESENTATION_CONTEXT('Context #1',"
              "'3D Context with UNIT and UNCERTAINTY') )" % (unc, lu, pau, sau))
    rep = w.e("ADVANCED_BREP_SHAPE_REPRESENTATION('%s',(%s),%s)"
              % (name, solid, ctx))
    appctx = w.e("APPLICATION_CONTEXT('mechanical design')")
    pdc = w.e("PRODUCT_DEFINITION_CONTEXT('part definition',%s,"
              "'design')" % appctx)
    prod = w.e("PRODUCT('%s','%s','',(%s))" % (name, name, pdc))
    pdf_ = w.e("PRODUCT_DEFINITION_FORMATION('%s','',%s)"
               % (name, prod))
    pdef = w.e("PRODUCT_DEFINITION('design',%s,%s)" % (pdf_, pdc))
    pds = w.e("PRODUCT_DEFINITION_SHAPE('','',%s)" % pdef)
    w.e("SHAPE_DEFINITION_REPRESENTATION(%s,%s)" % (pds, rep))
    w.e("PRODUCT_RELATED_PRODUCT_CATEGORY('part','',(%s))" % prod)

    head = ("ISO-10303-21;\nHEADER;\n"
            "FILE_DESCRIPTION((''),'2;1');\n"
            "FILE_NAME('%s.step','2026-11-10T00:00:00',(''),(''),"
            "'gen_models3d.py','','');\n"
            "FILE_SCHEMA(('AP214IS'));\nENDSEC;\nDATA;\n" % name)
    full = os.path.join(OUT, path + ".step")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as fh:
        fh.write(head + "\n".join(w.lines) + "\nENDSEC;\nEND-ISO-10303-21;\n")
    print("wrote", os.path.relpath(full, ROOT))


for path, (solids, comment) in sorted(MODELS.items()):
    emit_wrl(path, solids, comment)
    emit_step(path, solids, comment)
print("done: %d models x2 formats" % len(MODELS))
